import os
import threading

from docker_evaluator.disk_helper import (
    _CACHE_BASE,
    get_cache_dir,
    get_compile_lock,
    get_temp_dir,
)


def test_get_cache_dir_creates_directory():
    d = get_cache_dir("print('hi')", "py3")
    assert os.path.isdir(d)


def test_get_cache_dir_is_deterministic():
    d1 = get_cache_dir("x = 1", "c")
    d2 = get_cache_dir("x = 1", "c")
    assert d1 == d2


def test_get_cache_dir_different_code_gives_different_dir():
    d1 = get_cache_dir("code A", "py3")
    d2 = get_cache_dir("code B", "py3")
    assert d1 != d2


def test_get_cache_dir_different_language_gives_different_dir():
    d1 = get_cache_dir("same code", "c")
    d2 = get_cache_dir("same code", "cpp")
    assert d1 != d2


def test_get_cache_dir_is_under_cache_base():
    d = get_cache_dir("some code", "py3")
    assert d.startswith(_CACHE_BASE)


def test_get_compile_lock_same_dir_returns_same_lock():
    lock1 = get_compile_lock("/some/dir")
    lock2 = get_compile_lock("/some/dir")
    assert lock1 is lock2


def test_get_compile_lock_different_dirs_return_different_locks():
    lock1 = get_compile_lock("/dir/a")
    lock2 = get_compile_lock("/dir/b")
    assert lock1 is not lock2


def test_get_compile_lock_is_a_lock():
    lock = get_compile_lock("/any/path")
    assert isinstance(lock, type(threading.Lock()))


def test_get_temp_dir_creates_test_data_subdir():
    test_data = get_temp_dir([])
    assert os.path.isdir(test_data)
    assert test_data.endswith("test_data")


def test_get_temp_dir_writes_files():
    files = [
        {"name": "target.py", "content": "print('hello')"},
        {"name": "target.in", "content": "42\n"},
    ]
    test_data = get_temp_dir(files)
    for f in files:
        path = os.path.join(test_data, f["name"])
        assert os.path.isfile(path)
        with open(path) as fh:
            assert fh.read() == f["content"]


def test_get_temp_dir_each_call_returns_distinct_dir():
    d1 = get_temp_dir([])
    d2 = get_temp_dir([])
    assert d1 != d2


def test_clear_cache_removes_cache_base(tmp_path, monkeypatch):
    import docker_evaluator.disk_helper as dh

    fake_cache = str(tmp_path / "compilation_cache")
    os.makedirs(fake_cache)
    open(os.path.join(fake_cache, "dummy"), "w").close()
    monkeypatch.setattr(dh, "_CACHE_BASE", fake_cache)
    dh.clear_cache()
    assert not os.path.exists(fake_cache)


def test_clear_cache_no_error_when_missing(monkeypatch):
    import docker_evaluator.disk_helper as dh

    monkeypatch.setattr(dh, "_CACHE_BASE", "/nonexistent/path/xyz")
    dh.clear_cache()  # should not raise
