import hashlib
import os
import shutil
import tempfile
import threading

_compile_locks = {}
_compile_locks_mutex = threading.Lock()


def get_compile_lock(cache_dir):
    with _compile_locks_mutex:
        if cache_dir not in _compile_locks:
            _compile_locks[cache_dir] = threading.Lock()
        return _compile_locks[cache_dir]


_CACHE_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "compilation_cache"))


def get_cache_dir(code, language):
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    cache_dir = os.path.join(_CACHE_BASE, language, code_hash)
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def clear_cache():
    if os.path.exists(_CACHE_BASE):
        shutil.rmtree(_CACHE_BASE)
    print("Compilation cache cleared.")


def get_temp_dir(files):
    temp_dir = tempfile.mkdtemp()
    test_data_dir = os.path.join(temp_dir, "test_data")
    os.makedirs(test_data_dir, exist_ok=True)
    for file in files:
        with open(os.path.join(test_data_dir, file["name"]), "w", encoding="utf-8", errors="replace") as file_writer:
            file_writer.write(file["content"])
    return test_data_dir
