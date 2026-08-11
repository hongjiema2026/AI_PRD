"""测试配置加载模块"""
import pytest
import yaml
from pathlib import Path
from utils import config as config_module


class TestConfigLoader:
    """配置加载器测试"""

    def test_get_existing_key(self):
        """读取存在的配置项"""
        value = config_module.get("version.current")
        assert value == "v0.1.0"

    def test_get_nested_key(self):
        """读取嵌套配置"""
        value = config_module.get("project.name")
        assert value is not None

    def test_get_missing_key_with_default(self):
        """读取不存在的配置项返回默认值"""
        value = config_module.get("nonexistent.key", "default_val")
        assert value == "default_val"

    def test_get_missing_key_without_default(self):
        """读取不存在的配置项返回 None"""
        value = config_module.get("nonexistent.key")
        assert value is None

    def test_get_max_retry(self):
        """获取最大重试次数"""
        value = config_module.get_max_retry()
        assert isinstance(value, int)
        assert value > 0

    def test_get_task_timeout(self):
        """获取任务超时时间"""
        value = config_module.get_task_timeout_minutes()
        assert isinstance(value, int)
        assert value > 0

    def test_get_crawler_timeout(self):
        """获取爬虫超时时间"""
        value = config_module.get_crawler_timeout_seconds()
        assert isinstance(value, int)
        assert value > 0

    def test_get_max_resource_size(self):
        """获取资源大小限制"""
        value = config_module.get_max_resource_size_mb()
        assert isinstance(value, (int, float))
        assert value > 0

    def test_get_allowed_resource_types(self):
        """获取允许的资源类型"""
        value = config_module.get_allowed_resource_types()
        assert isinstance(value, list)
        assert "css" in value
        assert "js" in value

    def test_get_noise_selectors(self):
        """获取噪声选择器"""
        value = config_module.get_noise_selectors()
        assert isinstance(value, list)
        assert len(value) > 0

    def test_get_current_version(self):
        """获取当前版本号"""
        value = config_module.get_current_version()
        assert value.startswith("v")

    def test_get_project_root(self):
        """获取项目根目录"""
        value = config_module.get_project_root()
        assert isinstance(value, Path)
        assert value.exists()

    def test_reload_config(self):
        """重新加载配置"""
        config_module.reload_config()
        value = config_module.get("version.current")
        assert value is not None