from docker_evaluator.docker_helper import DockerHelper
from docker_evaluator.env_helper import load_env_variables
from docker_evaluator.language_helpers.c_helper.c_helper import CHelper
from docker_evaluator.language_helpers.cpp_helper.cpp_helper import CppHelper
from docker_evaluator.language_helpers.py2_helper.py2_helper import Py2Helper
from docker_evaluator.language_helpers.py3_helper.py3_helper import Py3Helper

class DockerEvaluator:
    def __init__(self, docker_client=None):
        load_env_variables()
        self.docker_helper = docker_client
        if docker_client is None:
            self.docker_helper = DockerHelper()

        self.language_helpers = [
            CHelper(self.docker_helper),
            CppHelper(self.docker_helper),
            Py2Helper(self.docker_helper),
            Py3Helper(self.docker_helper),
        ]

    def evaluate(self, code, input, expected_output, language, time_limit, input_type='stdin', file_io_name='', memory_limit=1024):
        # Enforce minimum memory limit of 256MB to avoid spurious segfaults on valid code.
        # memory_limit is in KB, so 262144 KB = 256 MB.
        MIN_MEMORY_KB = 256 * 1024
        memory_limit = max(memory_limit, MIN_MEMORY_KB)

        for language_helper in self.language_helpers:
            if language_helper.language == language:
                output = language_helper.evaluate(code, input, time_limit, input_type, file_io_name, memory_limit=memory_limit)
                # Extract container-side timing appended by entrypoint as last line
                time_str = None
                lines = output.split('\n')
                if lines and lines[-1].startswith('__TIME__:'):
                    time_str = lines[-1][len('__TIME__:'):]
                    output = '\n'.join(lines[:-1]).rstrip()
                if "Limit Exceeded" in output or "Compilation Error" in output or "Runtime Error" in output:
                    return {
                        "correct": False,
                        "details": output
                    }
                elif output.split() != expected_output.split():
                    return {
                        "correct": False,
                        "details": "Wrong Answer"
                    }
                return {
                    "correct": True,
                    "details": f"OK ({time_str})" if time_str else "OK (time unavailable)"
                }

    def close(self):
        self.docker_helper.close()
