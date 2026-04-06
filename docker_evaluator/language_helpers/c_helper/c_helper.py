import os

from docker_evaluator.language_helpers.language_helper import LanguageHelper


class CHelper(LanguageHelper):
    def __init__(self, docker_helper):
        super().__init__(docker_helper, os.path.dirname(__file__), "c", "c", 1, cache_compilation=True)
