#!/usr/bin/env python3
"""
演示如何通过命令行使用 ContainerManager

这个脚本提供了一个简单的命令行接口，用于调用 ContainerManager 的核心功能，
例如启动、停止、重启和查看容器状态。

用法:
  python examples/demo_container_manager_cli.py start
  python examples/demo_container_manager_cli.py status
  python examples/demo_container_manager_cli.py logs
  python examples/demo_container_manager_cli.py info
  python examples/demo_container_manager_cli.py stop
  python examples/demo_container_manager_cli.py restart
  python examples/demo_container_manager_cli.py remove
"""

import argparse
import logging
import sys
from pathlib import Path

# 将项目根目录添加到 sys.path，以便能够导入 msm 模块
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from msm.core.container_manager import ContainerManager  # noqa: E402
from msm.data.models import MCPServerConfig  # noqa: E402


# 配置日志记录，以便看到 ContainerManager 的输出
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# 为演示定义一个固定的服务器配置
# 我们将使用一个简单的 nginx 容器
DEMO_SERVER_NAME = "msm-demo-nginx"
DEMO_CONFIG = MCPServerConfig(
    name=DEMO_SERVER_NAME,
    docker_command="docker run -d -p 8888:80 nginx:latest",
    description="一个用于演示的Nginx服务器",
    labels={"manager": "msm-demo"},
)


def handle_start(manager: ContainerManager):
    """处理 start 命令"""
    print(f"🚀 正在尝试启动容器 '{DEMO_CONFIG.name}'...")
    try:
        container_id = manager.start_container(DEMO_CONFIG)
        print(f"✅ 容器已启动，ID: {container_id}")
    except Exception as e:
        print(f"❌ 启动失败: {e}")


def handle_stop(manager: ContainerManager):
    """处理 stop 命令"""
    print(f"🛑 正在尝试停止容器 '{DEMO_SERVER_NAME}'...")
    try:
        if manager.stop_container(DEMO_SERVER_NAME):
            print("✅ 容器已成功停止。")
        else:
            print(f"⚠️ 停止操作完成，但可能容器 '{DEMO_SERVER_NAME}' 本身就不存在。")
    except Exception as e:
        print(f"❌ 停止失败: {e}")


def handle_restart(manager: ContainerManager):
    """处理 restart 命令"""
    print(f"🔄 正在尝试重启容器 '{DEMO_SERVER_NAME}'...")
    try:
        if manager.restart_container(DEMO_SERVER_NAME):
            print("✅ 容器已成功重启。")
        else:
            print(f"⚠️ 重启失败，请检查容器 '{DEMO_SERVER_NAME}' 是否存在。")
    except Exception as e:
        print(f"❌ 重启失败: {e}")


def handle_remove(manager: ContainerManager):
    """处理 remove 命令"""
    print(f"🗑️ 正在尝试移除容器 '{DEMO_SERVER_NAME}'...")
    try:
        if manager.remove_container(DEMO_SERVER_NAME):
            print("✅ 容器已成功移除。")
        else:
            print(f"⚠️ 移除失败，请检查容器 '{DEMO_SERVER_NAME}' 是否存在。")
    except Exception as e:
        print(f"❌ 移除失败: {e}")


def handle_status(manager: ContainerManager):
    """处理 status 命令"""
    print(f"ℹ️ 正在获取容器 '{DEMO_SERVER_NAME}' 的状态...")
    try:
        status = manager.get_container_status(DEMO_SERVER_NAME)
        print(f"  - 状态: {status.value}")
    except Exception as e:
        print(f"❌ 获取状态失败: {e}")


def handle_info(manager: ContainerManager):
    """处理 info 命令"""
    print(f"ℹ️ 正在获取容器 '{DEMO_SERVER_NAME}' 的详细信息...")
    try:
        info = manager.get_container_info(DEMO_SERVER_NAME)
        if info:
            print("  - 容器ID:", info.container_id)
            print("  - 容器名称:", info.container_name)
            print("  - 镜像:", info.image)
            print("  - 端口映射:", info.ports)
        else:
            print(f"  - 找不到容器 '{DEMO_SERVER_NAME}' 的信息。")
    except Exception as e:
        print(f"❌ 获取信息失败: {e}")


def handle_logs(manager: ContainerManager):
    """处理 logs 命令"""
    print(f"📜 正在获取容器 '{DEMO_SERVER_NAME}' 的最新日志...")
    try:
        logs = manager.get_container_logs(DEMO_SERVER_NAME, tail=20)
        print("--- 日志开始 ---")
        for line in logs.logs:
            print(line)
        print("--- 日志结束 ---")
    except Exception as e:
        print(f"❌ 获取日志失败: {e}")


def main():
    """主函数，解析命令行参数并执行相应操作"""
    parser = argparse.ArgumentParser(
        description="ContainerManager 演示命令行工具",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "command",
        choices=["start", "stop", "restart", "remove", "status", "info", "logs"],
        help=(
            "要执行的操作:\n"
            "  start   - 启动一个演示 Nginx 容器\n"
            "  stop    - 停止该容器\n"
            "  restart - 重启该容器\n"
            "  remove  - 移除该容器\n"
            "  status  - 获取容器的运行状态\n"
            "  info    - 获取容器的详细信息\n"
            "  logs    - 查看容器的最新日志"
        ),
    )

    args = parser.parse_args()

    try:
        manager = ContainerManager()
    except ConnectionError as e:
        print(f"❌ 无法连接到 Docker! 请确保 Docker 正在运行。错误: {e}")
        sys.exit(1)

    command_handlers = {
        "start": handle_start,
        "stop": handle_stop,
        "restart": handle_restart,
        "remove": handle_remove,
        "status": handle_status,
        "info": handle_info,
        "logs": handle_logs,
    }

    handler = command_handlers.get(args.command)
    if handler:
        handler(manager)


if __name__ == "__main__":
    main()
