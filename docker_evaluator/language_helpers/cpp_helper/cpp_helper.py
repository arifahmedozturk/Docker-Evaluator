import os
from docker_evaluator.language_helpers.language_helper import LanguageHelper

class CppHelper(LanguageHelper):
    def __init__(self, docker_helper):
        super().__init__(docker_helper, os.path.dirname(__file__), "cpp", "cpp", 1, cache_compilation=True)
