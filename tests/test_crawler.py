"""测试 crawler 模块"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "restore_pipeline"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "utils"))


class TestRestoreCrawler:
    """页面复原爬虫测试"""

    def test_generate_filename(self, tmp_path):
        """测试文件名生成"""
        from crawler import RestoreCrawler
        crawler = RestoreCrawler("https://example.com/page", str(tmp_path))
        name = crawler._generate_filename("https://example.com/css/style.css?v=1", ".css")
        assert name.endswith(".css")
        assert len(name) < 100

    def test_generate_filename_with_long_url(self, tmp_path):
        """长 URL 文件名截断"""
        from crawler import RestoreCrawler
        crawler = RestoreCrawler("https://example.com/page", str(tmp_path))
        long_url = "https://example.com/" + "a" * 200 + "/style.css"
        name = crawler._generate_filename(long_url, ".css")
        assert name.endswith(".css")
        assert len(name) < 150

    def test_make_relative_path(self, tmp_path):
        """相对路径生成"""
        from crawler import RestoreCrawler
        crawler = RestoreCrawler("https://example.com/page", str(tmp_path))
        result = crawler._make_relative_path(tmp_path / "assets" / "css" / "style.css")
        assert "assets/css/style.css" in result

    def test_noise_selectors_is_list(self, tmp_path):
        """噪声选择器是列表"""
        from crawler import RestoreCrawler
        crawler = RestoreCrawler("https://example.com/page", str(tmp_path))
        assert isinstance(crawler.NOISE_SELECTORS, list)
        assert len(crawler.NOISE_SELECTORS) > 0

    def test_allowed_types_is_dict(self, tmp_path):
        """允许的类型是字典"""
        from crawler import RestoreCrawler
        crawler = RestoreCrawler("https://example.com/page", str(tmp_path))
        assert isinstance(crawler.ALLOWED_TYPES, dict)
        assert ".css" in crawler.ALLOWED_TYPES
        assert ".js" in crawler.ALLOWED_TYPES
        assert ".png" in crawler.ALLOWED_TYPES

    @patch("crawler.requests.Session")
    def test_run_basic(self, mock_session_cls, tmp_path, sample_html):
        """基本复原流程"""
        from crawler import RestoreCrawler

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.text = sample_html
        mock_response.content = b"/* css */"
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        mock_session_cls.return_value = mock_session

        crawler = RestoreCrawler("https://example.com/page", str(tmp_path))
        crawler.session = mock_session

        result = crawler.run()
        assert result["success"] is True
        assert "html_file" in result
        assert (tmp_path / "index.html").exists()
        assert (tmp_path / "original.html").exists()
        assert (tmp_path / "restoration_log.md").exists()

    def test_clean_noise_removes_ads(self, tmp_path, sample_html):
        """噪声清洗移除广告"""
        from bs4 import BeautifulSoup
        from crawler import RestoreCrawler

        crawler = RestoreCrawler("https://example.com/page", str(tmp_path))
        soup = BeautifulSoup(sample_html, "html.parser")

        # 确认广告存在
        assert soup.find(class_="ad") is not None

        crawler._clean_noise(soup)

        # 确认广告被移除
        assert soup.find(class_="ad") is None

    def test_clean_noise_removes_comments(self, tmp_path):
        """噪声清洗移除注释"""
        from bs4 import BeautifulSoup, Comment
        from crawler import RestoreCrawler

        html = "<html><body><!-- 这是一条注释 --><p>内容</p></body></html>"
        crawler = RestoreCrawler("https://example.com/page", str(tmp_path))
        soup = BeautifulSoup(html, "html.parser")

        assert len(soup.find_all(string=lambda t: isinstance(t, Comment))) > 0
        crawler._clean_noise(soup)
        assert len(soup.find_all(string=lambda t: isinstance(t, Comment))) == 0