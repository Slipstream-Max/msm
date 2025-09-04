"""
测试 ContainerLogs 模型的 YAML 序列化和反序列化功能
"""

import pytest
from msm.data.models import ContainerLogs


class TestContainerLogsYAML:
    """测试 ContainerLogs 的 YAML 方法"""

    def test_containerlogs_yaml(self):
        """测试 ContainerLogs 的 YAML 方法"""
        logs = ContainerLogs(
            logs=[
                "2025-09-03 10:00:00 INFO Starting nginx",
                "2025-09-03 10:00:01 INFO Listening on port 80",
            ]
        )

        yaml_str = logs.to_yaml()
        assert isinstance(yaml_str, str)
        assert "logs:" in yaml_str

        restored = ContainerLogs.from_yaml(yaml_str)
        assert restored.logs == logs.logs

    def test_containerlogs_yaml_empty_logs(self):
        """测试 ContainerLogs YAML 处理空日志列表"""
        logs = ContainerLogs()

        yaml_str = logs.to_yaml()
        assert isinstance(yaml_str, str)
        assert "logs: []" in yaml_str

        restored = ContainerLogs.from_yaml(yaml_str)
        assert restored.logs == []

    def test_containerlogs_yaml_error_handling(self):
        """测试 ContainerLogs YAML 错误处理"""
        with pytest.raises(Exception):
            ContainerLogs.from_yaml("invalid: yaml: content: [")

        with pytest.raises(Exception):
            ContainerLogs.from_yaml("")
