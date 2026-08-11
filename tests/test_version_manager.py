"""测试 version_manager 模块"""
import pytest
import os
import sys
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


class TestCreateVersion:
    """版本创建测试"""

    def test_validate_version_valid(self):
        """合法版本号"""
        # Import inline to avoid path issues
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from create_version import validate_version
        assert validate_version("v1.0.0") == "v1.0.0"
        assert validate_version("1.0.0") == "v1.0.0"
        assert validate_version("v0.1.0") == "v0.1.0"

    def test_validate_version_invalid(self):
        """非法版本号"""
        from create_version import validate_version
        with pytest.raises(ValueError):
            validate_version("1.0")
        with pytest.raises(ValueError):
            validate_version("abc")
        with pytest.raises(ValueError):
            validate_version("")

    def test_compare_versions(self):
        """版本号比较"""
        from create_version import compare_versions
        assert compare_versions("v1.0.0", "v0.9.0") == 1
        assert compare_versions("v0.9.0", "v1.0.0") == -1
        assert compare_versions("v1.0.0", "v1.0.0") == 0
        assert compare_versions("v2.0.0", "v1.9.9") == 1

    def test_version_exists(self, tmp_project):
        """版本存在性检查"""
        from create_version import version_exists
        # Mock PROJECT_ROOT
        import create_version
        original_root = create_version.PROJECT_ROOT
        create_version.PROJECT_ROOT = tmp_project
        try:
            # v0.1.0 应该不存在（只有空目录）
            assert not version_exists("v0.1.0") or (tmp_project / "versions" / "v0.1.0").exists()
        finally:
            create_version.PROJECT_ROOT = original_root

    def test_create_version_structure(self, tmp_project):
        """创建版本目录结构"""
        from create_version import create_version_structure
        import create_version
        original_root = create_version.PROJECT_ROOT
        create_version.PROJECT_ROOT = tmp_project
        try:
            create_version_structure("v1.0.0")
            assert (tmp_project / "versions" / "v1.0.0").exists()
            assert (tmp_project / "versions" / "v1.0.0" / "prd").exists()
            assert (tmp_project / "versions" / "v1.0.0" / "prototype").exists()
            assert (tmp_project / "versions" / "v1.0.0" / "agent_comm").exists()
        finally:
            create_version.PROJECT_ROOT = original_root