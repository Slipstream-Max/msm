import pytest
from unittest.mock import MagicMock, patch
from msm.core.container_manager import ContainerManager
from msm.data.models import MCPServerConfig, ContainerStatus, ContainerInfo, ContainerLogs
from docker.errors import DockerException, NotFound

@pytest.fixture
def mock_docker_client():
    """Fixture for a mocked Docker client."""
    with patch('docker.from_env') as mock_from_env:
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        yield mock_client

@pytest.fixture
def container_manager(mock_docker_client):
    """Fixture for a ContainerManager with a mocked Docker client."""
    manager = ContainerManager()
    manager.client = mock_docker_client
    return manager

@pytest.fixture
def sample_config():
    """Fixture for a sample MCPServerConfig."""
    return MCPServerConfig(
        name="test-server",
        docker_command="docker run -p 8080:80 nginx:latest",
        description="A test server"
    )

class TestContainerManager:
    def test_init_success(self, mock_docker_client):
        """Test successful initialization of ContainerManager."""
        mock_docker_client.ping.return_value = True
        manager = ContainerManager()
        assert manager.client is not None
        mock_docker_client.ping.assert_called_once()

    def test_init_failure(self):
        """Test ContainerManager initialization failure."""
        with patch('docker.from_env', side_effect=DockerException("Test error")):
            with pytest.raises(ConnectionError):
                ContainerManager()

    def test_start_container_new(self, container_manager, mock_docker_client, sample_config):
        """Test starting a new container."""
        mock_docker_client.containers.get.side_effect = NotFound("not found")
        mock_container = MagicMock()
        mock_container.id = "12345"
        mock_docker_client.containers.run.return_value = mock_container

        container_id = container_manager.start_container(sample_config)

        assert container_id == "12345"
        mock_docker_client.images.pull.assert_called_with("nginx:latest")
        mock_docker_client.containers.run.assert_called_once()

    def test_start_container_existing(self, container_manager, mock_docker_client, sample_config):
        """Test starting a container that already exists."""
        mock_existing_container = MagicMock()
        mock_existing_container.id = "existing-123"
        mock_docker_client.containers.get.return_value = mock_existing_container

        container_id = container_manager.start_container(sample_config)

        assert container_id == "existing-123"
        mock_docker_client.containers.run.assert_not_called()

    def test_stop_container_success(self, container_manager, mock_docker_client):
        """Test stopping a running container."""
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_docker_client.containers.get.return_value = mock_container

        result = container_manager.stop_container("test-id")

        assert result is True
        mock_container.stop.assert_called_once()

    def test_stop_container_not_running(self, container_manager, mock_docker_client):
        """Test stopping a container that is not running."""
        mock_container = MagicMock()
        mock_container.status = "exited"
        mock_docker_client.containers.get.return_value = mock_container

        result = container_manager.stop_container("test-id")

        assert result is True
        mock_container.stop.assert_not_called()

    def test_stop_container_not_found(self, container_manager, mock_docker_client):
        """Test stopping a container that does not exist."""
        mock_docker_client.containers.get.side_effect = NotFound("not found")
        result = container_manager.stop_container("test-id")
        assert result is False

    def test_restart_container_success(self, container_manager, mock_docker_client):
        """Test restarting a container."""
        mock_container = MagicMock()
        mock_docker_client.containers.get.return_value = mock_container

        result = container_manager.restart_container("test-id")

        assert result is True
        mock_container.restart.assert_called_once()

    def test_remove_container_success(self, container_manager, mock_docker_client):
        """Test removing a container."""
        mock_container = MagicMock()
        mock_docker_client.containers.get.return_value = mock_container

        result = container_manager.remove_container("test-id")

        assert result is True
        mock_container.remove.assert_called_with(force=True)

    def test_get_container_info_success(self, container_manager, mock_docker_client):
        """Test getting container info."""
        mock_container = MagicMock()
        mock_container.id = "123"
        mock_container.name = "test-container"
        mock_container.image.tags = ["nginx:latest"]
        mock_container.image.id = "sha256:abc"
        mock_container.ports = {"80/tcp": [{"HostPort": "8080"}]}
        mock_container.attrs = {"Mounts": []}
        mock_docker_client.containers.get.return_value = mock_container

        info = container_manager.get_container_info("123")

        assert isinstance(info, ContainerInfo)
        assert info.container_id == "123"
        assert info.container_name == "test-container"

    def test_get_container_logs_success(self, container_manager, mock_docker_client):
        """Test getting container logs."""
        mock_container = MagicMock()
        mock_container.logs.return_value = b"line 1\nline 2"
        mock_docker_client.containers.get.return_value = mock_container

        logs = container_manager.get_container_logs("123")

        assert isinstance(logs, ContainerLogs)
        assert logs.logs == ["line 1", "line 2"]

    @pytest.mark.parametrize("docker_status, expected_status", [
        ("running", ContainerStatus.RUNNING),
        ("exited", ContainerStatus.STOPPED),
        ("dead", ContainerStatus.STOPPED),
        ("created", ContainerStatus.STARTING),
        ("restarting", ContainerStatus.STARTING),
        ("paused", ContainerStatus.UNKNOWN),
    ])
    def test_get_container_status(self, container_manager, mock_docker_client, docker_status, expected_status):
        """Test getting container status."""
        mock_container = MagicMock()
        mock_container.status = docker_status
        mock_docker_client.containers.get.return_value = mock_container

        status = container_manager.get_container_status("123")
        assert status == expected_status

    def test_get_container_status_not_found(self, container_manager, mock_docker_client):
        """Test getting status for a non-existent container."""
        mock_docker_client.containers.get.side_effect = NotFound("not found")
        status = container_manager.get_container_status("123")
        assert status == ContainerStatus.UNKNOWN
