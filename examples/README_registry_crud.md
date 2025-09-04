# ServerRegistry CRUD 示例

这个示例演示了如何使用 `ServerRegistry` 类进行服务器管理的 CRUD 操作。

## 功能演示

### 1. 创建服务器 (Create)
- 创建 `ServerRegistry` 实例
- 创建多个 `MCPServerConfig` 配置
- 将服务器添加到注册表中

### 2. 读取服务器 (Read)
- 获取服务器数量
- 列出所有服务器
- 获取特定服务器信息
- 检查服务器是否存在

### 3. 更新服务器 (Update)
- 更新服务器配置
- 更新服务器状态（运行状态、容器信息、资源使用情况等）

### 4. 删除服务器 (Delete)
- 删除指定服务器
- 处理删除不存在服务器的情况

### 5. 查询操作
- 获取运行中的服务器
- 显示服务器详细信息

### 6. 数据持久化
- 将注册表保存为 YAML 文件
- 从 YAML 文件重新加载注册表
- 验证数据完整性

## 运行示例

```bash
cd /path/to/msm
source .venv/bin/activate
python examples/server_registry_crud.py
```

## 输出文件

运行示例后会在 `examples/demo_output/` 目录下生成：
- `server_registry.yaml` - 注册表的 YAML 序列化数据

## 示例中的服务器

1. **nginx-server**: Nginx Web 服务器
   - 端口: 8080
   - 自动启动: 是
   - 状态: 运行中

2. **mysql-server**: MySQL 数据库服务器
   - 端口: 3306
   - 自动启动: 是
   - 包含环境变量配置

3. **redis-server**: Redis 缓存服务器
   - 端口: 6379
   - 自动启动: 否
   - 状态: 未知

## 主要API方法

- `add_server(config)` - 添加服务器
- `remove_server(name)` - 删除服务器
- `get_server(name)` - 获取服务器
- `list_servers()` - 列出所有服务器
- `update_server_config(name, config)` - 更新配置
- `update_server_status(name, status)` - 更新状态
- `get_running_servers()` - 获取运行中的服务器
- `to_yaml()` / `from_yaml()` - YAML 序列化</content>
<parameter name="filePath">/home/slipstream/projects/msm/examples/README_server_registry.md
