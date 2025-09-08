"""
MCPServerManager 单元测试
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from msm.core.mcp_manager import MCPServerManager
from msm.data.models import ContainerStatus, MCPServerConfig, MCPServerData, MCPServerStatus, ContainerInfo


class TestMCPServerManager(unittest.TestCase):
    """MCPServerManager 的单元测试类"""

    def setUp(self):
        """测试前的设置"""
        # 使用 patch 来模拟 ContainerManager 和 StatusMonitor
        self.container_manager_patcher = patch('msm.core.mcp_manager.ContainerManager')
        self.status_monitor_patcher = patch('msm.core.mcp_manager.StatusMonitor')
        
        self.mock_container_manager_class = self.container_manager_patcher.start()
        self.mock_status_monitor_class = self.status_monitor_patcher.start()
        
        self.mock_container_manager = MagicMock()
        self.mock_status_monitor = MagicMock()
        
        self.mock_container_manager_class.return_value = self.mock_container_manager
        self.mock_status_monitor_class.return_value = self.mock_status_monitor
        
        # 创建 MCPServerManager 实例
        self.manager = MCPServerManager()

    def tearDown(self):
        """测试后的清理"""
        self.container_manager_patcher.stop()
        self.status_monitor_patcher.stop()

    def test_start_server_success(self):
        """测试 start_server 方法成功启动服务器"""
        # 准备测试数据
        config = MCPServerConfig(name="test_server", docker_command="docker run test_image")
        server_data = MCPServerData(config=config, status=MCPServerStatus(status=ContainerStatus.UNKNOWN, last_check=datetime.now()))
        self.manager.registry.servers["test_server"] = server_data

        # 模拟 ContainerManager 的行为
        self.mock_container_manager.start_container.return_value = "container_123"
        self.mock_container_manager.get_container_info.return_value = MagicMock(container_id="container_123")
        
        # 模拟 StatusMonitor 的行为
        self.mock_status_monitor.check_container_status.return_value = MCPServerStatus(status=ContainerStatus.RUNNING, last_check=datetime.now())

        # 调用方法
        result = self.manager.start_server("test_server")

        # 断言
        self.assertTrue(result)
        self.mock_container_manager.start_container.assert_called_once_with(config)
        self.assertIsNotNone(server_data.container_info)
        container_info = server_data.container_info
        assert container_info is not None  # Explicit assertion for type checker
        self.assertEqual(container_info.container_id, "container_123")
        self.assertEqual(server_data.status.status, ContainerStatus.RUNNING)

    def test_start_server_not_found(self):
        """测试 start_server 方法，服务器未找到"""
        result = self.manager.start_server("nonexistent_server")
        self.assertFalse(result)

    def test_stop_server_success(self):
        """测试 stop_server 方法成功停止服务器"""
        # 准备测试数据
        config = MCPServerConfig(name="test_server", docker_command="docker run test_image")
        server_data = MCPServerData(
            config=config,
            container_info=ContainerInfo(container_id="container_123"),
            status=MCPServerStatus(status=ContainerStatus.RUNNING, last_check=datetime.now())
        )
        self.manager.registry.servers["test_server"] = server_data

        # 模拟 ContainerManager 的行为
        self.mock_container_manager.stop_container.return_value = True
        
        # 模拟 StatusMonitor 的行为
        self.mock_status_monitor.check_container_status.return_value = MCPServerStatus(status=ContainerStatus.STOPPED, last_check=datetime.now())

        # 调用方法
        result = self.manager.stop_server("test_server")

        # 断言
        self.assertTrue(result)
        self.mock_container_manager.stop_container.assert_called_once_with("container_123")
        self.assertEqual(server_data.status.status, ContainerStatus.STOPPED)

    def test_stop_server_not_found(self):
        """测试 stop_server 方法，服务器未找到或未运行"""
        result = self.manager.stop_server("nonexistent_server")
        self.assertFalse(result)

    def test_restart_server_success(self):
        """测试 restart_server 方法成功重启服务器"""
        # 准备测试数据
        config = MCPServerConfig(name="test_server", docker_command="docker run test_image")
        server_data = MCPServerData(
            config=config,
            container_info=ContainerInfo(container_id="container_123"),
            status=MCPServerStatus(status=ContainerStatus.RUNNING, last_check=datetime.now())
        )
        self.manager.registry.servers["test_server"] = server_data

        # 模拟 ContainerManager 的行为
        self.mock_container_manager.restart_container.return_value = True
        
        # 模拟 StatusMonitor 的行为
        self.mock_status_monitor.check_container_status.return_value = MCPServerStatus(status=ContainerStatus.RUNNING, last_check=datetime.now())

        # 调用方法
        result = self.manager.restart_server("test_server")

        # 断言
        self.assertTrue(result)
        self.mock_container_manager.restart_container.assert_called_once_with("container_123")
        self.assertEqual(server_data.status.status, ContainerStatus.RUNNING)

    def test_get_server_status_success(self):
        """测试 get_server_status 方法成功获取状态"""
        # 准备测试数据
        config = MCPServerConfig(name="test_server", docker_command="docker run test_image")
        server_data = MCPServerData(
            config=config,
            container_info=ContainerInfo(container_id="container_123"),
            status=MCPServerStatus(status=ContainerStatus.UNKNOWN, last_check=datetime.now())
        )
        self.manager.registry.servers["test_server"] = server_data

        # 模拟 StatusMonitor 的行为
        mock_status = MCPServerStatus(status=ContainerStatus.RUNNING, last_check=datetime.now())
        self.mock_status_monitor.check_container_status.return_value = mock_status

        # 调用方法
        result = self.manager.get_server_status("test_server")

        # 断言
        self.assertEqual(result, mock_status)
        self.assertEqual(server_data.status, mock_status)

    def test_get_server_status_not_found(self):
        """测试 get_server_status 方法，服务器未找到"""
        result = self.manager.get_server_status("nonexistent_server")
        self.assertIsNone(result)

    def test_list_all_servers(self):
        """测试 list_all_servers 方法"""
        # 准备测试数据
        config1 = MCPServerConfig(name="server1", docker_command="docker run image1")
        config2 = MCPServerConfig(name="server2", docker_command="docker run image2")
        
        server_data1 = MCPServerData(config=config1, status=MCPServerStatus(status=ContainerStatus.UNKNOWN, last_check=datetime.now()))
        server_data2 = MCPServerData(config=config2, status=MCPServerStatus(status=ContainerStatus.UNKNOWN, last_check=datetime.now()))
        # 提供 container_info 以便 list_all_servers 能更新状态
        server_data1.update_container_info(ContainerInfo(container_id="c1"))
        server_data2.update_container_info(ContainerInfo(container_id="c2"))

        self.manager.registry.servers = {
            "server1": server_data1,
            "server2": server_data2
        }

        # 模拟 StatusMonitor 的行为
        self.mock_status_monitor.check_container_status.side_effect = [
            MCPServerStatus(status=ContainerStatus.RUNNING, last_check=datetime.now()),
            MCPServerStatus(status=ContainerStatus.STOPPED, last_check=datetime.now())
        ]

        # 调用方法
        result = self.manager.list_all_servers()

        # 断言
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].config.name, "server1")
        self.assertEqual(result[0].status.status, ContainerStatus.RUNNING)
        self.assertEqual(result[1].config.name, "server2")
        self.assertEqual(result[1].status.status, ContainerStatus.STOPPED)

if __name__ == '__main__':
    unittest.main()
