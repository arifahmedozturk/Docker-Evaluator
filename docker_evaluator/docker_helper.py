import os

import docker
from docker.errors import ContainerError
from docker.types import LogConfig


class DockerHelper:
    def __init__(self):
        self.client = docker.from_env()

    def image_exists(self, image_tag):
        images = self.client.images.list()
        image_names = []
        for image in images:
            image_names.extend(image.tags)
        return image_tag in image_names

    def create_image(self, image_path, image_tag):
        self.client.images.build(path=image_path, tag=image_tag)

    def evaluate(self, image_name, volume, environment_variables, cpus=1, memory_limit_mb=None, cache_dir=None):
        volumes = {volume: {"bind": "/test_data", "mode": "ro"}}
        if cache_dir:
            volumes[cache_dir] = {"bind": "/cache", "mode": "rw"}
        # Read env at call time because env files may be loaded after helper init.
        keep_eval_containers = os.getenv("KEEP_EVAL_CONTAINERS", "0") == "1"
        try:
            logs = self.client.containers.run(
                image_name,
                volumes=volumes,
                detach=False,
                environment=environment_variables,
                remove=not keep_eval_containers,
                log_config=LogConfig(type="json-file"),
                nano_cpus=int(cpus * 1e9),
                mem_limit=f"{memory_limit_mb}m" if memory_limit_mb else None,
                memswap_limit=f"{memory_limit_mb}m" if memory_limit_mb else None,
                network_disabled=True,
                pids_limit=64,
            )
        except ContainerError as e:
            if e.exit_status == 137:
                return "Memory Limit Exceeded"
            return f"Runtime Error (exit code {e.exit_status})"
        output = logs.decode("utf-8", errors="replace").rstrip()
        return output

    def close(self):
        self.client.close()
