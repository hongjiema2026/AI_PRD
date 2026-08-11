#!/usr/bin/env python3
"""Playwright fetcher 单元测试"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

import sys
_pipeline_dir = str(Path(__file__).parent.parent / "scripts" / "restore_pipeline")
if _pipeline_dir not in sys.path:
    sys.path.insert(0, _pipeline_dir)

import playwright_fetcher
from playwright_fetcher import (
    PlaywrightFetcher,
    PlaywrightError,
    PlaywrightUnavailableError,
    PlaywrightTimeoutError,
    PlaywrightAPIError,
    create_fetcher,
)


class FakePage:
    """模拟 playwright Page 的最小实现"""

    def __init__(self, url="about:blank", content="<html><body>Hello</body></html>"):
        self.url = url
        self._content = content
        self.goto_calls = []
        self.screenshot_calls = []
        self.evaluate_calls = []
        self._goto_behavior = None  # 可选：callable(url) -> 落地后的 url

    def goto(self, url, wait_until=None, timeout=None):
        self.goto_calls.append(url)
        if self._goto_behavior:
            self.url = self._goto_behavior(url)
        else:
            self.url = url  # 默认立即落地

    def content(self):
        return self._content

    def screenshot(self, path=None, full_page=False):
        self.screenshot_calls.append({"path": path, "full_page": full_page})
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(b"fake-png")

    def evaluate(self, code):
        self.evaluate_calls.append(code)
        return None


def _healthy_pw(fake_page=None):
    """构造一个可用的假 sync_playwright：sync_playwright().start() → pw → context(page)"""
    fake_page = fake_page or FakePage()
    fake_context = MagicMock()
    fake_context.pages = [fake_page]
    fake_pw = MagicMock()
    fake_pw.chromium.launch_persistent_context.return_value = fake_context
    fakeStarter = MagicMock()
    fakeStarter.return_value.start.return_value = fake_pw
    return fakeStarter, fake_pw, fake_context, fake_page


class TestCheckHealth(unittest.TestCase):

    def test_healthy(self):
        fake_pw = MagicMock()
        fake_pw.chromium.executable_path = "/bin/sh"  # 真实存在的文件
        fakeStarter = MagicMock()
        fakeStarter.return_value.__enter__ = MagicMock(return_value=fake_pw)
        fakeStarter.return_value.__exit__ = MagicMock(return_value=False)
        with patch.object(playwright_fetcher, "sync_playwright", fakeStarter):
            result = PlaywrightFetcher.check_health()
        self.assertTrue(result["available"])
        self.assertIsNone(result["error"])

    def test_package_missing(self):
        with patch.object(playwright_fetcher, "sync_playwright", None):
            result = PlaywrightFetcher.check_health()
        self.assertFalse(result["available"])
        self.assertIn("未安装", result["error"])

    def test_chromium_binary_missing(self):
        fake_pw = MagicMock()
        fake_pw.chromium.executable_path = "/nonexistent/path/chromium"
        fakeStarter = MagicMock()
        fakeStarter.return_value.__enter__ = MagicMock(return_value=fake_pw)
        fakeStarter.return_value.__exit__ = MagicMock(return_value=False)
        with patch.object(playwright_fetcher, "sync_playwright", fakeStarter):
            result = PlaywrightFetcher.check_health()
        self.assertFalse(result["available"])
        self.assertIn("chromium", result["error"])

    def test_probe_failure(self):
        fakeStarter = MagicMock(side_effect=RuntimeError("driver broken"))
        with patch.object(playwright_fetcher, "sync_playwright", fakeStarter):
            result = PlaywrightFetcher.check_health()
        self.assertFalse(result["available"])
        self.assertIn("探测失败", result["error"])


class TestFetchHtml(unittest.TestCase):

    def _make_fetcher(self, fake_page):
        fetcher = PlaywrightFetcher(
            session_name="test",
            page_load_wait=0.01,
            scroll_times=1,
        )
        fetcher._page = fake_page  # 注入，跳过真实浏览器启动
        return fetcher

    @patch("time.sleep")
    def test_success(self, mock_sleep):
        fake = FakePage(content="<html><body>Hello</body></html>")
        fetcher = self._make_fetcher(fake)
        html = fetcher.fetch_html("https://example.com")
        self.assertEqual(html, "<html><body>Hello</body></html>")
        self.assertEqual(fake.goto_calls, ["https://example.com"])

    @patch("time.sleep")
    def test_empty_html_raises(self, mock_sleep):
        fetcher = self._make_fetcher(FakePage(content=""))
        with self.assertRaises(PlaywrightAPIError):
            fetcher.fetch_html("https://example.com")

    @patch("time.sleep")
    def test_goto_timeout_raises_timeout_error(self, mock_sleep):
        fake = FakePage()
        fake.goto = MagicMock(side_effect=Exception("Timeout 60000ms exceeded"))
        fetcher = self._make_fetcher(fake)
        with self.assertRaises(PlaywrightTimeoutError):
            fetcher.fetch_html("https://example.com")

    @patch("time.sleep")
    def test_goto_failure_raises_api_error(self, mock_sleep):
        fake = FakePage()
        fake.goto = MagicMock(side_effect=Exception("net::ERR_CONNECTION_REFUSED"))
        fetcher = self._make_fetcher(fake)
        with self.assertRaises(PlaywrightAPIError):
            fetcher.fetch_html("https://example.com")

    @patch("time.sleep")
    def test_scroll_failure_does_not_break_fetch(self, mock_sleep):
        """滚动失败为 best-effort，不应阻断 HTML 获取"""
        fake = FakePage()
        def eval_flaky(code):
            if "scrollBy" in code:
                raise Exception("page crashed")
            return None
        fake.evaluate = eval_flaky
        fetcher = self._make_fetcher(fake)
        html = fetcher.fetch_html("https://example.com")
        self.assertIn("Hello", html)


class TestSaveScreenshot(unittest.TestCase):

    def test_success_full_page(self):
        fake = FakePage()
        fetcher = PlaywrightFetcher(session_name="test")
        fetcher._page = fake
        result = fetcher.save_screenshot("/tmp/test_pw_shot.png")
        self.assertEqual(result, "/tmp/test_pw_shot.png")
        self.assertEqual(fake.screenshot_calls[0]["full_page"], True)

    def test_failure_returns_none(self):
        fake = FakePage()
        fake.screenshot = MagicMock(side_effect=Exception("target closed"))
        fetcher = PlaywrightFetcher(session_name="test")
        fetcher._page = fake
        result = fetcher.save_screenshot("/tmp/test_pw_shot.png")
        self.assertIsNone(result)


class TestClose(unittest.TestCase):

    def test_close_releases_context_and_playwright(self):
        fakeStarter, fake_pw, fake_context, fake_page = _healthy_pw()
        fetcher = PlaywrightFetcher(session_name="test")
        fetcher._pw = fake_pw
        fetcher._context = fake_context
        fetcher._page = fake_page
        fetcher.close()
        fake_context.close.assert_called_once()
        fake_pw.stop.assert_called_once()
        self.assertIsNone(fetcher._page)
        self.assertIsNone(fetcher._context)
        self.assertIsNone(fetcher._pw)

    def test_close_silences_errors(self):
        fetcher = PlaywrightFetcher(session_name="test")
        fetcher._context = MagicMock()
        fetcher._context.close.side_effect = Exception("already closed")
        fetcher._pw = MagicMock()
        fetcher._pw.stop.side_effect = Exception("already stopped")
        fetcher.close()  # 不应抛异常

    def test_close_idempotent_when_never_started(self):
        PlaywrightFetcher(session_name="test").close()  # 不应抛异常


class TestEnsurePageLazyStart(unittest.TestCase):

    def test_lazy_start_and_reuse(self):
        """首次访问惰性启动持久化上下文，之后复用同一 page（不重复 launch）"""
        fakeStarter, fake_pw, fake_context, fake_page = _healthy_pw()
        fetcher = PlaywrightFetcher(
            session_name="test",
            user_data_dir="/tmp/test-pw-profile",
            headless=True,
        )
        with patch.object(playwright_fetcher, "sync_playwright", fakeStarter):
            page1 = fetcher._ensure_page()
            page2 = fetcher._ensure_page()
        self.assertIs(page1, fake_page)
        self.assertIs(page2, fake_page)
        fake_pw.chromium.launch_persistent_context.assert_called_once()
        kwargs = fake_pw.chromium.launch_persistent_context.call_args
        self.assertEqual(kwargs.args[0], "/tmp/test-pw-profile")
        self.assertEqual(kwargs.kwargs["headless"], True)
        fetcher.close()

    def test_start_failure_raises_unavailable(self):
        fakeStarter = MagicMock()
        fakeStarter.return_value.start.side_effect = Exception("driver missing")
        fetcher = PlaywrightFetcher(
            session_name="test", user_data_dir="/tmp/test-pw-profile",
        )
        with patch.object(playwright_fetcher, "sync_playwright", fakeStarter):
            with self.assertRaises(PlaywrightUnavailableError):
                fetcher._ensure_page()

    def test_package_missing_raises_unavailable(self):
        fetcher = PlaywrightFetcher(session_name="test")
        with patch.object(playwright_fetcher, "sync_playwright", None):
            with self.assertRaises(PlaywrightUnavailableError):
                fetcher._ensure_page()


class TestCaptureFullPageNavGuard(unittest.TestCase):
    """capture_full_page 的导航落地校验 + 重试测试。

    背景：视觉验收截「本地复原页」时，若浏览器当前 page 仍停在之前导航的
    线上 SPA 页面，goto 本地 URL 若被 SPA 路由守卫拦截，会截到残留页面/白屏。
    要求 capture_full_page 在 goto 后校验 page.url 是否落地，不落地则重试。
    """

    def _make_fetcher(self, fake_page):
        fetcher = PlaywrightFetcher(
            session_name="test",
            page_load_wait=0.01,
            scroll_times=1,
        )
        fetcher._page = fake_page
        return fetcher

    @patch("time.sleep")
    def test_nav_landed_first_try_no_retry(self, mock_sleep):
        """goto 后 URL 已落地 → 不重试，直接截图"""
        target = "http://127.0.0.1:18000/index.html"
        fake = FakePage()  # 默认 goto 即落地
        fetcher = self._make_fetcher(fake)
        result = fetcher.capture_full_page(target, "/tmp/out.png")
        self.assertEqual(result, "/tmp/out.png")
        self.assertEqual(len(fake.goto_calls), 1)

    @patch("time.sleep")
    def test_nav_not_landed_then_retry_succeeds(self, mock_sleep):
        """首次 goto 未落地（仍在线上页），重试后落地 → 截图成功"""
        online_url = "http://example.com/listing/list"
        target = "http://127.0.0.1:18000/index.html"
        fake = FakePage(url=online_url)
        calls = {"n": 0}
        def behavior(url):
            calls["n"] += 1
            return online_url if calls["n"] == 1 else target
        fake._goto_behavior = behavior
        fetcher = self._make_fetcher(fake)
        result = fetcher.capture_full_page(target, "/tmp/out.png")
        self.assertEqual(result, "/tmp/out.png")
        self.assertEqual(len(fake.goto_calls), 2)

    @patch("time.sleep")
    def test_nav_never_lands_still_attempts_screenshot(self, mock_sleep):
        """始终未落地 → 仍尝试截图（不阻断），日志可追溯"""
        online_url = "http://example.com/listing/list"
        target = "http://127.0.0.1:18000/index.html"
        fake = FakePage(url=online_url)
        fake._goto_behavior = lambda url: online_url  # 始终不落地
        fetcher = self._make_fetcher(fake)
        result = fetcher.capture_full_page(target, "/tmp/out.png", nav_retries=2)
        # 未落地也应返回截图路径（不阻断流程），调用方据 warning 判断
        self.assertEqual(result, "/tmp/out.png")
        # 初始 1 次 + 重试 2 次 = 3 次 goto
        self.assertEqual(len(fake.goto_calls), 3)

    @patch("time.sleep")
    def test_nav_query_hash_tolerance(self, mock_sleep):
        """URL 比较容忍 query/hash 差异（同 host+path 即视为落地）"""
        target = "http://127.0.0.1:18000/index.html"
        fake = FakePage()
        fake._goto_behavior = (
            lambda url: "http://127.0.0.1:18000/index.html?t=123#section"
        )
        fetcher = self._make_fetcher(fake)
        fetcher.capture_full_page(target, "/tmp/out.png")
        self.assertEqual(len(fake.goto_calls), 1)

    @patch("time.sleep")
    def test_file_url_landing(self, mock_sleep):
        """file:// 协议按 path 精确比较，Playwright 原生支持"""
        target = "file:///tmp/restored/index.html"
        fake = FakePage()
        fetcher = self._make_fetcher(fake)
        result = fetcher.capture_full_page(target, "/tmp/out.png")
        self.assertEqual(result, "/tmp/out.png")
        self.assertEqual(len(fake.goto_calls), 1)


class TestUrlsMatch(unittest.TestCase):

    def test_same_host_path_ignores_query_hash(self):
        self.assertTrue(PlaywrightFetcher._urls_match(
            "http://a.com:8080/p/list?x=1#top", "http://a.com:8080/p/list",
        ))

    def test_different_path_not_match(self):
        self.assertFalse(PlaywrightFetcher._urls_match(
            "http://a.com/p/a", "http://a.com/p/b",
        ))

    def test_file_scheme_compares_path(self):
        self.assertTrue(PlaywrightFetcher._urls_match(
            "file:///tmp/r/index.html", "file:///tmp/r/index.html",
        ))
        self.assertFalse(PlaywrightFetcher._urls_match(
            "file:///tmp/r/a.html", "file:///tmp/r/b.html",
        ))

    def test_empty_values_not_match(self):
        self.assertFalse(PlaywrightFetcher._urls_match("", "http://a.com"))
        self.assertFalse(PlaywrightFetcher._urls_match("http://a.com", ""))

    def test_bare_domain_trailing_slash_match(self):
        """浏览器会给裸域名补尾斜杠（example.com → example.com/），应视为落地"""
        self.assertTrue(PlaywrightFetcher._urls_match(
            "https://example.com/", "https://example.com",
        ))


class TestCreateFetcher(unittest.TestCase):

    def test_requests_mode_returns_none(self):
        result = create_fetcher("requests")
        self.assertIsNone(result)

    @patch.object(PlaywrightFetcher, "check_health")
    def test_auto_available(self, mock_health):
        mock_health.return_value = {
            "available": True, "version": "1.58.0", "error": None,
        }
        result = create_fetcher("auto")
        self.assertIsInstance(result, PlaywrightFetcher)

    @patch.object(PlaywrightFetcher, "check_health")
    def test_auto_unavailable_returns_none(self, mock_health):
        mock_health.return_value = {
            "available": False, "version": None, "error": "not installed",
        }
        result = create_fetcher("auto")
        self.assertIsNone(result)

    @patch.object(PlaywrightFetcher, "check_health")
    def test_playwright_unavailable_raises(self, mock_health):
        mock_health.return_value = {
            "available": False, "version": None, "error": "not installed",
        }
        with self.assertRaises(PlaywrightUnavailableError):
            create_fetcher("playwright")


if __name__ == "__main__":
    unittest.main()
