#!/usr/bin/env python3
"""
演示 ServerRegistry 的 CRUD 操作

这个脚本展示了如何使用 ServerRegistry 进行服务器的增删改查操作。
"""

from pathlib import Path

from msm.data.models import (
    MCPServerConfig,
    MCPServerStatus,
    ServerRegistry,
    ServerStatus,
    ContainerInfo,
    ResourceUsage,
)


def demo_create_servers():
    """演示创建服务器配置"""
    print("=== 创建服务器配置 ===")

    # 创建注册表
    registry = ServerRegistry(version="2.0.0")
    print(f"创建注册表，版本: {registry.version}")

    # 创建第一个服务器配置
    nginx_config = MCPServerConfig(
        name="nginx-server",
        docker_command="docker run -d -p 8080:80 nginx:latest",
        host="localhost",
        port=8080,
        description="Nginx Web 服务器",
        auto_start=True,
    )

    # 创建第二个服务器配置
    mysql_config = MCPServerConfig(
        name="mysql-server",
        docker_command="docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=secret mysql:8.0",
        host="localhost",
        port=3306,
        description="MySQL 数据库服务器",
        auto_start=True,
        environment={"MYSQL_ROOT_PASSWORD": "secret"},
    )

    # 创建第三个服务器配置
    redis_config = MCPServerConfig(
        name="redis-server",
        docker_command="docker run -d -p 6379:6379 redis:alpine",
        host="localhost",
        port=6379,
        description="Redis 缓存服务器",
        auto_start=False,
    )

    # 添加服务器到注册表
    print("\n添加服务器到注册表:")
    print(f"添加 nginx-server: {registry.add_server(nginx_config)}")
    print(f"添加 mysql-server: {registry.add_server(mysql_config)}")
    print(f"添加 redis-server: {registry.add_server(redis_config)}")

    # 尝试添加重复的服务器
    print(f"尝试添加重复的 nginx-server: {registry.add_server(nginx_config)}")

    return registry


def demo_read_servers(registry):
    """演示读取服务器信息"""
    print("\n=== 读取服务器信息 ===")

    # 获取服务器数量
    print(f"注册表中的服务器数量: {registry.get_server_count()}")

    # 列出所有服务器
    print("\n所有服务器列表:")
    servers = registry.list_servers()
    for server in servers:
        print(f"  - {server.name}: {server.config.description}")

    # 获取特定服务器
    print("\n获取特定服务器:")
    nginx_server = registry.get_server("nginx-server")
    if nginx_server:
        print(f"nginx-server 配置: {nginx_server.config.docker_command}")

    # 检查服务器是否存在
    print("\n检查服务器是否存在:")
    print(f"nginx-server 存在: {registry.server_exists('nginx-server')}")
    print(f"unknown-server 存在: {registry.server_exists('unknown-server')}")


def demo_update_servers(registry):
    """演示更新服务器配置和状态"""
    print("\n=== 更新服务器配置和状态 ===")

    # 更新服务器配置
    print("更新 nginx-server 配置:")
    new_nginx_config = MCPServerConfig(
        name="nginx-server",
        docker_command="docker run -d -p 8080:80 --name nginx-prod nginx:stable",
        host="localhost",
        port=8080,
        description="生产环境 Nginx 服务器",
        auto_start=True,
    )

    success = registry.update_server_config("nginx-server", new_nginx_config)
    print(f"更新配置成功: {success}")

    # 更新服务器状态
    print("\n更新服务器状态:")
    running_status = MCPServerStatus(
        status=ServerStatus.RUNNING,
        resource_usage=ResourceUsage(
            cpu_usage=15.5,
            memory_usage=52428800,  # 50MB
        ),
        uptime="2h 30m",
        health_status="healthy",
    )

    success = registry.update_server_status("nginx-server", running_status)
    print(f"更新状态成功: {success}")

    # 更新容器信息
    print("\n更新容器信息:")
    nginx_server = registry.get_server("nginx-server")
    if nginx_server:
        container_info = ContainerInfo(
            container_id="abc123def456",
            container_name="nginx-prod",
            image="nginx:stable",
        )
        nginx_server.update_container_info(container_info)

    # 验证更新结果
    updated_server = registry.get_server("nginx-server")
    if updated_server:
        print(f"更新后的描述: {updated_server.config.description}")
        print(f"更新后的状态: {updated_server.status.status}")
        print(f"容器ID: {updated_server.get_container_id()}")


def demo_delete_servers(registry):
    """演示删除服务器"""
    print("\n=== 删除服务器 ===")

    # 删除存在的服务器
    print("删除 mysql-server:")
    success = registry.remove_server("mysql-server")
    print(f"删除成功: {success}")
    print(f"剩余服务器数量: {registry.get_server_count()}")

    # 尝试删除不存在的服务器
    print("\n尝试删除不存在的服务器:")
    success = registry.remove_server("non-existent-server")
    print(f"删除成功: {success}")


def demo_query_operations(registry):
    """演示查询操作"""
    print("\n=== 查询操作 ===")

    # 获取运行中的服务器
    print("运行中的服务器:")
    running_servers = registry.get_running_servers()
    for server in running_servers:
        print(f"  - {server.name}: {server.status.status}")

    # 显示所有服务器的详细信息
    print("\n所有服务器详细信息:")
    for server in registry.list_servers():
        print(f"\n服务器: {server.name}")
        print(f"  描述: {server.config.description}")
        print(f"  Docker命令: {server.config.docker_command}")
        print(f"  状态: {server.status.status}")
        print(f"  自动启动: {server.config.auto_start}")
        if server.status.container_info and server.status.container_info.container_id:
            print(f"  容器ID: {server.status.container_info.container_id}")


def demo_persistence(registry):
    """演示数据持久化"""
    print("\n=== 数据持久化 ===")

    # 保存到 YAML 文件
    output_file = Path("examples/demo_output/demo_server_registry.yaml")
    output_file.parent.mkdir(exist_ok=True)

    yaml_content = registry.to_yaml()
    output_file.write_text(yaml_content, encoding='utf-8')
    print(f"注册表已保存到: {output_file}")

    # 从 YAML 文件加载
    print("\n从文件重新加载注册表:")
    loaded_yaml = output_file.read_text(encoding='utf-8')
    loaded_registry = ServerRegistry.from_yaml(loaded_yaml)

    print(f"加载的注册表版本: {loaded_registry.version}")
    print(f"加载的服务器数量: {loaded_registry.get_server_count()}")

    # 验证数据完整性
    print("\n验证数据完整性:")
    for server in loaded_registry.list_servers():
        print(f"  - {server.name}: {server.config.description}")


def main():
    """主函数"""
    print("MCP Server Registry CRUD 操作演示")
    print("=" * 50)

    # 创建和添加服务器
    registry = demo_create_servers()

    # 读取服务器信息
    demo_read_servers(registry)

    # 更新服务器
    demo_update_servers(registry)

    # 删除服务器
    demo_delete_servers(registry)

    # 查询操作
    demo_query_operations(registry)

    # 数据持久化
    demo_persistence(registry)

    print("\n" + "=" * 50)
    print("演示完成！")


if __name__ == "__main__":
    main()
