"""测试 verifier 模块"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "restore_pipeline"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "utils"))


class TestRestoreVerifier:
    """复原质量验证器测试"""

    def _create_restored_files(self, restored_dir, html_content):
        """辅助：创建复原文件"""
        restored_dir.mkdir(parents=True, exist_ok=True)
        (restored_dir / "index.html").write_text(html_content, encoding="utf-8")
        assets = restored_dir / "assets"
        for sub in ["css", "js", "images", "fonts"]:
            (assets / sub).mkdir(parents=True, exist_ok=True)
            (assets / sub / "dummy.txt").write_text("dummy")

    def test_check_dom_identical(self, tmp_path):
        """DOM 结构完全一致"""
        from verifier import RestoreVerifier

        html = "<html><body><div><p>hello</p></div></body></html>"
        restored_dir = tmp_path / "restored"
        self._create_restored_files(restored_dir, html)

        verifier = RestoreVerifier(
            original_url="https://example.com",
            restored_dir=str(restored_dir),
            check_points=[],
        )

        from bs4 import BeautifulSoup
        soup1 = BeautifulSoup(html, "html.parser")
        soup2 = BeautifulSoup(html, "html.parser")
        score = verifier._check_dom_structure(soup1, soup2)
        assert score == 100.0

    def test_check_dom_different(self, tmp_path):
        """DOM 结构差异"""
        from verifier import RestoreVerifier

        html1 = "<html><body><div><p>a</p><p>b</p></div></body></html>"
        html2 = "<html><body><div><p>a</p></div></body></html>"
        restored_dir = tmp_path / "restored"
        self._create_restored_files(restored_dir, html2)

        verifier = RestoreVerifier(
            original_url="https://example.com",
            restored_dir=str(restored_dir),
            check_points=[],
        )

        from bs4 import BeautifulSoup
        soup1 = BeautifulSoup(html1, "html.parser")
        soup2 = BeautifulSoup(html2, "html.parser")
        score = verifier._check_dom_structure(soup1, soup2)
        assert 0 <= score <= 100

    def test_check_styles_matching(self, tmp_path):
        """样式匹配"""
        from verifier import RestoreVerifier

        css = "<style>body { color: #333; font-family: Arial; font-size: 14px; }</style>"
        html1 = f"<html><body>{css}<p>hello</p></body></html>"
        html2 = f"<html><body>{css}<p>hello</p></body></html>"

        restored_dir = tmp_path / "restored"
        self._create_restored_files(restored_dir, html2)

        verifier = RestoreVerifier(
            original_url="https://example.com",
            restored_dir=str(restored_dir),
            check_points=[],
        )

        from bs4 import BeautifulSoup
        soup1 = BeautifulSoup(html1, "html.parser")
        soup2 = BeautifulSoup(html2, "html.parser")
        score = verifier._check_styles(soup1, soup2)
        assert score == 100.0

    def test_check_resources_all_present(self, tmp_path):
        """资源完整性检查"""
        from verifier import RestoreVerifier

        html = "<html><body><p>hello</p></body></html>"
        restored_dir = tmp_path / "restored"
        self._create_restored_files(restored_dir, html)

        verifier = RestoreVerifier(
            original_url="https://example.com",
            restored_dir=str(restored_dir),
            check_points=[],
        )
        score = verifier._check_resources()
        assert score == 100.0

    def test_check_resources_missing(self, tmp_path):
        """资源缺失"""
        from verifier import RestoreVerifier

        html = "<html><body><p>hello</p></body></html>"
        restored_dir = tmp_path / "restored"
        (restored_dir / "index.html").write_text(html, encoding="utf-8")
        # 不创建 assets 目录

        verifier = RestoreVerifier(
            original_url="https://example.com",
            restored_dir=str(restored_dir),
            check_points=[],
        )
        score = verifier._check_resources()
        assert score == 0.0

    def test_check_interactions(self, tmp_path):
        """交互元素检查"""
        from verifier import RestoreVerifier

        html1 = '<html><body><button>OK</button><a href="/x">link</a><input name="q"></body></html>'
        html2 = '<html><body><button>OK</button><a href="/x">link</a><input name="q"></body></html>'
        restored_dir = tmp_path / "restored"
        self._create_restored_files(restored_dir, html2)

        verifier = RestoreVerifier(
            original_url="https://example.com",
            restored_dir=str(restored_dir),
            check_points=[],
        )

        from bs4 import BeautifulSoup
        soup1 = BeautifulSoup(html1, "html.parser")
        soup2 = BeautifulSoup(html2, "html.parser")
        score = verifier._check_interactions(soup1, soup2)
        assert score == 100.0

    @patch("verifier.requests.Session")
    def test_run_missing_restored_file(self, mock_session_cls, tmp_path):
        """复原文件不存在"""
        from verifier import RestoreVerifier

        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "<html><body>original</body></html>"
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_session_cls.return_value = mock_session

        verifier = RestoreVerifier(
            original_url="https://example.com",
            restored_dir=str(tmp_path / "nonexistent"),
            check_points=[],
        )

        result = verifier.run()
        assert result["success"] is False
        assert "error" in result