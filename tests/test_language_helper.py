import os
import pytest
from unittest.mock import MagicMock, patch, call
from docker_evaluator.language_helpers.language_helper import LanguageHelper


def _make_helper(docker_helper, language="py3", file_extension="py",
                 multiplier=5, memory_overhead_mb=64, cache_compilation=False):
    """Instantiate a LanguageHelper without actually touching Docker."""
    with patch.object(LanguageHelper, "initialize"):
        helper = LanguageHelper(
            docker_helper,
            "/fake/context",
            language,
            file_extension,
            multiplier,
            memory_overhead_mb=memory_overhead_mb,
            cache_compilation=cache_compilation,
        )
    return helper


@pytest.fixture
def docker_helper():
    m = MagicMock()
    m.evaluate.return_value = "42\n__TIME__:5ms"
    return m


# --- initialization ---

def test_initialize_skips_build_when_image_exists():
    dh = MagicMock()
    dh.image_exists.return_value = True
    LanguageHelper(dh, "/ctx", "py3", "py", 5)
    dh.create_image.assert_not_called()


def test_initialize_builds_when_image_missing():
    dh = MagicMock()
    dh.image_exists.return_value = False
    LanguageHelper(dh, "/ctx", "py3", "py", 5)
    dh.create_image.assert_called_once()


def test_image_name_uses_docker_evaluator_prefix():
    dh = MagicMock()
    dh.image_exists.return_value = True
    helper = LanguageHelper(dh, "/ctx", "py3", "py", 5)
    assert helper.docker_image_name == "docker-evaluator-py3"


# --- time limit multiplier ---

def test_evaluate_applies_time_multiplier(docker_helper):
    helper = _make_helper(docker_helper, multiplier=5)
    helper.evaluate("code", "", 2)
    env = docker_helper.evaluate.call_args[1]["environment_variables"]
    # effective = 2 * 5 + 0.2 grace = 10.2
    assert env["TIME_LIMIT"] == pytest.approx(10.2)


def test_evaluate_multiplier_one_for_compiled(docker_helper):
    helper = _make_helper(docker_helper, language="c", file_extension="c", multiplier=1)
    helper.evaluate("code", "", 3)
    env = docker_helper.evaluate.call_args[1]["environment_variables"]
    assert env["TIME_LIMIT"] == pytest.approx(3.2)


# --- memory calculation ---

def test_evaluate_passes_total_memory_to_docker(docker_helper):
    helper = _make_helper(docker_helper, memory_overhead_mb=64)
    helper.evaluate("code", "", 5, memory_limit=256 * 1024)  # 256MB
    kwargs = docker_helper.evaluate.call_args[1]
    assert kwargs["memory_limit_mb"] == 256 + 64  # 320


def test_evaluate_compiled_language_enforces_compile_memory_floor(docker_helper):
    helper = _make_helper(docker_helper, language="c", file_extension="c",
                          multiplier=1, memory_overhead_mb=32, cache_compilation=True)
    # 256MB + 32MB overhead = 288MB < 1536MB floor for compiled langs
    helper.evaluate("code", "", 5, memory_limit=256 * 1024)
    kwargs = docker_helper.evaluate.call_args[1]
    assert kwargs["memory_limit_mb"] == 1536


# --- environment variables ---

def test_evaluate_sets_input_type_env_var(docker_helper):
    helper = _make_helper(docker_helper)
    helper.evaluate("code", "", 5, input_type="file", file_io_name="data")
    env = docker_helper.evaluate.call_args[1]["environment_variables"]
    assert env["INPUT_TYPE"] == "file"
    assert env["FILE_IO_NAME"] == "data"


def test_evaluate_sets_memory_limit_kb_env_var(docker_helper):
    helper = _make_helper(docker_helper)
    helper.evaluate("code", "", 5, memory_limit=262144)
    env = docker_helper.evaluate.call_args[1]["environment_variables"]
    assert env["MEMORY_LIMIT_KB"] == "262144"


def test_evaluate_sets_utf8_locale(docker_helper):
    helper = _make_helper(docker_helper)
    helper.evaluate("code", "", 5)
    env = docker_helper.evaluate.call_args[1]["environment_variables"]
    assert env["LANG"] == "C.UTF-8"
    assert env["LC_ALL"] == "C.UTF-8"


# --- file staging ---

def test_evaluate_stages_source_file_with_correct_extension(docker_helper, tmp_path):
    helper = _make_helper(docker_helper, file_extension="py")

    staged_files = []

    def capture_temp_dir(files):
        staged_files.extend(files)
        return str(tmp_path)

    with patch("docker_evaluator.language_helpers.language_helper.get_temp_dir", side_effect=capture_temp_dir):
        helper.evaluate("print(42)", "5", 5)

    names = [f["name"] for f in staged_files]
    assert "target.py" in names
    assert "target.in" in names


def test_evaluate_stages_correct_code_content(docker_helper, tmp_path):
    helper = _make_helper(docker_helper, file_extension="c")
    staged_files = []

    def capture_temp_dir(files):
        staged_files.extend(files)
        return str(tmp_path)

    with patch("docker_evaluator.language_helpers.language_helper.get_temp_dir", side_effect=capture_temp_dir):
        helper.evaluate("int main(){}", "input_data", 5)

    src = next(f for f in staged_files if f["name"] == "target.c")
    assert src["content"] == "int main(){}"
    inp = next(f for f in staged_files if f["name"] == "target.in")
    assert inp["content"] == "input_data"


# --- caching ---

def test_no_cache_dir_passed_when_cache_disabled(docker_helper, tmp_path):
    helper = _make_helper(docker_helper, cache_compilation=False)

    with patch("docker_evaluator.language_helpers.language_helper.get_temp_dir", return_value=str(tmp_path)):
        helper.evaluate("code", "", 5)

    kwargs = docker_helper.evaluate.call_args[1]
    assert kwargs.get("cache_dir") is None


def test_cache_dir_passed_when_cache_enabled(docker_helper, tmp_path):
    helper = _make_helper(docker_helper, language="c", file_extension="c",
                          multiplier=1, cache_compilation=True)
    fake_cache = str(tmp_path / "cache_dir")
    os.makedirs(fake_cache)

    with patch("docker_evaluator.language_helpers.language_helper.get_temp_dir", return_value=str(tmp_path)), \
         patch("docker_evaluator.language_helpers.language_helper.get_cache_dir", return_value=fake_cache):
        helper.evaluate("code", "", 5)

    kwargs = docker_helper.evaluate.call_args[1]
    assert kwargs.get("cache_dir") == fake_cache
