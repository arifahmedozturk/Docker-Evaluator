import os

from docker_evaluator.disk_helper import get_cache_dir, get_compile_lock, get_temp_dir


class LanguageHelper:
    def __init__(
        self,
        docker_helper,
        docker_context_path,
        language,
        file_extension,
        language_time_limit_multiplier,
        memory_overhead_mb=32,
        cache_compilation=False,
    ):
        docker_image_name = f"docker-evaluator-{language}"
        self.docker_helper = docker_helper
        self.docker_image_name = docker_image_name
        self.language = language
        self.language_time_limit_multiplier = language_time_limit_multiplier
        self.memory_overhead_mb = memory_overhead_mb
        self.cache_compilation = cache_compilation
        self.file_extension = file_extension
        self.initialize(docker_context_path, docker_image_name)

    def initialize(self, docker_context_path, docker_image_name):
        docker_image_tag = f"{docker_image_name}:latest"
        if not self.docker_helper.image_exists(docker_image_tag):
            print(f"Image {docker_image_tag} not found, building...")
            self.docker_helper.create_image(docker_context_path, docker_image_tag)
            print(f"Image {docker_image_tag} built successfully.")

    def evaluate(self, code, code_input, time_limit, input_type="stdin", file_io_name="", memory_limit=1024):
        files = [
            {"name": f"target.{self.file_extension}", "content": code},
            {"name": "target.in", "content": code_input},
        ]
        # Add grace to compensate for Docker/WSL2 scheduling jitter on Windows.
        # timeout measures wall clock, not CPU time, so the process may get less
        # than a full CPU-second per wall-second under load.
        GRACE_S = 0.2
        effective_time_limit = time_limit * self.language_time_limit_multiplier + GRACE_S
        environment_variables = {
            "TIME_LIMIT": effective_time_limit,
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "INPUT_TYPE": input_type,
            "FILE_IO_NAME": file_io_name or "",
            "MEMORY_LIMIT_KB": str(memory_limit),
        }
        memory_limit_mb = memory_limit // 1024
        total_memory_mb = memory_limit_mb + self.memory_overhead_mb
        # C/C++ compilation can briefly use much more memory than runtime.
        # Keep a minimum container budget for compile-heavy languages, while
        # entrypoints enforce the requested runtime limit with ulimit.
        compile_safe_memory_mb = max(total_memory_mb, 1536) if self.cache_compilation else total_memory_mb
        temp_dir = get_temp_dir(files)
        cache_dir = get_cache_dir(code, self.language) if self.cache_compilation else None
        cache_file = os.path.join(cache_dir, "main") if cache_dir else None
        cache_status = "disabled" if not cache_dir else ("hit" if os.path.exists(cache_file) else "miss")
        print(
            f"env: {environment_variables}, time: {time_limit}s x{self.language_time_limit_multiplier} +{GRACE_S}s grace = {effective_time_limit}s, memory: {memory_limit}KB ({memory_limit_mb}MB) + {self.memory_overhead_mb}MB overhead = {total_memory_mb}MB, container: {compile_safe_memory_mb}MB, cache: {cache_status}"
        )
        # On a cache miss, serialize via a per-hash lock so only one container
        # compiles at a time. This prevents simultaneous writes to the same
        # Windows volume path from hanging. Cache hits run without the lock.
        if cache_dir and not os.path.exists(cache_file):
            with get_compile_lock(cache_dir):
                return self.docker_helper.evaluate(
                    self.docker_image_name,
                    temp_dir,
                    environment_variables=environment_variables,
                    memory_limit_mb=compile_safe_memory_mb,
                    cache_dir=cache_dir,
                )
        return self.docker_helper.evaluate(
            self.docker_image_name,
            temp_dir,
            environment_variables=environment_variables,
            memory_limit_mb=compile_safe_memory_mb,
            cache_dir=cache_dir,
        )
