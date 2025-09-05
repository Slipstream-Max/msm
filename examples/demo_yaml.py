#!/usr/bin/env python3
"""
演示 MCP Server 数据模型的 YAML 序列化功能

这个脚本展示了如何使用数据模型创建配置，并将其序列化为 YAML 格式。
"""
from pathlib import Path

from msm.data.models import (
    ContainerInfo,
    ContainerLogs,
    MCPServerConfig,
    MCPServerStatus,
    MCPServerData,
    ResourceUsage,
    ServerRegistry,
    ContainerStatus,
)


def demo_server_config():
    """演示服务器配置的 YAML 序列化"""
    print("=== 服务器配置示例 ===")

    config = MCPServerConfig(
        name="demo-nginx-server",
        docker_command="docker run -d -p 8080:80 --name demo-nginx nginx:latest",
        host="localhost",
        port=8080,
        description="演示用的 Nginx 服务器",
        environment={
            "ENV": "production",
            "NGINX_WORKER_PROCESSES": "4"
        },
        volumes=[
            "/host/logs:/var/log/nginx",
            "/host/config:/etc/nginx/conf.d"
        ],
        networks=["bridge", "app-network"],
        labels={
            "app": "web-server",
            "version": "1.0",
            "managed-by": "msm"
        },
        auto_start=True,
        restart_policy="always",
        health_check={
            "test": ["CMD", "curl", "-f", "http://localhost/health"],
            "interval": 30000000000,  # 30秒
            "timeout": 10000000000,   # 10秒
            "retries": 3
        }
    )

    yaml_content = config.to_yaml()
    print(yaml_content)

    # 保存到文件
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    config_file = output_dir / "server_config.yaml"
    config_file.write_text(yaml_content, encoding='utf-8')
    print(f"配置文件已保存到: {config_file.absolute()}\n")


def demo_container_info():
    """演示容器信息的 YAML 序列化"""
    print("=== 容器信息示例 ===")

    container_info = ContainerInfo(
        container_id="abc123def456",
        container_name="demo-nginx-server",
        image="nginx:latest",
        image_id="sha256:abcdef123456",
        ports={
            "80/tcp": [
                {"HostIp": "0.0.0.0", "HostPort": "8080"},
                {"HostIp": "::", "HostPort": "8080"}
            ]
        },
        mounts=[
            {
                "Type": "bind",
                "Source": "/host/logs",
                "Destination": "/var/log/nginx",
                "Mode": "rw"
            },
            {
                "Type": "volume",
                "Name": "nginx-config",
                "Destination": "/etc/nginx/conf.d",
                "Mode": "ro"
            }
        ]
    )

    yaml_content = container_info.to_yaml()
    print(yaml_content)

    # 保存到文件
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    info_file = output_dir / "container_info.yaml"
    info_file.write_text(yaml_content, encoding='utf-8')
    print(f"容器信息已保存到: {info_file.absolute()}\n")


def demo_container_logs():
    """演示容器日志的 YAML 序列化"""
    print("=== 容器日志示例 ===")

    logs = ContainerLogs(
        logs=[
            "2025-09-03 10:00:00 INFO [main] Starting nginx 1.25.3",
            "2025-09-03 10:00:01 INFO [main] Listening on port 80",
            "2025-09-03 10:00:02 INFO [worker-1] Worker process started",
            "2025-09-03 10:00:03 INFO [worker-2] Worker process started",
            "2025-09-03 10:00:05 INFO [health-check] Health check passed",
            "2025-09-03 10:01:00 INFO [access] 192.168.1.100 - GET / HTTP/1.1 200",
            "2025-09-03 10:01:05 INFO [access] 192.168.1.101 - GET /api/status HTTP/1.1 200"
        ]
    )

    yaml_content = logs.to_yaml()
    print(yaml_content)

    # 保存到文件
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    logs_file = output_dir / "container_logs.yaml"
    logs_file.write_text(yaml_content, encoding='utf-8')
    print(f"容器日志已保存到: {logs_file.absolute()}\n")


def demo_resource_usage():
    """演示资源使用情况的 YAML 序列化"""
    print("=== 资源使用情况示例 ===")

    usage = ResourceUsage(
        cpu_usage=15.7,  # CPU 使用率 15.7%
        memory_usage=134217728,  # 内存使用 128MB
        network_rx=5242880,  # 网络接收 5MB
        network_tx=2097152,  # 网络发送 2MB
        block_read=10485760,  # 磁盘读取 10MB
        block_write=5242880,  # 磁盘写入 5MB
        pids=8  # 进程数
    )

    yaml_content = usage.to_yaml()
    print(yaml_content)

    # 保存到文件
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    usage_file = output_dir / "resource_usage.yaml"
    usage_file.write_text(yaml_content, encoding='utf-8')
    print(f"资源使用情况已保存到: {usage_file.absolute()}\n")


def demo_server_status():
    """演示服务器状态的 YAML 序列化"""
    print("=== 服务器状态示例 ===")

    status = MCPServerStatus(
        status=ContainerStatus.RUNNING,
        container_logs=ContainerLogs(logs=["INFO: Server started", "INFO: Listening on port 80"]),
        resource_usage=ResourceUsage(cpu_usage=12.5, memory_usage=67108864),
        uptime="2h 15m 30s",
        health_status="healthy"
    )

    yaml_content = status.to_yaml()
    print(yaml_content)

    # 保存到文件
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    status_file = output_dir / "server_status.yaml"
    status_file.write_text(yaml_content, encoding='utf-8')
    print(f"服务器状态已保存到: {status_file.absolute()}\n")


def demo_server_data():
    """演示服务器数据的 YAML 序列化"""
    print("=== 服务器数据示例 ===")

    config = MCPServerConfig(
        name="demo-server",
        docker_command="docker run -d -p 8080:80 --name demo-server nginx:latest",
        description="演示用的服务器"
    )

    status = MCPServerStatus(
        status=ContainerStatus.RUNNING,
        uptime="3h 45m",
        health_status="healthy"
    )

    container_info = ContainerInfo(
        container_id="test123",
        container_name="demo-server",
        image="nginx:latest"
    )

    data = MCPServerData(config=config, status=status, container_info=container_info)

    yaml_content = data.to_yaml()
    print(yaml_content)

    # 保存到文件
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    data_file = output_dir / "server_data.yaml"
    data_file.write_text(yaml_content, encoding='utf-8')
    print(f"服务器数据已保存到: {data_file.absolute()}\n")


def demo_server_registry():
    """演示服务器注册表的 YAML 序列化"""
    print("=== 服务器注册表示例 ===")

    registry = ServerRegistry(version="1.0.0")

    # 添加多个服务器
    servers = [
        MCPServerConfig(
            name="web-server",
            docker_command="docker run -d -p 8080:80 nginx",
            description="Web 服务器"
        ),
        MCPServerConfig(
            name="api-server",
            docker_command="docker run -d -p 3000:3000 myapi",
            description="API 服务器"
        ),
        MCPServerConfig(
            name="db-server",
            docker_command="docker run -d -p 5432:5432 postgres",
            description="数据库服务器"
        )
    ]

    for server_config in servers:
        registry.add_server(server_config)

    yaml_content = registry.to_yaml()
    print(yaml_content)

    # 保存到文件
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    registry_file = output_dir / "server_registry.yaml"
    registry_file.write_text(yaml_content, encoding='utf-8')
    print(f"服务器注册表已保存到: {registry_file.absolute()}\n")


def demo_round_trip():
    """演示序列化-反序列化的完整循环"""
    print("=== 序列化-反序列化循环示例 ===")

    # 创建原始配置
    original_config = MCPServerConfig(
        name="round-trip-test",
        docker_command="docker run test",
        port=9000,
        description="测试循环序列化"
    )

    print("原始配置:")
    print(f"  名称: {original_config.name}")
    print(f"  端口: {original_config.port}")
    print(f"  描述: {original_config.description}")

    # 序列化
    yaml_str = original_config.to_yaml()
    print(f"\nYAML 内容:\n{yaml_str}")

    # 反序列化
    restored_config = MCPServerConfig.from_yaml(yaml_str)
    print("反序列化后的配置:")
    print(f"  名称: {restored_config.name}")
    print(f"  端口: {restored_config.port}")
    print(f"  描述: {restored_config.description}")

    # 验证数据完整性
    assert original_config.name == restored_config.name
    assert original_config.docker_command == restored_config.docker_command
    assert original_config.port == restored_config.port
    assert original_config.description == restored_config.description

    print("\n✅ 数据完整性验证通过！")


def main():
    """主函数"""
    print("MCP Server 数据模型 YAML 演示")
    print("=" * 50)

    # 创建输出目录
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)

    try:
        demo_server_config()
        demo_container_info()
        demo_container_logs()
        demo_resource_usage()
        demo_server_status()
        demo_server_data()
        demo_server_registry()
        demo_round_trip()

        print("🎉 所有演示完成！")
        print(f"输出文件保存在: {output_dir.absolute()}")

        # 列出生成的文件
        print("\n生成的文件:")
        for file_path in sorted(output_dir.glob("*.yaml")):
            print(f"  - {file_path.name}")

    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
