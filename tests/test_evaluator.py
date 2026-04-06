import pytest
from unittest.mock import MagicMock, patch
from docker_evaluator.evaluator import DockerEvaluator


def _make_evaluator(language_output):
    """Return a DockerEvaluator whose language helper returns the given raw output."""
    mock_docker = MagicMock()
    mock_docker.image_exists.return_value = True  # skip image build

    with patch("docker_evaluator.evaluator.load_env_variables"):
        evaluator = DockerEvaluator(docker_client=mock_docker)

    # Replace all language helpers with a single mock for "py3"
    mock_helper = MagicMock()
    mock_helper.language = "py3"
    mock_helper.evaluate.return_value = language_output
    evaluator.language_helpers = [mock_helper]
    return evaluator, mock_helper


# --- output matching ---

def test_correct_when_output_matches():
    evaluator, _ = _make_evaluator("42\n__TIME__:10ms")
    result = evaluator.evaluate("code", "", "42", "py3", 5)
    assert result["correct"] is True


def test_correct_result_includes_time():
    evaluator, _ = _make_evaluator("hello\n__TIME__:55ms")
    result = evaluator.evaluate("code", "", "hello", "py3", 5)
    assert "55ms" in result["details"]


def test_wrong_answer_when_output_differs():
    evaluator, _ = _make_evaluator("99\n__TIME__:5ms")
    result = evaluator.evaluate("code", "", "42", "py3", 5)
    assert result["correct"] is False
    assert result["details"] == "Wrong Answer"


def test_whitespace_normalization_allows_extra_spaces():
    evaluator, _ = _make_evaluator("1  2  3\n__TIME__:5ms")
    result = evaluator.evaluate("code", "", "1 2 3", "py3", 5)
    assert result["correct"] is True


def test_whitespace_normalization_allows_trailing_newline():
    evaluator, _ = _make_evaluator("hello\n\n__TIME__:5ms")
    result = evaluator.evaluate("code", "", "hello", "py3", 5)
    assert result["correct"] is True


# --- error passthrough ---

def test_time_limit_exceeded_is_not_correct():
    evaluator, _ = _make_evaluator("Time Limit Exceeded")
    result = evaluator.evaluate("code", "", "anything", "py3", 5)
    assert result["correct"] is False
    assert "Limit Exceeded" in result["details"]


def test_memory_limit_exceeded_is_not_correct():
    evaluator, _ = _make_evaluator("Memory Limit Exceeded")
    result = evaluator.evaluate("code", "", "anything", "py3", 5)
    assert result["correct"] is False


def test_compilation_error_is_not_correct():
    evaluator, _ = _make_evaluator("Compilation Error: undefined symbol")
    result = evaluator.evaluate("code", "", "anything", "py3", 5)
    assert result["correct"] is False
    assert "Compilation Error" in result["details"]


def test_runtime_error_is_not_correct():
    evaluator, _ = _make_evaluator("Runtime Error (exit code 1)")
    result = evaluator.evaluate("code", "", "anything", "py3", 5)
    assert result["correct"] is False


# --- time suffix stripping ---

def test_time_suffix_stripped_from_output_before_compare():
    # Without stripping, "42\n__TIME__:5ms" would not equal "42"
    evaluator, _ = _make_evaluator("42\n__TIME__:5ms")
    result = evaluator.evaluate("code", "", "42", "py3", 5)
    assert result["correct"] is True


def test_ok_time_unavailable_when_no_time_suffix():
    evaluator, _ = _make_evaluator("42")
    result = evaluator.evaluate("code", "", "42", "py3", 5)
    assert result["correct"] is True
    assert "time unavailable" in result["details"]


# --- memory floor ---

def test_memory_limit_enforced_to_256mb_minimum():
    evaluator, mock_helper = _make_evaluator("ok\n__TIME__:1ms")
    evaluator.evaluate("code", "", "ok", "py3", 5, memory_limit=1024)  # 1 MB — below floor
    _, kwargs = mock_helper.evaluate.call_args
    assert kwargs["memory_limit"] == 256 * 1024


def test_memory_limit_above_floor_passed_through():
    evaluator, mock_helper = _make_evaluator("ok\n__TIME__:1ms")
    evaluator.evaluate("code", "", "ok", "py3", 5, memory_limit=512 * 1024)
    _, kwargs = mock_helper.evaluate.call_args
    assert kwargs["memory_limit"] == 512 * 1024


# --- parameter forwarding ---

def test_evaluate_forwards_input_type_and_file_io_name():
    evaluator, mock_helper = _make_evaluator("result\n__TIME__:1ms")
    evaluator.evaluate("code", "stdin_data", "result", "py3", 5,
                       input_type="file", file_io_name="data")
    mock_helper.evaluate.assert_called_once_with(
        "code", "stdin_data", 5, "file", "data", memory_limit=256 * 1024
    )
