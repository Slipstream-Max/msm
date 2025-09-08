"""
StatusMonitor 单元测试
"""
import unittest
from unittest.mock import MagicMock, patch

from docker.errors import NotFound

from msm.core.status_monitor import StatusMonitor
from msm.data.models import ContainerStatus, MCPServerStatus, ResourceUsage


class TestStatusMonitor(unittest.TestCase):
    """StatusMonitor 的单元测试类"""

    def setUp(self):
        """测试前的设置"""
        # 使用 patch 来模拟 docker.from_env，避免在测试中连接真实的 Docker daemon
        self.patcher = patch('msm.core.status_monitor.docker.from_env')
        self.mock_docker_from_env = self.patcher.start()
        self.mock_client = MagicMock()
        self.mock_docker_from_env.return_value = self.mock_client
        
        # 创建 StatusMonitor 实例
        self.monitor = StatusMonitor()

    def tearDown(self):
        """测试后的清理"""
        self.patcher.stop()

    def test_check_container_status_running(self):
        """测试 check_container_status 方法，容器状态为 running"""
        # 模拟容器对象
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.attrs = {"State": {}}
        self.mock_client.containers.get.return_value = mock_container

        # 模拟 get_resource_usage 返回值
        self.monitor.get_resource_usage = MagicMock(return_value=ResourceUsage(cpu_usage=10.0))
        # 模拟 _get_health_status 返回值
        self.monitor._get_health_status = MagicMock(return_value="healthy")

        # 调用方法
        result = self.monitor.check_container_status("test_container_id")

        # 断言
        self.assertEqual(result.status, ContainerStatus.RUNNING)
        self.assertEqual(result.health_status, "healthy")
        self.assertIsNotNone(result.last_check)

    def test_check_container_status_not_found(self):
        """测试 check_container_status 方法，容器不存在"""
        self.mock_client.containers.get.side_effect = NotFound("Container not found")

        result = self.monitor.check_container_status("nonexistent_container_id")

        self.assertEqual(result.status, ContainerStatus.UNKNOWN)

    def test_get_resource_usage_success(self):
        """测试 get_resource_usage 方法成功获取资源"""
        # 模拟容器和 stats 数据
        mock_container = MagicMock()
        mock_stats = {
            'cpu_stats': {
                'cpu_usage': {'total_usage': 2000, 'percpu_usage': [1000, 1000]},
                'system_cpu_usage': 10000
            },
            'precpu_stats': {
                'cpu_usage': {'total_usage': 1000},
                'system_cpu_usage': 5000
            },
            'memory_stats': {'usage': 1024 * 1024},
            'networks': {
                'eth0': {'rx_bytes': 1000, 'tx_bytes': 2000}
            },
            'blkio_stats': {
                'io_service_bytes_recursive': [
                    {'op': 'Read', 'value': 512},
                    {'op': 'Write', 'value': 1024}
                ]
            },
            'pids_stats': {'current': 5}
        }
        mock_container.stats.return_value = mock_stats
        self.mock_client.containers.get.return_value = mock_container

        result = self.monitor.get_resource_usage("test_container_id")

        self.assertIsNotNone(result)
        if result is not None:  # Add this type check
            # Use assertTrue with abs for floating point comparison
            self.assertIsNotNone(result.cpu_usage)
            cpu_usage = result.cpu_usage  # This should now be safe
            assert cpu_usage is not None  # Explicit assertion for type checker
            self.assertTrue(abs(cpu_usage - 40.0) < 0.1)  # (1000/5000)*2*100
            self.assertEqual(result.memory_usage, 1024 * 1024)
            self.assertEqual(result.network_rx, 1000)
            self.assertEqual(result.network_tx, 2000)
            self.assertEqual(result.block_read, 512)
            self.assertEqual(result.block_write, 1024)
            self.assertEqual(result.pids, 5)

    def test_get_resource_usage_not_found(self):
        """测试 get_resource_usage 方法，容器不存在"""
        self.mock_client.containers.get.side_effect = NotFound("Container not found")

        result = self.monitor.get_resource_usage("nonexistent_container_id")

        self.assertIsNone(result)

    def test_health_check_healthy(self):
        """测试 health_check 方法，容器健康"""
        mock_container = MagicMock()
        mock_container.attrs = {"State": {"Health": {"Status": "healthy"}}}
        self.mock_client.containers.get.return_value = mock_container

        result = self.monitor.health_check("test_container_id")

        self.assertTrue(result)

    def test_health_check_unhealthy(self):
        """测试 health_check 方法，容器不健康"""
        mock_container = MagicMock()
        mock_container.attrs = {"State": {"Health": {"Status": "unhealthy"}}}
        self.mock_client.containers.get.return_value = mock_container

        result = self.monitor.health_check("test_container_id")

        self.assertFalse(result)

    def test_health_check_no_health_check(self):
        """测试 health_check 方法，容器没有健康检查配置"""
        mock_container = MagicMock()
        mock_container.attrs = {"State": {}}
        mock_container.status = "running"
        self.mock_client.containers.get.return_value = mock_container

        result = self.monitor.health_check("test_container_id")

        self.assertTrue(result)  # 只要容器在运行，就认为是健康的

    def test_monitor_all_containers(self):
        """测试 monitor_all_containers 方法"""
        # 模拟 ServerRegistry
        mock_registry = MagicMock()
        mock_server_data = MagicMock()
        mock_server_data.container_info.container_id = "container_1"
        mock_registry.servers.items.return_value = [("server_1", mock_server_data)]

        # 模拟 check_container_status
        self.monitor.check_container_status = MagicMock(return_value=MCPServerStatus(status=ContainerStatus.RUNNING))

        result = self.monitor.monitor_all_containers(mock_registry)

        self.assertIn("server_1", result)
        self.assertEqual(result["server_1"].status, ContainerStatus.RUNNING)

    def test_get_running_containers(self):
        """测试 get_running_containers 方法"""
        # 模拟正在运行的容器列表
        mock_container_1 = MagicMock()
        mock_container_1.id = "container_id_1"
        mock_container_2 = MagicMock()
        mock_container_2.id = "container_id_2"
        self.mock_client.containers.list.return_value = [mock_container_1, mock_container_2]

        result = self.monitor.get_running_containers()

        self.assertEqual(len(result), 2)
        self.assertIn("container_id_1", result)
        self.assertIn("container_id_2", result)

if __name__ == '__main__':
    unittest.main()
