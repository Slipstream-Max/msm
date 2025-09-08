"""
MCP 服务器管理器

这个模块提供了 `MCPServerManager` 类，用于管理多个 MCP 服务器实例。
它协调 `ContainerManager` 和 `StatusMonitor` 来提供完整的生命周期管理和状态监控功能。
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional

from msm.core.container_manager import ContainerManager
from msm.core.status_monitor import StatusMonitor
from msm.data.models import MCPServerData, MCPServerStatus, ServerRegistry, ContainerStatus

logger = logging.getLogger(__name__)

class MCPServerManager:
    """
    MCP 服务器管理器
    """

    def __init__(self):
        """
        初始化 MCPServerManager
        """
        self.container_manager = ContainerManager()
        self.status_monitor = StatusMonitor()
        self.registry = ServerRegistry()

    def start_server(self, name: str) -> bool:
        """
        启动指定的 MCP 服务器

        :param name: 服务器名称
        :return: 如果成功启动则返回 True
        """
        server_data = self.registry.servers.get(name)
        if not server_data:
            logger.error(f"找不到名为 '{name}' 的服务器配置")
            return False

        try:
            # 启动容器
            container_id = self.container_manager.start_container(server_data.config)
            
            # 更新注册表中的容器信息
            if not server_data.container_info:
                server_data.container_info = self.container_manager.get_container_info(container_id)
            else:
                server_data.container_info.container_id = container_id
            
            # 获取并更新状态
            server_data.status = self.status_monitor.check_container_status(container_id)
            
            logger.info(f"成功启动服务器 '{name}'")
            return True
        except Exception as e:
            logger.error(f"启动服务器 '{name}' 失败: {e}")
            return False

    def stop_server(self, name: str) -> bool:
        """
        停止指定的 MCP 服务器

        :param name: 服务器名称
        :return: 如果成功停止则返回 True
        """
        server_data = self.registry.servers.get(name)
        if not server_data or not server_data.container_info or not server_data.container_info.container_id:
            logger.error(f"找不到正在运行的服务器 '{name}'")
            return False

        try:
            container_id = server_data.container_info.container_id
            success = self.container_manager.stop_container(container_id)
            
            if success:
                # 更新状态
                server_data.status = self.status_monitor.check_container_status(container_id)
                logger.info(f"成功停止服务器 '{name}'")
            
            return success
        except Exception as e:
            logger.error(f"停止服务器 '{name}' 失败: {e}")
            return False

    def restart_server(self, name: str) -> bool:
        """
        重启指定的 MCP 服务器

        :param name: 服务器名称
        :return: 如果成功重启则返回 True
        """
        server_data = self.registry.servers.get(name)
        if not server_data or not server_data.container_info or not server_data.container_info.container_id:
            logger.error(f"找不到正在运行的服务器 '{name}'")
            return False

        try:
            container_id = server_data.container_info.container_id
            success = self.container_manager.restart_container(container_id)
            
            if success:
                # 更新状态
                server_data.status = self.status_monitor.check_container_status(container_id)
                logger.info(f"成功重启服务器 '{name}'")
            
            return success
        except Exception as e:
            logger.error(f"重启服务器 '{name}' 失败: {e}")
            return False

    def start_all_servers(self) -> Dict[str, bool]:
        """
        启动所有已注册的 MCP 服务器

        :return: 一个字典，键为服务器名称，值为启动是否成功
        """
        results = {}
        for name in self.registry.servers.keys():
            results[name] = self.start_server(name)
        return results

    def stop_all_servers(self) -> Dict[str, bool]:
        """
        停止所有已注册的 MCP 服务器

        :return: 一个字典，键为服务器名称，值为停止是否成功
        """
        results = {}
        # 为了安全，我们反向停止，但这取决于具体需求
        for name in reversed(list(self.registry.servers.keys())):
            results[name] = self.stop_server(name)
        return results

    def get_server_status(self, name: str) -> Optional[MCPServerStatus]:
        """
        获取指定服务器的当前状态

        :param name: 服务器名称
        :return: MCPServerStatus 对象或 None
        """
        server_data = self.registry.servers.get(name)
        if not server_data or not server_data.container_info or not server_data.container_info.container_id:
            return None

        try:
            container_id = server_data.container_info.container_id
            status = self.status_monitor.check_container_status(container_id)
            # 更新注册表中的状态
            server_data.status = status
            return status
        except Exception as e:
            logger.error(f"获取服务器 '{name}' 状态失败: {e}")
            return None

    def get_server_logs(self, name: str) -> Optional[str]:
        """
        获取指定服务器的容器日志

        :param name: 服务器名称
        :return: 日志字符串或 None
        """
        server_data = self.registry.servers.get(name)
        if not server_data or not server_data.container_info or not server_data.container_info.container_id:
            return None

        try:
            container_id = server_data.container_info.container_id
            logs = self.container_manager.get_container_logs(container_id)
            return "\n".join(logs.logs)
        except Exception as e:
            logger.error(f"获取服务器 '{name}' 日志失败: {e}")
            return None

    def list_all_servers(self) -> List[MCPServerData]:
        """
        列出所有已注册的服务器及其当前状态

        :return: MCPServerData 对象列表
        """
        # 更新所有服务器的状态
        for name, server_data in self.registry.servers.items():
            if server_data.container_info and server_data.container_info.container_id:
                try:
                    server_data.status = self.status_monitor.check_container_status(server_data.container_info.container_id)
                except Exception as e:
                    logger.error(f"更新服务器 '{name}' 状态失败: {e}")
                    server_data.status = MCPServerStatus(status=ContainerStatus.ERROR, last_check=datetime.now())
        
        return list(self.registry.servers.values())
