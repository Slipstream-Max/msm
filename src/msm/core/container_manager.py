"""
Docker 容器管理器

这个模块提供了 `ContainerManager` 类，用于管理 Docker 容器的生命周期，
包括启动、停止、重启、移除容器，以及获取容器信息、日志和状态。
"""
import logging
import shlex
from typing import Optional

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container

from msm.data.models import (
    ContainerInfo,
    ContainerLogs,
    ContainerStatus,
    MCPServerConfig,
)

logger = logging.getLogger(__name__)


class ContainerManager:
    """
    Docker 容器管理器
    """

    def __init__(self, docker_host: Optional[str] = None):
        """
        初始化 ContainerManager

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

    def _parse_docker_command(self, config: MCPServerConfig) -> dict:
        """
        一个简化的docker run命令解析器。
        注意：这个解析器功能有限，主要用于演示。
        """
        parts = shlex.split(config.docker_command)
        
        if not parts or parts[0] != "docker" or parts[1] != "run":
            raise ValueError("只支持 'docker run' 命令")

        image_part = parts[-1]
        
        restart_policy: dict = {"Name": config.restart_policy}
        if config.restart_policy == "on-failure":
            restart_policy["MaximumRetryCount"] = 5

        params = {
            "image": image_part,
            "name": config.name,
            "detach": True,  # 总是后台运行
            "environment": config.environment,
            "volumes": config.volumes,
            "labels": config.labels,
            "restart_policy": restart_policy,
        }

        # 简单的端口解析
        ports = {}
        for i, part in enumerate(parts):
            if part in ["-p", "--publish"] and i + 1 < len(parts):
                host_port, container_port = parts[i+1].split(":")
                ports[f"{container_port}/tcp"] = int(host_port)
        if ports:
            params["ports"] = ports

        return params

    def start_container(self, config: MCPServerConfig) -> str:
        """
        根据配置启动一个容器

        :param config: MCPServerConfig 对象
        :return: 容器 ID
        """
        try:
            # 检查同名容器是否已存在
            existing_container: Container = self.client.containers.get(config.name)
            if existing_container:
                if existing_container.status == "running":
                    logger.info(f"容器 '{config.name}' 已在运行中，无需重新启动。")
                    if not existing_container.id:
                        raise DockerException(f"找到已存在的容器 '{config.name}'，但它没有ID。")
                    return existing_container.id
                else:
                    # 容器存在但未运行，启动它
                    logger.info(f"容器 '{config.name}' 存在但未运行，正在启动...")
                    existing_container.start()
                    logger.info(f"成功启动现有容器 '{config.name}'，ID: {existing_container.id}")
                    if not existing_container.id:
                        raise DockerException(f"启动现有容器 '{config.name}' 成功但没有返回ID。")
                    return existing_container.id
        except NotFound:
            # 容器不存在，继续创建
            pass
        except DockerException as e:
            logger.error(f"检查容器 '{config.name}' 时出错: {e}")
            raise

        try:
            run_params = self._parse_docker_command(config)
            logger.info(f"使用以下参数创建新容器 '{config.name}': {run_params}")
            
            # 拉取镜像
            logger.info(f"正在拉取镜像: {run_params['image']}")
            self.client.images.pull(run_params['image'])

            container = self.client.containers.run(**run_params)
            logger.info(f"成功启动新容器 '{config.name}'，ID: {container.id}")
            if not container.id:
                raise DockerException(f"新容器 '{config.name}' 已启动但没有返回ID。")
            return container.id
        except DockerException as e:
            logger.error(f"启动容器 '{config.name}' 失败: {e}")
            raise

    def stop_container(self, container_id: str) -> bool:
        """
        停止一个容器

        :param container_id: 容器 ID 或名称
        :return: 如果成功停止则返回 True
        """
        try:
            container: Container = self.client.containers.get(container_id)
            if container.status == "running":
                logger.info(f"正在停止容器 {container.short_id} ({container.name})")
                container.stop()
                logger.info(f"成功停止容器 {container.short_id}")
            else:
                logger.warning(f"容器 {container.short_id} 未在运行状态，无需停止。")
            return True
        except NotFound:
            logger.error(f"找不到容器: {container_id}")
            return False
        except DockerException as e:
            logger.error(f"停止容器 {container_id} 失败: {e}")
            raise

    def restart_container(self, container_id: str) -> bool:
        """
        重启一个容器

        :param container_id: 容器 ID 或名称
        :return: 如果成功重启则返回 True
        """
        try:
            container: Container = self.client.containers.get(container_id)
            logger.info(f"正在重启容器 {container.short_id} ({container.name})")
            container.restart()
            logger.info(f"成功重启容器 {container.short_id}")
            return True
        except NotFound:
            logger.error(f"找不到容器: {container_id}")
            return False
        except DockerException as e:
            logger.error(f"重启容器 {container_id} 失败: {e}")
            raise

    def remove_container(self, container_id: str) -> bool:
        """
        移除一个容器

        :param container_id: 容器 ID 或名称
        :return: 如果成功移除则返回 True
        """
        try:
            container: Container = self.client.containers.get(container_id)
            logger.info(f"正在移除容器 {container.short_id} ({container.name})")
            container.remove(force=True)  # 强制移除，即使在运行中
            logger.info(f"成功移除容器 {container.short_id}")
            return True
        except NotFound:
            logger.warning(f"尝试移除但找不到容器: {container_id}")
            return True  # 如果容器本就不存在，也视为成功
        except DockerException as e:
            logger.error(f"移除容器 {container_id} 失败: {e}")
            raise

    def get_container_info(self, container_id: str) -> Optional[ContainerInfo]:
        """
        获取容器的详细信息

        :param container_id: 容器 ID 或名称
        :return: ContainerInfo 对象或 None
        """
        try:
            container: Container = self.client.containers.get(container_id)
            container.reload()
            
            image_str = ""
            image_id_str = ""
            if container.image:
                image_str = str(container.image.tags[0]) if container.image.tags else str(container.image.id)
                image_id_str = str(container.image.id)

            info = ContainerInfo(
                container_id=container.id,
                container_name=container.name,
                image=image_str,
                image_id=image_id_str,
                ports=container.ports,
                mounts=container.attrs.get("Mounts", []),
            )
            return info
        except NotFound:
            logger.warning(f"获取信息时找不到容器: {container_id}")
            return None
        except DockerException as e:
            logger.error(f"获取容器 {container_id} 信息失败: {e}")
            raise

    def get_container_logs(self, container_id: str, tail: int = 100) -> ContainerLogs:
        """
        获取容器的日志

        :param container_id: 容器 ID 或名称
        :param tail: 获取日志的最后几行
        :return: ContainerLogs 对象
        """
        try:
            container: Container = self.client.containers.get(container_id)
            logs_bytes = container.logs(tail=tail)
            logs_str = logs_bytes.decode("utf-8", errors="ignore")
            return ContainerLogs(logs=logs_str.strip().split("\n"))
        except NotFound:
            logger.warning(f"获取日志时找不到容器: {container_id}")
            return ContainerLogs(logs=[f"错误：找不到容器 '{container_id}'"])
        except DockerException as e:
            logger.error(f"获取容器 {container_id} 日志失败: {e}")
            raise

    def get_container_status(self, container_id: str) -> ContainerStatus:
        """
        获取容器的状态

        :param container_id: 容器 ID 或名称
        :return: ContainerStatus 枚举成员
        """
        try:
            container: Container = self.client.containers.get(container_id)
            container.reload()
            return ContainerStatus.from_docker_status(container.status)
        except NotFound:
            return ContainerStatus.UNKNOWN
        except DockerException as e:
            logger.error(f"获取容器 {container_id} 状态失败: {e}")
            return ContainerStatus.ERROR
