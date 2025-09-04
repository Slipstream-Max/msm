"""
测试 ServerStatus 枚举
"""

from msm.data.models import ServerStatus


class TestServerStatus:
    """测试 ServerStatus 枚举"""

    def test_server_status_values(self):
        """测试枚举值"""
        assert ServerStatus.RUNNING.value == "running"
        assert ServerStatus.STOPPED.value == "stopped"
        assert ServerStatus.ERROR.value == "error"
        assert ServerStatus.UNKNOWN.value == "unknown"
        assert ServerStatus.STARTING.value == "starting"
        assert ServerStatus.STOPPING.value == "stopping"

    def test_server_status_str_representation(self):
        """测试字符串表示"""
        assert str(ServerStatus.RUNNING) == "running"
        assert str(ServerStatus.STOPPED) == "stopped"
        assert str(ServerStatus.ERROR) == "error"
        assert str(ServerStatus.UNKNOWN) == "unknown"
        assert str(ServerStatus.STARTING) == "starting"
        assert str(ServerStatus.STOPPING) == "stopping"

    def test_server_status_membership(self):
        """测试枚举成员"""
        assert ServerStatus.RUNNING in ServerStatus
        assert ServerStatus.STOPPED in ServerStatus
        assert ServerStatus.ERROR in ServerStatus
        assert ServerStatus.UNKNOWN in ServerStatus
        assert ServerStatus.STARTING in ServerStatus
        assert ServerStatus.STOPPING in ServerStatus

    def test_server_status_iteration(self):
        """测试枚举迭代"""
        statuses = list(ServerStatus)
        assert len(statuses) == 6
        assert ServerStatus.RUNNING in statuses
        assert ServerStatus.STOPPED in statuses
        assert ServerStatus.ERROR in statuses
        assert ServerStatus.UNKNOWN in statuses
        assert ServerStatus.STARTING in statuses
        assert ServerStatus.STOPPING in statuses
