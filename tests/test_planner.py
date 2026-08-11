"""测试 planner 模块"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "restore_pipeline"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "utils"))


class TestRestorePlanner:
    """复原计划生成器测试"""

    def test_init(self):
        """初始化"""
        from planner import RestorePlanner
        planner = RestorePlanner("https://example.com/page")
        assert planner.url == "https://example.com/page"
        assert planner.domain == "example.com"

    @patch("planner.requests")
    def test_analyze_success(self, mock_requests, sample_html):
        """成功分析页面"""
        from planner import RestorePlanner

        mock_head_resp = MagicMock()
        mock_head_resp.status_code = 200

        mock_get_resp = MagicMock()
        mock_get_resp.text = sample_html

        mock_requests.head.return_value = mock_head_resp
        mock_requests.get.return_value = mock_get_resp

        planner = RestorePlanner("https://example.com/page")
        result = planner.analyze()

        assert result["success"] is True
        assert "plan" in result
        assert "sections" in result
        assert "resources" in result
        assert "check_points" in result

    @patch("planner.requests")
    def test_analyze_network_error(self, mock_requests):
        """网络错误"""
        from planner import RestorePlanner

        mock_requests.head.side_effect = Exception("Connection error")

        planner = RestorePlanner("https://example.com/page")
        result = planner.analyze()

        assert result["success"] is False
        assert "error" in result

    def test_detect_login_with_password(self):
        """检测密码登录"""
        from planner import RestorePlanner
        planner = RestorePlanner("https://example.com/login")
        from bs4 import BeautifulSoup
        html = '<form><input type="password" name="pass"></form>'
        soup = BeautifulSoup(html, "html.parser")
        result = planner._detect_login(soup, html)
        assert result["type"] == "password"

    def test_detect_login_with_captcha(self):
        """检测验证码"""
        from planner import RestorePlanner
        planner = RestorePlanner("https://example.com/page")
        from bs4 import BeautifulSoup
        html = '<form><input name="code"><p>请输入验证码</p></form>'
        soup = BeautifulSoup(html, "html.parser")
        result = planner._detect_login(soup, html)
        assert result["type"] == "captcha"

    def test_detect_login_none(self):
        """无登录需求"""
        from planner import RestorePlanner
        planner = RestorePlanner("https://example.com/page")
        from bs4 import BeautifulSoup
        html = '<div><p>普通页面内容</p></div>'
        soup = BeautifulSoup(html, "html.parser")
        result = planner._detect_login(soup, html)
        assert result["type"] == "none"

    def test_generate_check_points(self):
        """生成检查点"""
        from planner import RestorePlanner
        planner = RestorePlanner("https://example.com/page")

        sections = [{"name": "header", "selector": "header", "tag": "header", "node_count": 10, "depth": 3}]
        resources = {"css": ["style.css"], "js": [], "images": ["logo.png"], "fonts": []}

        check_points = planner._generate_check_points(sections, resources)
        assert len(check_points) > 0
        # 至少包含结构、资源、样式、交互检查点
        categories = {cp["category"] for cp in check_points}
        assert "structure" in categories

    def test_generate_plan_document(self):
        """生成计划文档"""
        from planner import RestorePlanner
        planner = RestorePlanner("https://example.com/page")

        doc = planner._generate_plan_document(
            status_code=200,
            sections=[],
            resources={"css": [], "js": [], "images": [], "fonts": []},
            login_info={"type": "none", "reason": ""},
            check_points=[],
        )
        assert "复原计划" in doc
        assert "example.com" in doc