"""
状态监控器

这个模块提供了 `StatusMonitor` 类，用于监控 Docker 容器的状态和资源使用情况。
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional

import docker
from docker.errors import DockerException, NotFound

from msm.data.models import (
    ContainerStatus,
    MCPServerStatus,
    ResourceUsage,
    ServerRegistry,
)

logger = logging.getLogger(__name__)

class StatusMonitor:
    """
    状态监控器
    """

    def __init__(self, docker_host: Optional[str] = None):
        """
        初始化 StatusMonitor

        :param docker_host: Docker daemon 的 URL，例如 'tcp://127.0.0.1:2375'
        """
        try:
            if docker_host:
                self.client = docker.DockerClient(base_url=docker_host)
                logger.info(f"连接到远程 Docker daemon: {docker_host}")
            else:
                self.client = docker.from_env()
                logger.info("从环境变量连接到本地 Docker daemon")
            self.client.ping()
            logger.info("成功连接到 Docker daemon")
        except DockerException as e:
            logger.error(f"无法连接到 Docker daemon: {e}")
            raise ConnectionError(f"无法连接到 Docker daemon: {e}") from e

    def check_container_status(self, container_id: str) -> MCPServerStatus:
        """
        检查容器的状态

        :param container_id: 容器 ID 或名称
        :return: MCPServerStatus 对象
        """
        try:
            container = self.client.containers.get(container_id)
            container.reload()
            
            # 获取容器状态
            status = ContainerStatus.from_docker_status(container.status)

            # 获取资源使用情况
            resource_usage = self.get_resource_usage(container_id)
            
            # 获取健康状态（如果有的话）
            health_status = self._get_health_status(container)
            
            return MCPServerStatus(
                status=status,
                resource_usage=resource_usage,
                health_status=health_status,
                last_check=datetime.now()
            )
        except NotFound:
            logger.warning(f"检查状态时找不到容器: {container_id}")
            return MCPServerStatus(
                status=ContainerStatus.UNKNOWN,
                last_check=datetime.now()
            )
        except DockerException as e:
            logger.error(f"检查容器 {container_id} 状态失败: {e}")
            return MCPServerStatus(
                status=ContainerStatus.ERROR,
                last_check=datetime.now()
            )

    def get_resource_usage(self, container_id: str) -> Optional[ResourceUsage]:
        """
        获取容器的资源使用情况

        :param container_id: 容器 ID 或名称
        :return: ResourceUsage 对象或 None
        """
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)
            
            # CPU 使用率计算
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_cpu_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            cpu_usage = (cpu_delta / system_cpu_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100 if system_cpu_delta > 0 else 0.0
            
            # 内存使用量
            memory_usage = stats['memory_stats']['usage']
            
            # 网络统计
            network_rx = 0
            network_tx = 0
            if 'networks' in stats:
                for interface in stats['networks'].values():
                    network_rx += interface['rx_bytes']
                    network_tx += interface['tx_bytes']
            
            # 块设备统计
            block_read = 0
            block_write = 0
            if 'blkio_stats' in stats and 'io_service_bytes_recursive' in stats['blkio_stats']:
                for item in stats['blkio_stats']['io_service_bytes_recursive']:
                    if item['op'] == 'Read':
                        block_read += item['value']
                    elif item['op'] == 'Write':
                        block_write += item['value']
            
            # 进程数
            pids = stats.get('pids_stats', {}).get('current', 0)
            
            return ResourceUsage(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                network_rx=network_rx,
                network_tx=network_tx,
                block_read=block_read,
                block_write=block_write,
                pids=pids
            )
        except NotFound:
            logger.warning(f"获取资源使用情况时找不到容器: {container_id}")
            return None
        except DockerException as e:
            logger.error(f"获取容器 {container_id} 资源使用情况失败: {e}")
            return None

    def health_check(self, container_id: str) -> bool:
        """
        执行容器的健康检查

        :param container_id: 容器 ID 或名称
        :return: 如果健康检查通过则返回 True
        """
        try:
            container = self.client.containers.get(container_id)
            container.reload()
            health_status = self._get_health_status(container)
            if health_status is not None:
                return health_status == "healthy"
            # 无健康检查字段时，只要容器在运行则视为健康
            return getattr(container, "status", None) == "running"
        except (NotFound, DockerException):
            return False

    def monitor_all_containers(self, registry: ServerRegistry) -> Dict[str, MCPServerStatus]:
        """
        监控所有注册的容器

        :param registry: ServerRegistry 对象
        :return: 容器名称到 MCPServerStatus 的映射
        """
        status_map = {}
        for name, server_data in registry.servers.items():
            if server_data.container_info and server_data.container_info.container_id:
                status = self.check_container_status(server_data.container_info.container_id)
                status_map[name] = status
        return status_map

    def get_running_containers(self) -> List[str]:
        """
        获取所有正在运行的容器 ID 列表

        :return: 容器 ID 列表
        """
        try:
            containers = self.client.containers.list(filters={"status": "running"})
            return [container.id for container in containers]
        except DockerException as e:
            logger.error(f"获取运行中的容器列表失败: {e}")
            return []

    def _map_docker_status(self, docker_status: str) -> ContainerStatus:
        """
        将 Docker 状态映射到 ContainerStatus 枚举

        :param docker_status: Docker 容器状态字符串
        :return: ContainerStatus 枚举成员
        """
        return ContainerStatus.from_docker_status(docker_status)

    def _get_health_status(self, container) -> Optional[str]:
        """
        获取容器的健康状态

        :param container: Docker 容器对象
        :return: 健康状态字符串或 None
        """
        try:
            if 'Health' in container.attrs['State']:
                return container.attrs['State']['Health']['Status']
        except (KeyError, TypeError):
            pass
        return None
