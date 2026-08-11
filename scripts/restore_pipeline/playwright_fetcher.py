#!/usr/bin/env python3
"""
Playwright 页面获取模块
职责：通过 Playwright 持久化浏览器（有头）获取 JS 渲染后的 HTML、整页截图

登录态方案：launch_persistent_context 使用固定 user_data_dir，
首次有头启动时在弹出的浏览器中手动登录一次，登录态随 profile 持久化，
后续运行自动复用（等效于「接管日常浏览器」的登录态能力）。
"""

import logging
import os
import time
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DEFAULT_USER_DATA_DIR = "~/.cache/pm-restore-browser-profile"

try:
    from playwright.sync_api import sync_playwright
    _IMPORT_ERROR = None
except ImportError as _e:  # 包未安装时不阻断模块导入，由 check_health 报告
    sync_playwright = None
    _IMPORT_ERROR = _e


class PlaywrightError(Exception):
    """Playwright 操作基础异常"""
    pass


class PlaywrightUnavailableError(PlaywrightError):
    """playwright 包未安装或浏览器二进制缺失"""
    pass


class PlaywrightTimeoutError(PlaywrightError):
    """页面导航或操作超时"""
    pass


class PlaywrightAPIError(PlaywrightError):
    """Playwright 调用返回错误"""
    pass


class PlaywrightFetcher:
    """Playwright 持久化浏览器客户端，用于页面获取与整页截图"""

    def __init__(self, session_name="restore-pipeline",
                 page_load_wait=3.0, scroll_times=3,
                 user_data_dir=None, headless=False):
        self.session_name = session_name
        self.page_load_wait = page_load_wait
        self.scroll_times = scroll_times
        self.user_data_dir = os.path.expanduser(
            user_data_dir or DEFAULT_USER_DATA_DIR
        )
        self.headless = headless
        self._pw = None       # sync_playwright() 实例
        self._context = None  # 持久化浏览器上下文
        self._page = None     # 复用单 page

    @staticmethod
    def check_health():
        """检查 Playwright 是否可用（包已安装 + chromium 二进制存在）"""
        if sync_playwright is None:
            return {
                "available": False,
                "version": None,
                "error": "playwright 包未安装（pip install playwright）",
            }
        try:
            import importlib.metadata as importlib_metadata
            version = importlib_metadata.version("playwright")
        except Exception:
            version = None
        try:
            with sync_playwright() as p:
                exe = p.chromium.executable_path
            if exe and Path(exe).exists():
                return {"available": True, "version": version, "error": None}
            return {
                "available": False,
                "version": version,
                "error": (
                    f"chromium 二进制不存在: {exe}"
                    "（playwright install chromium）"
                ),
            }
        except Exception as e:
            return {
                "available": False,
                "version": version,
                "error": f"chromium 探测失败: {e}（playwright install chromium）",
            }

    def fetch_html(self, url):
        """导航到 URL，等待 JS 渲染并滚动触发懒加载，返回完整 HTML"""
        try:
            page = self._ensure_page()
            self._goto(page, url)
            time.sleep(self.page_load_wait)

            for _ in range(self.scroll_times):
                self._scroll_page()
                time.sleep(0.5)

            html = page.content()
            if not html:
                raise PlaywrightAPIError("page.content() 返回空 HTML")
            return html

        except PlaywrightError:
            raise
        except Exception as e:
            raise PlaywrightError(f"获取页面失败: {e}") from e

    def save_screenshot(self, output_path):
        """把当前页面整页截图保存到 output_path。

        Returns:
            保存成功的文件路径，或 None（失败）
        """
        try:
            page = self._ensure_page()
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(output_path), full_page=True)
            logger.info("截图已保存: %s", output_path)
            return str(output_path)
        except Exception as e:
            logger.warning("截图失败: %s", e)
            return None

    def capture_full_page(self, url, output_path, wait=None, nav_retries=2):
        """导航到指定 URL（支持 http/https/file 协议），等待渲染后截整页，保存到 output_path。

        用于视觉验收：分别截「线上原始页面」和「本地复原页面」做对比基准。
        Playwright 原生支持 file:// 与 full_page 截图（含滚动区域）。

        导航后会校验 page.url 是否落地到目标 URL，未落地（常见于 SPA 路由
        守卫拦截）则最多重试 nav_retries 次，避免截到残留页面/白屏。

        Args:
            url: 目标 URL（可以是 file:///abs/path/to/index.html）
            output_path: 截图保存路径
            wait: 自定义页面加载等待秒数（默认用 self.page_load_wait）
            nav_retries: 导航未落地时的最大重试次数（默认 2）

        Returns:
            保存成功的文件路径，或 None（失败）
        """
        try:
            landed = self._ensure_navigation_landed(url, wait, nav_retries)

            # 整页截图前先滚动到底触发懒加载，再回到顶部截图
            for _ in range(self.scroll_times):
                self._scroll_page()
                time.sleep(0.5)
            # 回到顶部，确保整页截图从页面起始开始
            if self._page is not None:
                self._page.evaluate("window.scrollTo(0, 0)")
                time.sleep(0.3)

            if not landed:
                # 未落地仍尝试截图（不阻断流程），但记录 warning 供调用方判断
                logger.warning(
                    "capture_full_page: 导航未落地到 %s（重试 %d 次后仍不匹配），"
                    "截图可能为残留页面", url, nav_retries,
                )

            return self.save_screenshot(output_path)

        except PlaywrightError as e:
            logger.warning("capture_full_page 失败 [%s]: %s", url, e)
            return None
        except Exception as e:
            logger.warning("capture_full_page 异常 [%s]: %s", url, e)
            return None

    def close(self):
        """关闭浏览器上下文与 playwright 实例（幂等，异常静默）"""
        for resource in (self._context, self._pw):
            if resource is None:
                continue
            try:
                if resource is self._context:
                    resource.close()
                else:
                    resource.stop()
            except Exception:
                pass
        self._page = None
        self._context = None
        self._pw = None

    # ---------- 内部方法 ----------

    def _ensure_page(self):
        """惰性启动持久化浏览器并返回复用的 page"""
        if self._page is not None:
            return self._page
        if sync_playwright is None:
            raise PlaywrightUnavailableError(
                "playwright 包未安装（pip install playwright）"
            ) from _IMPORT_ERROR
        try:
            Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
            self._pw = sync_playwright().start()
            self._context = self._pw.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=self.headless,
                viewport={"width": 1440, "height": 900},
                accept_downloads=False,
            )
            self._page = (
                self._context.pages[0]
                if self._context.pages
                else self._context.new_page()
            )
            return self._page
        except PlaywrightError:
            raise
        except Exception as e:
            self.close()
            raise PlaywrightUnavailableError(f"浏览器启动失败: {e}") from e

    def _goto(self, page, url):
        """导航到 URL，等待 DOM 就绪（SPA 的异步渲染由后续 sleep 兜底）"""
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        except Exception as e:
            msg = str(e).lower()
            if "timeout" in msg:
                raise PlaywrightTimeoutError(f"导航超时: {url}") from e
            raise PlaywrightAPIError(f"导航失败 [{url}]: {e}") from e

    def _ensure_navigation_landed(self, url, wait=None, nav_retries=2):
        """导航到 url 并校验是否真正落地，未落地则重试。

        Returns:
            bool: 最终是否落地到目标 URL
        """
        page = self._ensure_page()
        for attempt in range(nav_retries + 1):
            self._goto(page, url)
            time.sleep(wait if wait is not None else self.page_load_wait)
            try:
                current = page.url or ""
            except Exception:
                current = ""
            if self._urls_match(current, url):
                if attempt > 0:
                    logger.info(
                        "导航落地校验：第 %d 次重试后成功 (%s)", attempt + 1, url
                    )
                return True
            if attempt < nav_retries:
                logger.warning(
                    "导航未落地: 期望 %s 实际 %s（第 %d 次，将重试）",
                    url, current, attempt + 1,
                )
        return False

    @staticmethod
    def _urls_match(current, target):
        """判断当前 URL 是否落地到目标 URL。

        比较规则：scheme + host + port + path 相同即视为落地，容忍 query/hash
        差异（SPA 抓取瞬间的路由参数、时间戳等不影响页面本体）。
        file:// 协议按完整 path 比较。
        """
        if not current or not target:
            return False
        try:
            c = urlparse(current)
            t = urlparse(target)
        except Exception:
            return current == target
        # file:// 比较 path
        if t.scheme == "file" or c.scheme == "file":
            return c.scheme == t.scheme and c.path == t.path
        # http/https 比较 netloc(host:port) + path，忽略 query/fragment；
        # path 归一化：浏览器会给裸域名补尾斜杠（example.com → example.com/）
        return (
            c.scheme == t.scheme
            and c.netloc == t.netloc
            and (c.path or "/") == (t.path or "/")
        )

    def _scroll_page(self):
        """向下滚动页面，触发懒加载内容（best-effort，失败不阻断）"""
        if self._page is None:
            return
        try:
            self._page.evaluate("window.scrollBy(0, window.innerHeight)")
        except Exception as e:
            logger.warning("滚动页面失败（忽略）: %s", e)


def create_fetcher(mode, **kwargs):
    """
    工厂函数：根据模式创建 fetcher

    Args:
        mode: 'requests' | 'playwright' | 'auto'
        **kwargs: 传递给 PlaywrightFetcher.__init__

    Returns:
        PlaywrightFetcher 实例，或 None（使用 requests）
    """
    if mode == "requests":
        return None

    health = PlaywrightFetcher.check_health()
    if health["available"]:
        logger.info(
            "Playwright 可用 (v%s)，使用浏览器获取模式",
            health.get("version", "?"),
        )
        return PlaywrightFetcher(**kwargs)

    if mode == "playwright":
        raise PlaywrightUnavailableError(
            f"Playwright 不可用: {health['error']}"
        )

    # auto 模式降级
    logger.warning(
        "Playwright 不可用 (%s)，降级为 requests 模式",
        health["error"],
    )
    return None
