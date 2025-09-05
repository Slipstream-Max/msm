开发一个MCP Server Management命令行工具（CLI），用于集中管理多个服务器上运行的多个 Docker 容器化的 MCP Server 实例。该工具需支持 MCP Server 的生命周期管理（如启动、停止、重启）、状态监控以及日志查看等基本运维操作，旨在提升多实例部署环境下的管理效率与可观测性。

---
系统架构概览
┌────────────────────────────────────────────────────────────────┐
│           MCP Server Manager                                   │
├────────────────────────────────────────────────────────────────┤
│           CLI Interface                                        │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │        命令行解析器                                         │
│  │   - 复用cli代码                                            │ │ 
│  │      路径为：src/msm/entrypoint/cli                        │ │   
│  └────────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────┤
│          Core Management Layer                           
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │           MCP管理器                                                           
│  │   - MCP Server生命周期管理（启动/停止/重启）                                                                    
│  │   - 监控各个MCP Server实例的运行状态                                                                              
│  │   - 根据命令或请求获取和处理日志                                                                                    
│  │   - 管理MCP Server对应的容器拉取命令                                                                              
│  └─────────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────┤
│       Data Layer                                                          
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │          配置文件管理                  
│  │   - 管理容器实例的配置信息（YAML格式）                          
│  │   - 持久化保存运行状态（例如：容器ID、配置）                                   
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

---
各模块说明
1.  命令行接口层（CLI Interface）：
  使用成熟的命令行解析库（如 argparse 或 click）实现命令处理，支持以下核心命令：
```bash
说明
mcp start <name> [--all]
启动指定 MCP Server 容器实例；支持 --all 参数批量启动
mcp stop <name> [--all]
停止指定 MCP Server 容器实例；支持 --all 参数批量停止
mcp restart <name> [--all]
重启指定 MCP Server 容器实例；支持 --all 参数批量重启
mcp get <name>
查看指定容器的配置信息以及当前运行状态及日志
mcp log <name>
查看指定容器的标准输出日志
mcp list
列出已注册的所有 MCP Server 的配置信息及运行状态
mcp add <name> --command "<docker_command>" [--host <ip>]
注册一个新的 MCP Server 容器实例 <docker_ip> 可指定执行该容器的服务器ip地址
mcp remove <name>
取消注册指定的 MCP Server 容器实例
```
- 服务化管理：在后续版本中，将该管理工具转化为FastAPI服务，接收远程报文请求来管理MCP Server实例。
2. 核心管理层（Core Management Layer）：
  - MCP管理器：负责管理MCP Server实例的生命周期，包括启动、停止、重启操作。
  - 状态监控：通过与Docker API的交互，获取容器的实时状态，并提供健康检查机制（例如：容器是否正常运行，资源使用情况等）。
  - 日志管理：可以获取容器运行的实时日志，便于调试和监控。
  - 实例信息管理：管理容器实例的基本信息（如容器ID、状态、运行时配置）。
3. 数据层（Data Layer）：
  - 配置文件管理：支持使用YAML格式保存和读取容器的配置文件。这些配置文件可以包括容器的启动参数、网络配置、端口映射等。
  - 运行状态持久化：可以持久化保存容器的运行状态信息，便于重启或恢复时自动加载这些状态。
## 依赖选择：
```toml
dependencies = [
    "fastapi>=0.116.1",
    "python-dotenv>=1.1.1",
    "prompt-toolkit>=3.0.52",
    "httpx>=0.28.1",
    "paramiko>=4.0.0",
    "rich>=14.1.0",
    "pyyaml>=6.0.2",
    "docker>=7.1.0",
]
```
## 数据模型设计
```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum

class ServerStatus(str, Enum):
    """MCP Server运行状态枚举"""

    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"

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

class ContainerLogs(BaseModel):
    """容器日志模型"""

    logs: List[str] = Field(default_factory=list, description="容器日志列表")

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

class MCPServerStatus(BaseModel):
    """MCP Server状态模型"""

    status: ServerStatus = Field(..., description="运行状态")
    container_info: Optional[ContainerInfo] = Field(
        default=None, description="容器信息"
    )
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

class MCPServerData(BaseModel):
    """MCP Server完整数据模型"""

    config: MCPServerConfig = Field(..., description="配置信息")
    status: MCPServerStatus = Field(..., description="状态信息")

class ServerRegistry(BaseModel):
    """MCP Server注册表模型"""

    servers: Dict[str, MCPServerData] = Field(
        default_factory=dict, description="服务器实例映射"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="最后更新时间"
    )
    version: str = Field(default="1.0.0", description="注册表版本")
```

## 结构设计
```yaml
msm
    -core：承担拉起容器，检查状态，远程连接的核心功能
    -data：mcp server数据存储管理
    -entrypoint
        -cli：前端解析命令
        -server：后端处理命令
```

---

## 开发进度

### ✅ 已完成
- [x] 数据层模型设计 (Data Layer)
  - [x] MCPServerConfig - MCP Server配置模型
  - [x] ServerStatus - 运行状态枚举
  - [x] ContainerInfo - 容器信息模型
  - [x] ContainerLogs - 容器日志模型
  - [x] ResourceUsage - 资源使用情况模型
  - [x] MCPServerStatus - MCP Server状态模型
  - [x] MCPServerData - MCP Server完整数据模型
  - [x] ServerRegistry - MCP Server注册表模型

### 🚧 进行中

### 📋 待完成

#### Core层开发计划

##### 第一阶段（基础功能）
- [ ] **步骤1: Docker容器管理器** (`src/msm/core/container_manager.py`)
  ```python
  class ContainerManager:
      # 基础容器操作
      def start_container(self, config: MCPServerConfig) -> bool
      def stop_container(self, container_id: str) -> bool
      def restart_container(self, container_id: str) -> bool
      def remove_container(self, container_id: str) -> bool
      
      # 容器信息获取
      def get_container_info(self, container_id: str) -> Optional[ContainerInfo]
      def get_container_logs(self, container_id: str) -> ContainerLogs
      def get_container_status(self, container_id: str) -> ServerStatus
  ```

- [ ] **步骤2: 状态监控器** (`src/msm/core/status_monitor.py`)
  ```python
  class StatusMonitor:
      # 状态检查
      def check_container_status(self, container_id: str) -> MCPServerStatus
      def get_resource_usage(self, container_id: str) -> ResourceUsage
      def health_check(self, container_id: str) -> bool
      
      # 批量监控
      def monitor_all_containers(self, registry: ServerRegistry) -> Dict[str, MCPServerStatus]
      def get_running_containers(self) -> List[str]
  ```

- [ ] **步骤3: 配置管理器** (`src/msm/core/config_manager.py`)
  ```python
  class ConfigManager:
      # 配置文件操作
      def load_registry_from_file(self, file_path: str) -> ServerRegistry
      def save_registry_to_file(self, registry: ServerRegistry, file_path: str) -> bool
      def backup_registry(self, registry: ServerRegistry) -> str
      
      # 配置验证
      def validate_config(self, config: MCPServerConfig) -> bool
      def validate_docker_command(self, command: str) -> bool
  ```

##### 第二阶段（核心整合）
- [ ] **步骤4: MCP服务器管理器** (`src/msm/core/mcp_manager.py`)
  ```python
  class MCPServerManager:
      def __init__(self):
          self.container_manager = DockerContainerManager()
          self.status_monitor = StatusMonitor()
          self.remote_manager = RemoteManager()
          self.registry = ServerRegistry()
      
      # 生命周期管理
      def start_server(self, name: str) -> bool
      def stop_server(self, name: str) -> bool
      def restart_server(self, name: str) -> bool
      
      # 批量操作
      def start_all_servers(self) -> Dict[str, bool]
      def stop_all_servers(self) -> Dict[str, bool]
      
      # 信息获取
      def get_server_status(self, name: str) -> Optional[MCPServerStatus]
      def get_server_logs(self, name: str) -> Optional[ContainerLogs]
      def list_all_servers(self) -> List[MCPServerData]
  ```

- [ ] **步骤5: 日志管理器** (`src/msm/core/log_manager.py`)
  ```python
  class LogManager:
      # 日志获取
      def get_container_logs(self, container_id: str, lines: int = 100) -> List[str]
      def stream_container_logs(self, container_id: str) -> Iterator[str]
      def save_logs_to_file(self, container_id: str, file_path: str) -> bool
      
      # 日志过滤和搜索
      def filter_logs(self, logs: List[str], keyword: str) -> List[str]
      def get_error_logs(self, container_id: str) -> List[str]
  ```

##### 第三阶段（高级功能）
- [ ] **步骤6: 远程连接管理器** (`src/msm/core/remote_manager.py`)
  ```python
  class RemoteManager:
      # SSH连接管理
      def connect_to_host(self, host: str, username: str, password: str) -> bool
      def execute_remote_command(self, host: str, command: str) -> str
      def disconnect_from_host(self, host: str) -> None
      
      # 远程Docker操作
      def remote_docker_operation(self, host: str, operation: str, container_id: str) -> bool
  ```

#### CLI层开发计划
- [ ] 命令行解析器实现 (`src/msm/entrypoint/cli/`)
  - [ ] 基础命令结构
  - [ ] start/stop/restart 命令
  - [ ] add/remove/list 命令
  - [ ] get/log 命令
  - [ ] 批量操作支持

#### 服务端开发计划
- [ ] FastAPI服务端实现 (`src/msm/entrypoint/server/`)
  - [ ] REST API接口设计
  - [ ] 请求处理逻辑
  - [ ] 身份验证和授权
  - [ ] API文档生成

#### 测试计划
- [ ] 单元测试
  - [ ] 数据模型测试
  - [ ] Core层各组件测试
  - [ ] CLI命令测试
- [ ] 集成测试
  - [ ] 端到端功能测试
  - [ ] Docker环境测试
  - [ ] 远程连接测试

**建议从 `ContainerManager` 开始实现，因为它是所有功能的基础
