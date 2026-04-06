import os

from docker_evaluator.language_helpers.language_helper import LanguageHelper


class Py2Helper(LanguageHelper):
    def __init__(self, docker_helper):
        super().__init__(docker_helper, os.path.dirname(__file__), "py2", "py", 5, memory_overhead_mb=64)
