"""
测试 MCPServerStatus 模型的 YAML 序列化和反序列化功能
"""

import pytest
from msm.data.models import MCPServerStatus, ContainerStatus, ContainerLogs, ResourceUsage


class TestMCPServerStatusYAML:
    """测试 MCPServerStatus 的 YAML 方法"""

    def test_mcpserverstatus_yaml(self):
        """测试 MCPServerStatus 的 YAML 方法"""
        status = MCPServerStatus(
            status=ContainerStatus.RUNNING,
            container_logs=ContainerLogs(logs=["log1", "log2"]),
            resource_usage=ResourceUsage(cpu_usage=10.0),
            uptime="1h 30m",
            health_status="healthy",
        )

        yaml_str = status.to_yaml()
        assert isinstance(yaml_str, str)
        assert "status: running" in yaml_str

        restored = MCPServerStatus.from_yaml(yaml_str)
        assert restored.status == status.status
        assert restored.uptime == status.uptime

    def test_mcpserverstatus_yaml_minimal(self):
        """测试 MCPServerStatus YAML 最小配置"""
        status = MCPServerStatus(status=ContainerStatus.STOPPED)

        yaml_str = status.to_yaml()
        assert isinstance(yaml_str, str)
        assert "status: stopped" in yaml_str

        restored = MCPServerStatus.from_yaml(yaml_str)
        assert restored.status == status.status
        assert restored.container_logs is None
        assert restored.resource_usage is None
        assert restored.uptime is None
        assert restored.health_status is None

    def test_mcpserverstatus_yaml_error_handling(self):
        """测试 MCPServerStatus YAML 错误处理"""
        with pytest.raises(Exception):
            MCPServerStatus.from_yaml("invalid: yaml: content: [")

        with pytest.raises(Exception):
            MCPServerStatus.from_yaml("")


class TestMCPServerStatusMethods:
    """测试 MCPServerStatus 的方法"""

    def test_is_running(self):
        """测试 is_running 方法"""
        running_status = MCPServerStatus(status=ContainerStatus.RUNNING)
        stopped_status = MCPServerStatus(status=ContainerStatus.STOPPED)

        assert running_status.is_running() is True
        assert stopped_status.is_running() is False

    def test_is_healthy(self):
        """测试 is_healthy 方法"""
        healthy_status = MCPServerStatus(
            status=ContainerStatus.RUNNING, health_status="healthy"
        )
        unhealthy_status = MCPServerStatus(
            status=ContainerStatus.RUNNING, health_status="unhealthy"
        )
        stopped_status = MCPServerStatus(status=ContainerStatus.STOPPED)

        assert healthy_status.is_healthy() is True
        assert unhealthy_status.is_healthy() is False
        assert stopped_status.is_healthy() is False

    def test_update_check_time(self):
        """测试 update_check_time 方法"""
        status = MCPServerStatus(status=ContainerStatus.RUNNING)
        old_time = status.last_check

        # 等待一小段时间
        import time
        time.sleep(0.001)

        status.update_check_time()
        new_time = status.last_check

        assert new_time > old_time
