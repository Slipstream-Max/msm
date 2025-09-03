"""
测试 MCP Server 数据模型的 YAML 序列化和反序列化功能
"""

import pytest
from src.msm.data.models import (
    MCPServerConfig,
    ContainerInfo,
    ContainerLogs,
    ResourceUsage,
    MCPServerStatus,
    MCPServerData,
    ServerRegistry,
    ServerStatus
)


class TestYAMLMethods:
    """测试 YAML 序列化和反序列化方法"""

    def test_mcpserverconfig_yaml(self):
        """测试 MCPServerConfig 的 YAML 方法"""
        config = MCPServerConfig(
            name="test-server",
            docker_command="docker run nginx",
            host="localhost",
            port=8080,
            description="Test server",
            auto_start=True
        )

        yaml_str = config.to_yaml()
        assert isinstance(yaml_str, str)
        assert "name: test-server" in yaml_str
        assert "docker_command: docker run nginx" in yaml_str

        # 反序列化
        restored_config = MCPServerConfig.from_yaml(yaml_str)
        assert restored_config.name == config.name
        assert restored_config.docker_command == config.docker_command
        assert restored_config.port == config.port

    def test_containerinfo_yaml(self):
        """测试 ContainerInfo 的 YAML 方法"""
        container_info = ContainerInfo(
            container_id="abc123",
            container_name="test-container",
            image="nginx:latest",
            image_id="sha256:123",
            ports={"80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}]},
            mounts=[{"Type": "bind", "Source": "/host/path", "Destination": "/container/path"}]
        )

        yaml_str = container_info.to_yaml()
        assert isinstance(yaml_str, str)
        assert "container_id: abc123" in yaml_str

        restored = ContainerInfo.from_yaml(yaml_str)
        assert restored.container_id == container_info.container_id
        assert restored.ports == container_info.ports

    def test_containerlogs_yaml(self):
        """测试 ContainerLogs 的 YAML 方法"""
        logs = ContainerLogs(
            logs=[
                "2025-09-03 10:00:00 INFO Starting nginx",
                "2025-09-03 10:00:01 INFO Listening on port 80"
            ]
        )

        yaml_str = logs.to_yaml()
        assert isinstance(yaml_str, str)
        assert "logs:" in yaml_str

        restored = ContainerLogs.from_yaml(yaml_str)
        assert restored.logs == logs.logs

    def test_resourceusage_yaml(self):
        """测试 ResourceUsage 的 YAML 方法"""
        usage = ResourceUsage(
            cpu_usage=25.5,
            memory_usage=104857600,  # 100MB
            network_rx=1024000,
            network_tx=512000,
            block_read=2048000,
            block_write=1024000,
            pids=5
        )

        yaml_str = usage.to_yaml()
        assert isinstance(yaml_str, str)
        assert "cpu_usage: 25.5" in yaml_str

        restored = ResourceUsage.from_yaml(yaml_str)
        assert restored.cpu_usage == usage.cpu_usage
        assert restored.memory_usage == usage.memory_usage

    def test_mcpserverstatus_yaml(self):
        """测试 MCPServerStatus 的 YAML 方法"""
        status = MCPServerStatus(
            status=ServerStatus.RUNNING,
            container_info=ContainerInfo(container_id="test123"),
            container_logs=ContainerLogs(logs=["log1", "log2"]),
            resource_usage=ResourceUsage(cpu_usage=10.0),
            uptime="1h 30m",
            health_status="healthy"
        )

        yaml_str = status.to_yaml()
        assert isinstance(yaml_str, str)
        assert "status: running" in yaml_str

        restored = MCPServerStatus.from_yaml(yaml_str)
        assert restored.status == status.status
        assert restored.uptime == status.uptime

    def test_mcpserverdata_yaml(self):
        """测试 MCPServerData 的 YAML 方法"""
        config = MCPServerConfig(
            name="demo-server",
            docker_command="docker run demo"
        )
        status = MCPServerStatus(status=ServerStatus.STOPPED)

        data = MCPServerData(config=config, status=status)

        yaml_str = data.to_yaml()
        assert isinstance(yaml_str, str)
        assert "name: demo-server" in yaml_str

        restored = MCPServerData.from_yaml(yaml_str)
        assert restored.name == data.name
        assert restored.status.status == data.status.status

    def test_serverregistry_yaml(self):
        """测试 ServerRegistry 的 YAML 方法"""
        registry = ServerRegistry(version="2.0.0")

        config1 = MCPServerConfig(
            name="server1",
            docker_command="docker run server1"
        )
        config2 = MCPServerConfig(
            name="server2",
            docker_command="docker run server2"
        )

        registry.add_server(config1)
        registry.add_server(config2)

        yaml_str = registry.to_yaml()
        assert isinstance(yaml_str, str)
        assert "version: 2.0.0" in yaml_str
        assert "server1:" in yaml_str
        assert "server2:" in yaml_str

        restored = ServerRegistry.from_yaml(yaml_str)
        assert restored.version == registry.version
        assert len(restored.servers) == 2
        assert "server1" in restored.servers
        assert "server2" in restored.servers

    def test_yaml_with_complex_data(self):
        """测试包含复杂数据的 YAML 序列化"""
        # 创建一个完整的服务器配置
        config = MCPServerConfig(
            name="complex-server",
            docker_command="docker run -p 8080:80 -v /data:/app/data nginx",
            host="192.168.1.100",
            port=8080,
            description="Complex demo server",
            auto_start=True,
        )

        yaml_str = config.to_yaml()
        print("\n=== Complex Config YAML ===")
        print(yaml_str)

        restored = MCPServerConfig.from_yaml(yaml_str)
        assert restored.name == config.name

    def test_yaml_error_handling(self):
        """测试 YAML 错误处理"""
        # 测试无效的 YAML 字符串
        with pytest.raises(Exception):
            MCPServerConfig.from_yaml("invalid: yaml: content: [")

        # 测试空字符串
        with pytest.raises(Exception):
            MCPServerConfig.from_yaml("")


class TestModelValidation:
    """测试模型验证"""

    def test_invalid_config(self):
        """测试无效配置"""
        with pytest.raises(ValueError):
            MCPServerConfig(
                name="invalid name with spaces",
                docker_command="docker run nginx"
            )

    def test_invalid_docker_command(self):
        """测试无效 Docker 命令"""
        with pytest.raises(ValueError):
            MCPServerConfig(
                name="test",
                docker_command="invalid command"
            )
