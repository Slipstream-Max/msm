"""
MCP Server管理系统的数据模型定义

这个模块包含了MCP Server配置、状态和相关数据结构的定义。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class MCPServerConfig(BaseModel):
    """MCP Server配置模型"""

    name: str = Field(..., description="MCP Server实例名称", min_length=1)
    docker_command: str = Field(..., description="Docker启动命令", min_length=1)
    host: str = Field(default="localhost", description="目标服务器IP")
    port: Optional[int] = Field(default=None, description="端口号", ge=1, le=65535)
    description: Optional[str] = Field(default=None, description="实例描述")
    environment: Dict[str, str] = Field(default_factory=dict, description="环境变量")
    volumes: List[str] = Field(default_factory=list, description="数据卷映射")
    networks: List[str] = Field(default_factory=list, description="网络配置")
    labels: Dict[str, str] = Field(default_factory=dict, description="容器标签")
    auto_start: bool = Field(default=False, description="是否自动启动")
    restart_policy: str = Field(default="no", description="重启策略")
    health_check: Optional[Dict[str, Any]] = Field(
        default=None, description="健康检查配置"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        """验证名称格式"""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("名称只能包含字母、数字、连字符和下划线")
        return v

    @field_validator("docker_command")
    def validate_docker_command(cls, v: str) -> str:
        """验证Docker命令格式"""
        if not v.strip().startswith("docker"):
            raise ValueError("必须是有效的Docker命令")
        return v.strip()

    def to_yaml(self) -> str:
        """序列化为 YAML 字符串"""
        return yaml.dump(
            self.model_dump(mode="json"), default_flow_style=False, allow_unicode=True
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "MCPServerConfig":
        """从 YAML 字符串反序列化"""
        data = yaml.safe_load(yaml_str)
        return cls(**data)


class ServerStatus(str, Enum):
    """MCP Server运行状态枚举"""

    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"

    def __str__(self) -> str:
        return self.value


class ContainerInfo(BaseModel):
    """容器信息模型"""

    container_id: Optional[str] = Field(default=None, description="容器ID")
    container_name: Optional[str] = Field(default=None, description="容器名称")
    image: Optional[str] = Field(default=None, description="镜像名称")
    image_id: Optional[str] = Field(default=None, description="镜像ID")
    ports: Dict[str, List[Dict[str, str]]] = Field(
        default_factory=dict, description="端口映射"
    )
    mounts: List[Dict[str, Any]] = Field(default_factory=list, description="挂载点")

    def to_yaml(self) -> str:
        """序列化为 YAML 字符串"""
        return yaml.dump(
            self.model_dump(mode="json"), default_flow_style=False, allow_unicode=True
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ContainerInfo":
        """从 YAML 字符串反序列化"""
        data = yaml.safe_load(yaml_str)
        return cls(**data)


class ContainerLogs(BaseModel):
    """容器日志模型"""

    logs: List[str] = Field(default_factory=list, description="容器日志列表")

    def to_yaml(self) -> str:
        """序列化为 YAML 字符串"""
        return yaml.dump(
            self.model_dump(mode="json"), default_flow_style=False, allow_unicode=True
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ContainerLogs":
        """从 YAML 字符串反序列化"""
        data = yaml.safe_load(yaml_str)
        return cls(**data)


class ResourceUsage(BaseModel):
    """资源使用情况模型"""

    cpu_usage: Optional[float] = Field(
        default=None, description="CPU使用百分比", ge=0, le=100
    )
    memory_usage: Optional[int] = Field(
        default=None, description="内存使用量(字节)", ge=0
    )
    network_rx: Optional[int] = Field(default=None, description="网络接收字节数", ge=0)
    network_tx: Optional[int] = Field(default=None, description="网络发送字节数", ge=0)
    block_read: Optional[int] = Field(default=None, description="磁盘读取字节数", ge=0)
    block_write: Optional[int] = Field(default=None, description="磁盘写入字节数", ge=0)
    pids: Optional[int] = Field(default=None, description="进程数", ge=0)

    def to_yaml(self) -> str:
        """序列化为 YAML 字符串"""
        return yaml.dump(
            self.model_dump(mode="json"), default_flow_style=False, allow_unicode=True
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ResourceUsage":
        """从 YAML 字符串反序列化"""
        data = yaml.safe_load(yaml_str)
        return cls(**data)


class MCPServerStatus(BaseModel):
    """MCP Server状态模型"""

    status: ServerStatus = Field(..., description="运行状态")
    container_logs: Optional[ContainerLogs] = Field(
        default=None, description="容器日志"
    )
    resource_usage: Optional[ResourceUsage] = Field(
        default=None, description="资源使用情况"
    )
    uptime: Optional[str] = Field(default=None, description="运行时长")
    health_status: Optional[str] = Field(default=None, description="健康状态")
    last_check: datetime = Field(
        default_factory=datetime.now, description="最后检查时间"
    )

    def is_running(self) -> bool:
        """判断是否正在运行"""
        return self.status == ServerStatus.RUNNING

    def is_healthy(self) -> bool:
        """判断是否健康"""
        return self.status == ServerStatus.RUNNING and self.health_status in [
            None,
            "healthy",
        ]

    def update_check_time(self) -> None:
        """更新检查时间"""
        self.last_check = datetime.now()

    def to_yaml(self) -> str:
        """序列化为 YAML 字符串"""
        return yaml.dump(
            self.model_dump(mode="json"), default_flow_style=False, allow_unicode=True
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "MCPServerStatus":
        """从 YAML 字符串反序列化"""
        data = yaml.safe_load(yaml_str)
        return cls(**data)


class MCPServerData(BaseModel):
    """MCP Server完整数据模型"""

    config: MCPServerConfig = Field(..., description="配置信息")
    status: MCPServerStatus = Field(..., description="状态信息")
    container_info: Optional[ContainerInfo] = Field(
        default=None, description="容器信息"
    )

    @property
    def name(self) -> str:
        """获取实例名称"""
        return self.config.name

    def update_status(self, new_status: MCPServerStatus) -> None:
        """更新状态信息"""
        self.status = new_status

    def update_config(self, new_config: MCPServerConfig) -> None:
        """更新配置信息"""
        self.config = new_config

    def update_container_info(self, container_info: Optional[ContainerInfo]) -> None:
        """更新容器信息"""
        self.container_info = container_info

    def get_container_id(self) -> Optional[str]:
        """获取容器ID"""
        return self.container_info.container_id if self.container_info else None

    def to_yaml(self) -> str:
        """序列化为 YAML 字符串"""
        return yaml.dump(
            self.model_dump(mode="json"), default_flow_style=False, allow_unicode=True
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "MCPServerData":
        """从 YAML 字符串反序列化"""
        data = yaml.safe_load(yaml_str)
        return cls(**data)


class ServerRegistry(BaseModel):
    """MCP Server注册表模型"""

    servers: Dict[str, MCPServerData] = Field(
        default_factory=dict, description="服务器实例映射"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="最后更新时间"
    )
    version: str = Field(default="1.0.0", description="注册表版本")

    def add_server(self, config: MCPServerConfig) -> bool:
        """添加服务器配置"""
        if config.name in self.servers:
            return False

        status = MCPServerStatus(status=ServerStatus.UNKNOWN)
        self.servers[config.name] = MCPServerData(config=config, status=status)
        self.last_updated = datetime.now()
        return True

    def remove_server(self, name: str) -> bool:
        """移除服务器配置"""
        if name not in self.servers:
            return False

        del self.servers[name]
        self.last_updated = datetime.now()
        return True

    def get_server(self, name: str) -> Optional[MCPServerData]:
        """获取服务器数据"""
        return self.servers.get(name)

    def list_servers(self) -> List[MCPServerData]:
        """列出所有服务器"""
        return list(self.servers.values())

    def update_server_status(self, name: str, status: MCPServerStatus) -> bool:
        """更新服务器状态"""
        if name not in self.servers:
            return False

        self.servers[name].update_status(status)
        self.last_updated = datetime.now()
        return True

    def update_server_config(self, name: str, config: MCPServerConfig) -> bool:
        """更新服务器配置"""
        if name not in self.servers:
            return False

        self.servers[name].update_config(config)
        self.last_updated = datetime.now()
        return True

    def server_exists(self, name: str) -> bool:
        """检查服务器是否存在"""
        return name in self.servers

    def get_running_servers(self) -> List[MCPServerData]:
        """获取所有运行中的服务器"""
        return [
            server
            for server in self.servers.values()
            if server.status.status == ServerStatus.RUNNING
        ]

    def get_server_count(self) -> int:
        """获取服务器总数"""
        return len(self.servers)

    def to_yaml(self) -> str:
        """序列化为 YAML 字符串"""
        return yaml.dump(
            self.model_dump(mode="json"), default_flow_style=False, allow_unicode=True
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ServerRegistry":
        """从 YAML 字符串反序列化"""
        data = yaml.safe_load(yaml_str)
        return cls(**data)
