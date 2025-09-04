"""
测试 MCPServerConfig 模型的 YAML 序列化和反序列化功能以及验证逻辑
"""

import pytest
from msm.data.models import MCPServerConfig


class TestMCPServerConfigYAML:
    """测试 MCPServerConfig 的 YAML 方法"""

    def test_mcpserverconfig_yaml(self):
        """测试 MCPServerConfig 的 YAML 方法"""
        config = MCPServerConfig(
            name="test-server",
            docker_command="docker run nginx",
            host="localhost",
            port=8080,
            description="Test server",
            auto_start=True,
            health_check={
                "test": ["CMD", "curl", "-f", "http://localhost/health"],
                "interval": 30000000000,  # 30秒
                "timeout": 10000000000,  # 10秒
                "retries": 3,
            },
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


class TestMCPServerConfigValidation:
    """测试 MCPServerConfig 的验证逻辑"""

    def test_invalid_config(self):
        """测试无效配置"""
        with pytest.raises(ValueError):
            MCPServerConfig(
                name="invalid name with spaces", docker_command="docker run nginx"
            )

    def test_invalid_docker_command(self):
        """测试无效 Docker 命令"""
        with pytest.raises(ValueError):
            MCPServerConfig(name="test", docker_command="invalid command")

    def test_empty_name(self):
        """测试空名称"""
        with pytest.raises(ValueError):
            MCPServerConfig(name="", docker_command="docker run nginx")

    def test_name_with_special_chars(self):
        """测试名称包含特殊字符"""
        with pytest.raises(ValueError):
            MCPServerConfig(name="test@server", docker_command="docker run nginx")

    def test_name_with_dots(self):
        """测试名称包含点号"""
        with pytest.raises(ValueError):
            MCPServerConfig(name="test.server", docker_command="docker run nginx")

    def test_docker_command_not_starting_with_docker(self):
        """测试 Docker 命令不以 docker 开头"""
        with pytest.raises(ValueError):
            MCPServerConfig(name="test", docker_command="podman run nginx")

    def test_docker_command_empty(self):
        """测试空 Docker 命令"""
        with pytest.raises(ValueError):
            MCPServerConfig(name="test", docker_command="")

    def test_invalid_port_negative(self):
        """测试无效端口（负数）"""
        with pytest.raises(ValueError):
            MCPServerConfig(name="test", docker_command="docker run nginx", port=-1)

    def test_invalid_port_zero(self):
        """测试无效端口（0）"""
        with pytest.raises(ValueError):
            MCPServerConfig(name="test", docker_command="docker run nginx", port=0)

    def test_invalid_port_too_high(self):
        """测试无效端口（超过65535）"""
        with pytest.raises(ValueError):
            MCPServerConfig(name="test", docker_command="docker run nginx", port=70000)
