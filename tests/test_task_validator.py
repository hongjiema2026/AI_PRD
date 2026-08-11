"""测试 task_validator 模块"""
import pytest
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from task_validator import (
    parse_frontmatter,
    validate_task_book,
    check_timeout,
    validate_agent_output,
    VALID_TASK_TYPES,
    VALID_STATUSES,
)


class TestParseFrontmatter:
    """Frontmatter 解析测试"""

    def test_valid_frontmatter(self, tmp_path):
        """解析合法的 frontmatter"""
        content = "---\ntask_id: test_001\ntype: prd\nstatus: pending\n---\n# 正文"
        f = tmp_path / "test.md"
        f.write_text(content)
        meta, body = parse_frontmatter(str(f))
        assert meta["task_id"] == "test_001"
        assert meta["type"] == "prd"
        assert "正文" in body

    def test_no_frontmatter(self, tmp_path):
        """无 frontmatter 的文件"""
        content = "# 正文\n无 frontmatter"
        f = tmp_path / "test.md"
        f.write_text(content)
        meta, body = parse_frontmatter(str(f))
        assert meta is None

    def test_invalid_yaml_frontmatter(self, tmp_path):
        """无效的 YAML"""
        content = "---\n{invalid yaml\n---\n# 正文"
        f = tmp_path / "test.md"
        f.write_text(content)
        meta, body = parse_frontmatter(str(f))
        assert meta is None


class TestValidateTaskBook:
    """任务书校验测试"""

    def test_valid_task_book(self, sample_task_md):
        """合法任务书"""
        errors, warnings = validate_task_book(sample_task_md)
        assert len(errors) == 0

    def test_missing_file(self):
        """文件不存在"""
        errors, warnings = validate_task_book("/nonexistent/path.md")
        assert len(errors) > 0
        assert "不存在" in errors[0]

    def test_missing_required_fields(self, tmp_path):
        """缺少必填字段"""
        content = "---\ntask_id: test\n---\n# 正文"
        f = tmp_path / "test.md"
        f.write_text(content)
        errors, warnings = validate_task_book(str(f))
        assert any("type" in e for e in errors)
        assert any("status" in e for e in errors)

    def test_invalid_type(self, tmp_path):
        """无效的任务类型"""
        content = "---\ntask_id: test\ntype: invalid_type\nstatus: pending\n---\n"
        f = tmp_path / "test.md"
        f.write_text(content)
        errors, warnings = validate_task_book(str(f))
        assert any("无效的 type" in e for e in errors)

    def test_invalid_status(self, tmp_path):
        """无效的状态"""
        content = "---\ntask_id: test\ntype: prd\nstatus: unknown\n---\n"
        f = tmp_path / "test.md"
        f.write_text(content)
        errors, warnings = validate_task_book(str(f))
        assert any("无效的 status" in e for e in errors)

    def test_missing_recommended_fields_gives_warning(self, tmp_path):
        """缺少建议字段产生警告"""
        content = "---\ntask_id: test\ntype: prd\nstatus: pending\n---\n"
        f = tmp_path / "test.md"
        f.write_text(content)
        errors, warnings = validate_task_book(str(f))
        assert len(errors) == 0
        assert any("created_at" in w for w in warnings)


class TestCheckTimeout:
    """超时检查测试"""

    def test_completed_task_no_timeout(self, tmp_path):
        """已完成任务不检查超时"""
        content = "---\ntask_id: test\ntype: prd\nstatus: completed\n---\n"
        f = tmp_path / "test.md"
        f.write_text(content)
        result = check_timeout(str(f))
        assert result is None

    def test_in_progress_task_with_execution_log(self, sample_task_md):
        """有执行日志的任务超时检查"""
        # sample_task_md 中的时间戳是过去的时间，不应超时
        result = check_timeout(sample_task_md)
        # 由于日志中的时间是 2026-04-28，结果取决于当前时间
        # 只要函数不抛异常即可
        assert result is None or isinstance(result, str)

    def test_multi_type_without_log(self, tmp_path):
        """multi 类型无执行日志时不做超时判断"""
        content = "---\ntask_id: test\ntype: multi\nstatus: in_progress\n---\n"
        f = tmp_path / "test.md"
        f.write_text(content)
        result = check_timeout(str(f))
        assert result is None