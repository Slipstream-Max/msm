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
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"

class MCPServerConfig(BaseModel):
    name: str = Field(..., description="MCP Server实例名称")
    docker_command: str = Field(..., description="Docker启动命令")
    host: str = Field(default="localhost", description="目标服务器IP")
    port: Optional[int] = Field(default=None, description="端口")
    
class MCPServerStatus(BaseModel):
    name: str
    status: ServerStatus
    container_id: Optional[str] = None
    uptime: Optional[str] = None
    cpu_usage: Optional[float] = None
    gpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    last_check: str
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
