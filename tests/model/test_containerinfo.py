"""
测试 ContainerInfo 模型的 YAML 序列化和反序列化功能
"""

import pytest
from msm.data.models import ContainerInfo


class TestContainerInfoYAML:
    """测试 ContainerInfo 的 YAML 方法"""

    def test_containerinfo_yaml(self):
        """测试 ContainerInfo 的 YAML 方法"""
        container_info = ContainerInfo(
            container_id="abc123",
            container_name="test-container",
            image="nginx:latest",
            image_id="sha256:123",
            ports={"80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}]},
            mounts=[
                {
                    "Type": "bind",
                    "Source": "/host/path",
                    "Destination": "/container/path",
                }
            ],
        )

        yaml_str = container_info.to_yaml()
        assert isinstance(yaml_str, str)
        assert "container_id: abc123" in yaml_str

        restored = ContainerInfo.from_yaml(yaml_str)
        assert restored.container_id == container_info.container_id
        assert restored.ports == container_info.ports

    def test_containerinfo_yaml_with_none_values(self):
        """测试 ContainerInfo YAML 处理 None 值"""
        container_info = ContainerInfo()

        yaml_str = container_info.to_yaml()
        assert isinstance(yaml_str, str)

        restored = ContainerInfo.from_yaml(yaml_str)
        assert restored.container_id is None
        assert restored.container_name is None
        assert restored.image is None
        assert restored.image_id is None
        assert restored.ports == {}
        assert restored.mounts == []

    def test_containerinfo_yaml_error_handling(self):
        """测试 ContainerInfo YAML 错误处理"""
        with pytest.raises(Exception):
            ContainerInfo.from_yaml("invalid: yaml: content: [")

        with pytest.raises(Exception):
            ContainerInfo.from_yaml("")
