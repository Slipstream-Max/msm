"""
测试 ServerRegistry 模型的 YAML 序列化和反序列化功能
"""

import pytest
from msm.data.models import ServerRegistry, MCPServerConfig, MCPServerStatus, ContainerStatus


class TestServerRegistryYAML:
    """测试 ServerRegistry 的 YAML 方法"""

    def test_serverregistry_yaml(self):
        """测试 ServerRegistry 的 YAML 方法"""
        registry = ServerRegistry(version="2.0.0")

        config1 = MCPServerConfig(name="server1", docker_command="docker run server1")
        config2 = MCPServerConfig(name="server2", docker_command="docker run server2")

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

    def test_serverregistry_yaml_empty(self):
        """测试 ServerRegistry YAML 空注册表"""
        registry = ServerRegistry()

        yaml_str = registry.to_yaml()
        assert isinstance(yaml_str, str)
        assert "servers: {}" in yaml_str

        restored = ServerRegistry.from_yaml(yaml_str)
        assert len(restored.servers) == 0

    def test_serverregistry_yaml_error_handling(self):
        """测试 ServerRegistry YAML 错误处理"""
        with pytest.raises(Exception):
            ServerRegistry.from_yaml("invalid: yaml: content: [")

        with pytest.raises(Exception):
            ServerRegistry.from_yaml("")


class TestServerRegistryMethods:
    """测试 ServerRegistry 的方法"""

    def test_add_server(self):
        """测试 add_server 方法"""
        registry = ServerRegistry()
        config = MCPServerConfig(name="test-server", docker_command="docker run test")

        # 添加新服务器
        result = registry.add_server(config)
        assert result is True
        assert "test-server" in registry.servers
        assert registry.servers["test-server"].name == "test-server"

        # 尝试添加已存在的服务器
        result = registry.add_server(config)
        assert result is False

    def test_remove_server(self):
        """测试 remove_server 方法"""
        registry = ServerRegistry()
        config = MCPServerConfig(name="test-server", docker_command="docker run test")

        registry.add_server(config)

        # 删除存在的服务器
        result = registry.remove_server("test-server")
        assert result is True
        assert "test-server" not in registry.servers

        # 尝试删除不存在的服务器
        result = registry.remove_server("non-existent")
        assert result is False

    def test_get_server(self):
        """测试 get_server 方法"""
        registry = ServerRegistry()
        config = MCPServerConfig(name="test-server", docker_command="docker run test")

        registry.add_server(config)

        # 获取存在的服务器
        server = registry.get_server("test-server")
        assert server is not None
        assert server.name == "test-server"

        # 获取不存在的服务器
        server = registry.get_server("non-existent")
        assert server is None

    def test_list_servers(self):
        """测试 list_servers 方法"""
        registry = ServerRegistry()
        config1 = MCPServerConfig(name="server1", docker_command="docker run server1")
        config2 = MCPServerConfig(name="server2", docker_command="docker run server2")

        registry.add_server(config1)
        registry.add_server(config2)

        servers = registry.list_servers()
        assert len(servers) == 2
        server_names = [s.name for s in servers]
        assert "server1" in server_names
        assert "server2" in server_names

    def test_update_server_status(self):
        """测试 update_server_status 方法"""
        registry = ServerRegistry()
        config = MCPServerConfig(name="test-server", docker_command="docker run test")
        registry.add_server(config)

        new_status = MCPServerStatus(status=ContainerStatus.RUNNING)

        # 更新存在的服务器状态
        result = registry.update_server_status("test-server", new_status)
        assert result is True
        assert registry.servers["test-server"].status.status == ContainerStatus.RUNNING

        # 更新不存在的服务器状态
        result = registry.update_server_status("non-existent", new_status)
        assert result is False

    def test_update_server_config(self):
        """测试 update_server_config 方法"""
        registry = ServerRegistry()
        config = MCPServerConfig(name="test-server", docker_command="docker run test")
        registry.add_server(config)

        new_config = MCPServerConfig(name="test-server", docker_command="docker run updated")

        # 更新存在的服务器配置
        result = registry.update_server_config("test-server", new_config)
        assert result is True
        assert registry.servers["test-server"].config.docker_command == "docker run updated"

        # 更新不存在的服务器配置
        result = registry.update_server_config("non-existent", new_config)
        assert result is False

    def test_server_exists(self):
        """测试 server_exists 方法"""
        registry = ServerRegistry()
        config = MCPServerConfig(name="test-server", docker_command="docker run test")

        assert registry.server_exists("test-server") is False

        registry.add_server(config)
        assert registry.server_exists("test-server") is True

    def test_get_running_servers(self):
        """测试 get_running_servers 方法"""
        registry = ServerRegistry()

        config1 = MCPServerConfig(name="running-server", docker_command="docker run running")
        config2 = MCPServerConfig(name="stopped-server", docker_command="docker run stopped")

        registry.add_server(config1)
        registry.add_server(config2)

        # 设置状态
        running_status = MCPServerStatus(status=ContainerStatus.RUNNING)
        stopped_status = MCPServerStatus(status=ContainerStatus.STOPPED)

        registry.update_server_status("running-server", running_status)
        registry.update_server_status("stopped-server", stopped_status)

        running_servers = registry.get_running_servers()
        assert len(running_servers) == 1
        assert running_servers[0].name == "running-server"

    def test_get_server_count(self):
        """测试 get_server_count 方法"""
        registry = ServerRegistry()

        assert registry.get_server_count() == 0

        config = MCPServerConfig(name="test-server", docker_command="docker run test")
        registry.add_server(config)

        assert registry.get_server_count() == 1
