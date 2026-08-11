#!/usr/bin/env python3
"""
复原爬取模块
职责：抓取页面 DOM 和资源，清洗去噪，输出可运行代码
核心原则：只抓取现有代码，禁止重新编码
"""

import logging
import os
import re
import hashlib
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Comment

import sys
from pathlib import Path
# Add utils to path
_utils_dir = str(Path(__file__).parent.parent / "utils")
if _utils_dir not in sys.path:
    sys.path.insert(0, _utils_dir)
from utils.retry import retry_call
from utils.config import (
    get_crawler_timeout_seconds,
    get_max_resource_size_mb,
    get_allowed_resource_types,
    get_noise_selectors,
    get_freeze_render_scripts,
    get_freeze_patterns,
    get_remove_preload_scripts,
    is_render_script,
)

from auth_handler import AuthHandler

logger = logging.getLogger(__name__)


class RestoreCrawler:
    """页面复原爬虫"""

    # 噪声选择器（广告、追踪等）— 从配置文件读取，无配置时使用默认值
    NOISE_SELECTORS = get_noise_selectors()

    # 允许下载的资源类型 — 从配置文件读取
    ALLOWED_TYPES = {
        f".{ext}": "css" if ext in ["css"] else "js" if ext in ["js"] else "images" if ext in ["png", "jpg", "jpeg", "gif", "svg", "webp", "ico"] else "fonts"
        for ext in get_allowed_resource_types()
    }

    def __init__(self, url, output_dir, username=None, password=None,
                 captcha=None, cookie=None, timeout=None, fetcher=None):
        self.url = url
        self.output_dir = Path(output_dir)
        self.username = username
        self.password = password
        self.captcha = captcha
        self.cookie = cookie
        self.timeout = timeout if timeout else get_crawler_timeout_seconds()
        self.fetcher = fetcher
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        self.downloaded_resources = {}
        self.log_lines = []

    def _log(self, message):
        """记录日志"""
        self.log_lines.append(message)
        logger.info("  %s", message)

    def run(self):
        """执行复原流程"""
        try:
            # 1. 登录处理（仅 requests 模式）
            if not self.fetcher and (self.username or self.cookie):
                auth = AuthHandler(self.session)
                success = auth.login(
                    url=self.url,
                    username=self.username,
                    password=self.password,
                    captcha=self.captcha,
                    cookie=self.cookie,
                )
                if not success:
                    return {"success": False, "error": "登录失败"}
                self._log("登录成功，Cookie 已设置")

            # 2. 获取页面
            self._log(f"正在抓取: {self.url}")
            if self.fetcher:
                original_html = self.fetcher.fetch_html(self.url)
                self._log(f"[Playwright] 页面大小: {len(original_html)} 字节")
            else:
                response = retry_call(
                self.session.get,
                args=(self.url,),
                kwargs={"timeout": self.timeout},
                max_retries=3,
                retry_delay=1.0,
                )
                response.raise_for_status()
                original_html = response.text
                self._log(f"页面大小: {len(original_html)} 字节")

            # 3. 解析 DOM
            soup = BeautifulSoup(original_html, "html.parser")

            # 4. 创建输出目录
            self.output_dir.mkdir(parents=True, exist_ok=True)
            assets_dir = self.output_dir / "assets"
            assets_dir.mkdir(exist_ok=True)
            for sub in ["css", "js", "images", "fonts"]:
                (assets_dir / sub).mkdir(exist_ok=True)

            # 5. 下载并处理资源
            self._process_resources(soup, self.url, assets_dir)

            # 6. 清洗去噪
            self._clean_noise(soup)

            # 6.5 静态冻结：中和 SPA 渲染脚本，防止本地打开时二次渲染污染
            self._freeze_render_scripts(soup)

            # 7. 生成多文件版本
            html_path = self.output_dir / "index.html"
            html_path.write_text(str(soup), encoding="utf-8")
            self._log(f"多文件版本: {html_path}")

            # 8. 生成单文件版本（内联 CSS）
            inline_soup = BeautifulSoup(str(soup), "html.parser")
            self._inline_css(inline_soup, assets_dir)
            inline_path = self.output_dir / "index_inline.html"
            inline_path.write_text(str(inline_soup), encoding="utf-8")
            self._log(f"单文件版本: {inline_path}")

            # 9. 保存原始 HTML
            original_path = self.output_dir / "original.html"
            original_path.write_text(original_html, encoding="utf-8")

            # 9.5 保存视觉参考截图（仅 Playwright 模式）
            if self.fetcher:
                screenshot_path = self.output_dir / "reference_screenshot.png"
                saved = self.fetcher.save_screenshot(str(screenshot_path))
                if saved:
                    self._log(f"视觉参考截图: {saved}")

            # 10. 保存日志
            log_path = self.output_dir / "restoration_log.md"
            log_content = self._generate_log()
            log_path.write_text(log_content, encoding="utf-8")

            # 统计
            resource_count = len(self.downloaded_resources)

            return {
                "success": True,
                "html_file": str(html_path),
                "inline_file": str(inline_path),
                "resource_count": resource_count,
                "output_dir": str(self.output_dir),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _process_resources(self, soup, base_url, assets_dir):
        """下载并处理外部资源"""
        # CSS
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if href:
                local_path = self._download_resource(href, base_url, assets_dir)
                if local_path:
                    link["href"] = self._make_relative_path(local_path)

        # JS
        for script in soup.find_all("script", src=True):
            src = script.get("src")
            if src:
                local_path = self._download_resource(src, base_url, assets_dir)
                if local_path:
                    script["src"] = self._make_relative_path(local_path)

        # Images
        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                local_path = self._download_resource(src, base_url, assets_dir)
                if local_path:
                    img["src"] = self._make_relative_path(local_path)

        # Favicon
        for link in soup.find_all("link", rel="icon"):
            href = link.get("href")
            if href:
                local_path = self._download_resource(href, base_url, assets_dir)
                if local_path:
                    link["href"] = self._make_relative_path(local_path)

        # <link rel="preload"> 预加载资源（script/style/font/image 等）
        # SPA 常用 preload 提示预加载 JS chunk，未处理会残留原始路径产生 404
        for link in soup.find_all("link", rel="preload"):
            href = link.get("href")
            if href:
                local_path = self._download_resource(href, base_url, assets_dir)
                if local_path:
                    link["href"] = self._make_relative_path(local_path)

        # Background images in style attributes
        for elem in soup.find_all(style=True):
            style = elem.get("style", "")
            new_style = self._process_style_urls(style, base_url, assets_dir)
            elem["style"] = new_style

        # <style> 标签内的 url()（@font-face 字体、background-image 等）
        # SPA 页面样式常内联在 <style> 中，不解析会遗漏字体下载导致图标不显示
        for style_tag in soup.find_all("style"):
            if style_tag.string:
                new_css = self._process_style_urls(style_tag.string, base_url, assets_dir)
                style_tag.string.replace_with(new_css)

        # CSS @import and url()
        css_dir = assets_dir / "css"
        if css_dir.exists():
            for css_file in css_dir.glob("*.css"):
                self._process_css_urls(css_file, base_url, assets_dir)

        # JS chunk 内 url() 引用（webpack 打包的资源、运行时加载的图片/字体等）
        # SPA 的 JS 包内可能含 url(./xxx.png) 形式的资源引用，未解析会遗漏下载
        js_dir = assets_dir / "js"
        if js_dir.exists():
            for js_file in js_dir.glob("*.js"):
                self._process_js_urls(js_file, base_url, assets_dir)

    def _process_js_urls(self, js_file, base_url, assets_dir):
        """处理 JS 文件中的 url() 资源引用

        webpack 打包的 JS 中，url(路径) 形式引用的资源需下载并改写。
        排除：data: URI、# 锚点、http(s) 绝对外部地址、变量拼接占位符。
        """
        js_url = urljoin(base_url, str(js_file.relative_to(self.output_dir)))
        try:
            content = js_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        def replace_url(match):
            raw = match.group(1).strip().strip("'\"")
            # 跳过：data URI、SVG/锚点引用、变量拼接、纯占位符
            if (raw.startswith("data:")
                    or raw.startswith("#")
                    or raw == ""
                    or raw == "..."
                    or raw.startswith(" + ")
                    or "+ " in raw
                    or raw.endswith(" +")
                    or "${" in raw
                    or raw.startswith("JSON.stringify")):
                return match.group(0)
            # 跳过 http(s) 外部地址（跨域资源，本地化风险高）
            if raw.startswith("http://") or raw.startswith("https://"):
                return match.group(0)
            local_path = self._download_resource(raw, js_url, assets_dir)
            if local_path:
                rel = self._make_relative_path(local_path)
                js_rel = js_file.parent.relative_to(self.output_dir)
                try:
                    rel_path = Path(rel).relative_to(js_rel)
                    return f"url({rel_path})"
                except ValueError:
                    return f"url({rel})"
            return match.group(0)

        new_content = re.sub(r'url\(["\']?([^"\')]+)["\']?\)', replace_url, content)
        if new_content != content:
            js_file.write_text(new_content, encoding="utf-8")

    def _download_resource(self, url, base_url, assets_dir):
        """下载单个资源"""
        full_url = urljoin(base_url, url)

        # 去重检查
        if full_url in self.downloaded_resources:
            return self.downloaded_resources[full_url]

        # 解析文件类型
        parsed = urlparse(full_url)
        path = parsed.path
        ext = Path(path).suffix.lower()

        if ext not in self.ALLOWED_TYPES:
            return None

        subdir = self.ALLOWED_TYPES[ext]
        target_dir = assets_dir / subdir

        try:
            resp = retry_call(
                self.session.get,
                args=(full_url,),
                kwargs={"timeout": self.timeout},
                max_retries=3,
                retry_delay=1.0,
            )
            resp.raise_for_status()

            # 资源大小检查
            max_size_bytes = get_max_resource_size_mb() * 1024 * 1024
            if len(resp.content) > max_size_bytes:
                self._log(f"资源过大，跳过: {full_url} ({len(resp.content) / 1024 / 1024:.1f}MB > {get_max_resource_size_mb()}MB)")
                return None

            # 生成文件名
            filename = self._generate_filename(full_url, ext)
            target_path = target_dir / filename

            # 保存
            target_path.write_bytes(resp.content)

            self.downloaded_resources[full_url] = target_path
            self._log(f"下载: {filename} ({len(resp.content)} 字节)")
            return target_path

        except Exception as e:
            self._log(f"下载失败 [{full_url}]: {e}")
            return None

    def _generate_filename(self, url, ext):
        """生成唯一文件名"""
        # 使用 URL hash 避免冲突
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        parsed = urlparse(url)
        basename = Path(parsed.path).stem
        if not basename or basename == "/":
            basename = "resource"
        # 清理文件名
        basename = re.sub(r"[^\w\-]", "_", basename)[:40]
        return f"{basename}_{url_hash}{ext}"

    def _make_relative_path(self, local_path):
        """生成相对路径"""
        if isinstance(local_path, Path):
            return str(local_path.relative_to(self.output_dir)).replace("\\", "/")
        return local_path

    def _process_style_urls(self, style, base_url, assets_dir):
        """处理 style 属性中的 url()"""
        def replace_url(match):
            url = match.group(1).strip("'\"")
            local_path = self._download_resource(url, base_url, assets_dir)
            if local_path:
                return f"url('{self._make_relative_path(local_path)}')"
            return match.group(0)

        return re.sub(r'url\(["\']?([^"\')]+)["\']?\)', replace_url, style)

    def _process_css_urls(self, css_file, base_url, assets_dir):
        """处理 CSS 文件中的 url()"""
        css_url = urljoin(base_url, str(css_file.relative_to(self.output_dir)))
        content = css_file.read_text(encoding="utf-8")

        def replace_url(match):
            url = match.group(1).strip("'\"")
            if url.startswith("data:") or url.startswith("#"):
                return match.group(0)
            local_path = self._download_resource(url, css_url, assets_dir)
            if local_path:
                rel = self._make_relative_path(local_path)
                # 计算相对于 CSS 文件的路径
                css_rel = css_file.parent.relative_to(self.output_dir)
                try:
                    rel_path = Path(rel).relative_to(css_rel)
                    return f"url('{rel_path}')"
                except ValueError:
                    return f"url('{rel}')"
            return match.group(0)

        new_content = re.sub(r'url\(["\']?([^"\')]+)["\']?\)', replace_url, content)
        css_file.write_text(new_content, encoding="utf-8")

    def _clean_noise(self, soup):
        """清洗噪声内容"""
        # 移除噪声节点
        for selector in self.NOISE_SELECTORS:
            try:
                for elem in soup.select(selector):
                    elem.decompose()
                    self._log(f"移除噪声: {selector}")
            except Exception:
                pass

        # 移除 HTML 注释
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 移除空的 style/script 标签
        for tag in soup.find_all(["style", "script"]):
            if not tag.contents and not tag.get("src"):
                tag.decompose()

        # 移除 data-* 属性中的追踪相关属性
        for elem in soup.find_all(True):
            attrs_to_remove = [k for k in elem.attrs if k.startswith("data-track") or k.startswith("data-analytics")]
            for attr in attrs_to_remove:
                del elem.attrs[attr]

    def _freeze_render_scripts(self, soup):
        """中和会触发二次渲染的 SPA 脚本，防止本地打开时覆盖渲染好的 DOM 快照。

        Playwright 抓取的是 Vue/React 渲染后的 DOM。若保留 app.js 等渲染脚本，
        本地打开时框架会重新挂载 #app，因无后端 API/路由守卫/登录态导致白屏或样式错乱。
        处理方式：移除匹配关键词的 <script> 和 <link rel="preload" as="script">。
        JS 文件本身保留在 assets/js/ 备查（仅移除 HTML 中的引用标签）。
        """
        if not get_freeze_render_scripts():
            return

        patterns = get_freeze_patterns()
        if not patterns:
            return

        # 1. 中和渲染型 <script src>（src basename stem 以任一关键词开头）
        removed_scripts = []
        for script in soup.find_all("script", src=True):
            src = script.get("src", "")
            if is_render_script(src, patterns):
                removed_scripts.append(src)
                script.decompose()
        if removed_scripts:
            self._log(f"[静态冻结] 中和 {len(removed_scripts)} 个渲染脚本: "
                      f"{', '.join(Path(s).name for s in removed_scripts)}")

        # 2. 移除 <link rel="preload" as="script">（仅 script 类型 preload）
        if get_remove_preload_scripts():
            removed_preloads = []
            for link in soup.find_all("link", rel="preload"):
                if link.get("as") == "script":
                    href = link.get("href", "")
                    removed_preloads.append(href)
                    link.decompose()
            if removed_preloads:
                self._log(f"[静态冻结] 移除 {len(removed_preloads)} 个脚本 preload: "
                          f"{', '.join(Path(h).name for h in removed_preloads)}")

    def _inline_css(self, soup, assets_dir):
        """将外部 CSS 内联"""
        css_dir = assets_dir / "css"
        if not css_dir.exists():
            return

        inline_styles = []
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if href:
                css_path = self.output_dir / href
                if css_path.exists():
                    css_content = css_path.read_text(encoding="utf-8")
                    inline_styles.append(css_content)
                    link.decompose()

        if inline_styles:
            style_tag = soup.new_tag("style")
            style_tag.string = "\n".join(inline_styles)
            head = soup.find("head")
            if head:
                head.append(style_tag)

    def _generate_log(self):
        """生成复原日志"""
        lines = [
            "# 复原日志",
            "",
            f"- 目标 URL: {self.url}",
            f"- 输出目录: {self.output_dir}",
            f"- 下载资源数: {len(self.downloaded_resources)}",
            "",
            "## 执行记录",
            "",
        ]
        for line in self.log_lines:
            lines.append(f"- {line}")

        lines.extend([
            "",
            "## 已下载资源",
            "",
        ])
        for url, path in self.downloaded_resources.items():
            lines.append(f"- `{url}` → `{path}`")

        lines.append("")
        return "\n".join(lines)
