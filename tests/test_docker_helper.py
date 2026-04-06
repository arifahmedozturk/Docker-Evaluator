from unittest.mock import MagicMock, patch

import docker
import pytest
from docker.errors import ContainerError

from docker_evaluator.docker_helper import DockerHelper


@pytest.fixture
def mock_docker_client():
    with patch("docker_evaluator.docker_helper.docker.from_env") as mock_from_env:
        client = MagicMock()
        mock_from_env.return_value = client
        yield client


@pytest.fixture
def helper(mock_docker_client):
    return DockerHelper()


# --- image_exists ---


def test_image_exists_returns_true_when_present(helper, mock_docker_client):
    mock_docker_client.images.get.return_value = MagicMock()
    assert helper.image_exists("docker-evaluator-py3:latest") is True


def test_image_exists_returns_false_when_absent(helper, mock_docker_client):
    mock_docker_client.images.get.side_effect = docker.errors.ImageNotFound("not found")
    assert helper.image_exists("docker-evaluator-py3:latest") is False


def test_image_exists_returns_false_when_no_images(helper, mock_docker_client):
    mock_docker_client.images.get.side_effect = docker.errors.ImageNotFound("not found")
    assert helper.image_exists("docker-evaluator-py3:latest") is False


# --- create_image ---


def test_create_image_calls_build(helper, mock_docker_client):
    helper.create_image("/some/path", "my-image:latest")
    mock_docker_client.images.build.assert_called_once_with(path="/some/path", tag="my-image:latest")


# --- evaluate ---


def test_evaluate_returns_decoded_output(helper, mock_docker_client):
    mock_docker_client.containers.run.return_value = b"42\n"
    result = helper.evaluate("img", "/tmp/vol", {})
    assert result == "42"


def test_evaluate_strips_trailing_whitespace(helper, mock_docker_client):
    mock_docker_client.containers.run.return_value = b"hello   \n\n"
    result = helper.evaluate("img", "/tmp/vol", {})
    assert result == "hello"


def test_evaluate_oom_returns_memory_limit_exceeded(helper, mock_docker_client):
    err = ContainerError("img", 137, "cmd", "img", b"")
    mock_docker_client.containers.run.side_effect = err
    result = helper.evaluate("img", "/tmp/vol", {})
    assert result == "Memory Limit Exceeded"


def test_evaluate_nonzero_exit_returns_runtime_error(helper, mock_docker_client):
    err = ContainerError("img", 1, "cmd", "img", b"")
    mock_docker_client.containers.run.side_effect = err
    result = helper.evaluate("img", "/tmp/vol", {})
    assert "Runtime Error" in result
    assert "1" in result


def test_evaluate_mounts_cache_dir_when_provided(helper, mock_docker_client):
    mock_docker_client.containers.run.return_value = b""
    helper.evaluate("img", "/tmp/vol", {}, cache_dir="/tmp/cache")
    call_kwargs = mock_docker_client.containers.run.call_args[1]
    volumes = call_kwargs["volumes"]
    assert "/tmp/cache" in volumes
    assert volumes["/tmp/cache"]["bind"] == "/cache"


def test_evaluate_no_cache_dir_omits_cache_volume(helper, mock_docker_client):
    mock_docker_client.containers.run.return_value = b""
    helper.evaluate("img", "/tmp/vol", {})
    call_kwargs = mock_docker_client.containers.run.call_args[1]
    volumes = call_kwargs["volumes"]
    assert len(volumes) == 1  # only the test_data volume


def test_evaluate_sets_network_disabled(helper, mock_docker_client):
    mock_docker_client.containers.run.return_value = b""
    helper.evaluate("img", "/tmp/vol", {})
    call_kwargs = mock_docker_client.containers.run.call_args[1]
    assert call_kwargs["network_disabled"] is True


def test_close_calls_client_close(helper, mock_docker_client):
    helper.close()
    mock_docker_client.close.assert_called_once()
