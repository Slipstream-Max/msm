"""
测试 ResourceUsage 模型的 YAML 序列化和反序列化功能以及验证逻辑
"""

import pytest
from msm.data.models import ResourceUsage


class TestResourceUsageYAML:
    """测试 ResourceUsage 的 YAML 方法"""

    def test_resourceusage_yaml(self):
        """测试 ResourceUsage 的 YAML 方法"""
        usage = ResourceUsage(
            cpu_usage=25.5,
            memory_usage=104857600,  # 100MB
            network_rx=1024000,
            network_tx=512000,
            block_read=2048000,
            block_write=1024000,
            pids=5,
        )

        yaml_str = usage.to_yaml()
        assert isinstance(yaml_str, str)
        assert "cpu_usage: 25.5" in yaml_str

        restored = ResourceUsage.from_yaml(yaml_str)
        assert restored.cpu_usage == usage.cpu_usage
        assert restored.memory_usage == usage.memory_usage

    def test_resourceusage_yaml_with_none_values(self):
        """测试 ResourceUsage YAML 处理 None 值"""
        usage = ResourceUsage()

        yaml_str = usage.to_yaml()
        assert isinstance(yaml_str, str)

        restored = ResourceUsage.from_yaml(yaml_str)
        assert restored.cpu_usage is None
        assert restored.memory_usage is None
        assert restored.network_rx is None
        assert restored.network_tx is None
        assert restored.block_read is None
        assert restored.block_write is None
        assert restored.pids is None

    def test_resourceusage_yaml_error_handling(self):
        """测试 ResourceUsage YAML 错误处理"""
        with pytest.raises(Exception):
            ResourceUsage.from_yaml("invalid: yaml: content: [")

        with pytest.raises(Exception):
            ResourceUsage.from_yaml("")


class TestResourceUsageValidation:
    """测试 ResourceUsage 的验证逻辑"""

    def test_resource_usage_negative_cpu(self):
        """测试资源使用负 CPU 使用率"""
        with pytest.raises(ValueError):
            ResourceUsage(cpu_usage=-5.0)

    def test_resource_usage_cpu_over_100(self):
        """测试资源使用 CPU 使用率超过100"""
        with pytest.raises(ValueError):
            ResourceUsage(cpu_usage=150.0)

    def test_resource_usage_negative_memory(self):
        """测试资源使用负内存使用量"""
        with pytest.raises(ValueError):
            ResourceUsage(memory_usage=-1024)

    def test_resource_usage_negative_network_rx(self):
        """测试资源使用负网络接收"""
        with pytest.raises(ValueError):
            ResourceUsage(network_rx=-1000)

    def test_resource_usage_negative_network_tx(self):
        """测试资源使用负网络发送"""
        with pytest.raises(ValueError):
            ResourceUsage(network_tx=-500)

    def test_resource_usage_negative_block_read(self):
        """测试资源使用负磁盘读取"""
        with pytest.raises(ValueError):
            ResourceUsage(block_read=-2048)

    def test_resource_usage_negative_block_write(self):
        """测试资源使用负磁盘写入"""
        with pytest.raises(ValueError):
            ResourceUsage(block_write=-1024)

    def test_resource_usage_negative_pids(self):
        """测试资源使用负进程数"""
        with pytest.raises(ValueError):
            ResourceUsage(pids=-1)
