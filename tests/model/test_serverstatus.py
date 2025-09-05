"""
测试 ServerStatus 枚举
"""

from msm.data.models import ContainerStatus


class TestServerStatus:
    """测试 ServerStatus 枚举"""

    def test_server_status_values(self):
        """测试枚举值"""
        assert ContainerStatus.RUNNING.value == "running"
        assert ContainerStatus.STOPPED.value == "stopped"
        assert ContainerStatus.ERROR.value == "error"
        assert ContainerStatus.UNKNOWN.value == "unknown"
        assert ContainerStatus.STARTING.value == "starting"
        assert ContainerStatus.STOPPING.value == "stopping"

    def test_server_status_str_representation(self):
        """测试字符串表示"""
        assert str(ContainerStatus.RUNNING) == "running"
        assert str(ContainerStatus.STOPPED) == "stopped"
        assert str(ContainerStatus.ERROR) == "error"
        assert str(ContainerStatus.UNKNOWN) == "unknown"
        assert str(ContainerStatus.STARTING) == "starting"
        assert str(ContainerStatus.STOPPING) == "stopping"

    def test_server_status_membership(self):
        """测试枚举成员"""
        assert ContainerStatus.RUNNING in ContainerStatus
        assert ContainerStatus.STOPPED in ContainerStatus
        assert ContainerStatus.ERROR in ContainerStatus
        assert ContainerStatus.UNKNOWN in ContainerStatus
        assert ContainerStatus.STARTING in ContainerStatus
        assert ContainerStatus.STOPPING in ContainerStatus

    def test_server_status_iteration(self):
        """测试枚举迭代"""
        statuses = list(ContainerStatus)
        assert len(statuses) == 6
        assert ContainerStatus.RUNNING in statuses
        assert ContainerStatus.STOPPED in statuses
        assert ContainerStatus.ERROR in statuses
        assert ContainerStatus.UNKNOWN in statuses
        assert ContainerStatus.STARTING in statuses
        assert ContainerStatus.STOPPING in statuses
