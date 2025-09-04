"""
测试 MCPServerData 模型的 YAML 序列化和反序列化功能
"""

import pytest
from msm.data.models import MCPServerData, MCPServerConfig, MCPServerStatus, ServerStatus


class TestMCPServerDataYAML:
    """测试 MCPServerData 的 YAML 方法"""

    def test_mcpserverdata_yaml(self):
        """测试 MCPServerData 的 YAML 方法"""
        config = MCPServerConfig(name="demo-server", docker_command="docker run demo")
        status = MCPServerStatus(status=ServerStatus.STOPPED)

        data = MCPServerData(config=config, status=status)

        yaml_str = data.to_yaml()
        assert isinstance(yaml_str, str)
        assert "name: demo-server" in yaml_str

        restored = MCPServerData.from_yaml(yaml_str)
        assert restored.name == data.name
        assert restored.status.status == data.status.status

    def test_mcpserverdata_yaml_error_handling(self):
        """测试 MCPServerData YAML 错误处理"""
        with pytest.raises(Exception):
            MCPServerData.from_yaml("invalid: yaml: content: [")

        with pytest.raises(Exception):
            MCPServerData.from_yaml("")


class TestMCPServerDataProperties:
    """测试 MCPServerData 的属性和方法"""

    def test_name_property(self):
        """测试 name 属性"""
        config = MCPServerConfig(name="test-server", docker_command="docker run test")
        status = MCPServerStatus(status=ServerStatus.RUNNING)

        data = MCPServerData(config=config, status=status)
        assert data.name == "test-server"

    def test_update_status(self):
        """测试 update_status 方法"""
        config = MCPServerConfig(name="test-server", docker_command="docker run test")
        old_status = MCPServerStatus(status=ServerStatus.STOPPED)
        new_status = MCPServerStatus(status=ServerStatus.RUNNING)

        data = MCPServerData(config=config, status=old_status)
        assert data.status.status == ServerStatus.STOPPED

        data.update_status(new_status)
        assert data.status.status == ServerStatus.RUNNING

    def test_update_config(self):
        """测试 update_config 方法"""
        old_config = MCPServerConfig(name="old-server", docker_command="docker run old")
        new_config = MCPServerConfig(name="new-server", docker_command="docker run new")
        status = MCPServerStatus(status=ServerStatus.RUNNING)

        data = MCPServerData(config=old_config, status=status)
        assert data.name == "old-server"

        data.update_config(new_config)
        assert data.name == "new-server"
