#!/usr/bin/env python3
"""
复原计划生成模块
职责：分析目标页面，生成复原计划和验证检查点
"""

import re
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

import sys
from pathlib import Path
# Add utils to path
_utils_dir = str(Path(__file__).parent.parent / "utils")
if _utils_dir not in sys.path:
    sys.path.insert(0, _utils_dir)
from utils.retry import retry_call
from utils.config import get_crawler_timeout_seconds


class RestorePlanner:
    """复原计划生成器"""

    def __init__(self, url, timeout=None, fetcher=None):
        self.url = url
        self.timeout = timeout if timeout != 30 else get_crawler_timeout_seconds()
        self.domain = urlparse(url).netloc
        self.fetcher = fetcher

    def analyze(self):
        """分析页面并生成计划"""
        try:
            if self.fetcher:
                # Playwright 模式：通过浏览器获取渲染后 HTML
                html = self.fetcher.fetch_html(self.url)
                status_code = 200
                soup = BeautifulSoup(html, "html.parser")
            else:
                # requests 模式（原有逻辑）
                try:
                    response = retry_call(
                        requests.head,
                        args=(self.url,),
                        kwargs={
                            "timeout": self.timeout,
                            "allow_redirects": True,
                            "headers": {
                                "User-Agent": (
                                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                                    "Chrome/120.0.0.0 Safari/537.36"
                                )
                            }
                        },
                        max_retries=3,
                        retry_delay=1.0,
                    )
                    status_code = response.status_code
                except Exception as e:
                    return {"success": False, "error": f"预请求失败: {e}"}

                try:
                    response = retry_call(
                        requests.get,
                        args=(self.url,),
                        kwargs={
                            "timeout": self.timeout,
                            "headers": {
                                "User-Agent": (
                                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                    "AppleWebKit/537.36"
                                )
                            }
                        },
                        max_retries=3,
                        retry_delay=1.0,
                    )
                    html = response.text
                    soup = BeautifulSoup(html, "html.parser")
                except Exception as e:
                    return {"success": False, "error": f"页面获取失败: {e}"}

            # 分析页面结构
            sections = self._analyze_sections(soup)

            # 分析资源
            resources = self._analyze_resources(soup, self.url)

            # 检测登录需求
            login_info = self._detect_login(soup, html)

            # 生成检查点
            check_points = self._generate_check_points(sections, resources)

            # 生成计划文档
            plan = self._generate_plan_document(
                status_code, sections, resources, login_info, check_points
            )

            return {
                "success": True,
                "plan": plan,
                "login_required": login_info["type"],
                "check_points": check_points,
                "sections": sections,
                "resources": resources,
            }
        except Exception as e:
            return {"success": False, "error": f"分析失败: {e}"}

    def _analyze_sections(self, soup):
        """分析页面主要区块"""
        sections = []

        # 常见区块选择器
        section_selectors = [
            ("header", ["header", '[role="banner"]', ".header", "#header"]),
            ("nav", ["nav", '[role="navigation"]', ".nav", "#nav", ".navbar"]),
            ("main", ["main", '[role="main"]', ".main", "#main", ".content"]),
            ("sidebar", ["aside", '[role="complementary"]', ".sidebar", "#sidebar"]),
            ("footer", ["footer", '[role="contentinfo"]', ".footer", "#footer"]),
            ("article", ["article", ".article", ".post", ".entry"]),
        ]

        for name, selectors in section_selectors:
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    elem = elements[0]
                    sections.append({
                        "name": name,
                        "selector": selector,
                        "tag": elem.name,
                        "node_count": len(list(elem.descendants)),
                        "depth": self._get_depth(elem),
                        "text_preview": elem.get_text(strip=True)[:100],
                    })
                    break

        # 如果没找到任何区块，记录 body
        if not sections and soup.body:
            sections.append({
                "name": "body",
                "selector": "body",
                "tag": "body",
                "node_count": len(list(soup.body.descendants)),
                "depth": self._get_depth(soup.body),
                "text_preview": soup.body.get_text(strip=True)[:100],
            })

        return sections

    def _get_depth(self, element):
        """计算 DOM 深度"""
        depth = 0
        current = element
        while current.parent:
            depth += 1
            current = current.parent
        return depth

    def _analyze_resources(self, soup, base_url):
        """分析外部资源"""
        from urllib.parse import urljoin

        resources = {
            "css": [],
            "js": [],
            "images": [],
            "fonts": [],
            "other": [],
        }

        # CSS
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if href:
                resources["css"].append(urljoin(base_url, href))

        # JS
        for script in soup.find_all("script", src=True):
            src = script.get("src")
            if src:
                resources["js"].append(urljoin(base_url, src))

        # Images
        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                resources["images"].append(urljoin(base_url, src))

        # Background images in style attributes
        for elem in soup.find_all(style=True):
            style = elem.get("style", "")
            urls = re.findall(r'url\(["\']?([^"\')]+)', style)
            for u in urls:
                resources["images"].append(urljoin(base_url, u))

        # Fonts (preload)
        for link in soup.find_all("link", rel="preload"):
            if link.get("as") == "font":
                href = link.get("href")
                if href:
                    resources["fonts"].append(urljoin(base_url, href))

        return resources

    def _detect_login(self, soup, html):
        """检测登录需求"""
        info = {"type": "none", "reason": ""}

        # 检测密码输入框
        password_inputs = soup.find_all("input", {"type": "password"})
        if password_inputs:
            info["type"] = "password"
            info["reason"] = "页面包含密码输入框"
            return info

        # 检测验证码
        captcha_keywords = ["captcha", "verify", "verification", "验证码"]
        for kw in captcha_keywords:
            if kw in html.lower():
                info["type"] = "captcha"
                info["reason"] = f"页面包含验证码关键词: {kw}"
                return info

        # 检测登录表单
        forms = soup.find_all("form")
        for form in forms:
            action = form.get("action", "").lower()
            if any(kw in action for kw in ["login", "signin", "auth"]):
                info["type"] = "password"
                info["reason"] = f"表单 action 指向登录: {action}"
                return info

        # 检测登录提示文本
        login_keywords = ["login", "sign in", "signin", "登录", "登入"]
        text = soup.get_text(strip=True).lower()
        for kw in login_keywords:
            if kw in text:
                info["type"] = "password"
                info["reason"] = f"页面包含登录提示: {kw}"
                return info

        return info

    def _generate_check_points(self, sections, resources):
        """生成验证检查点"""
        check_points = []

        # 结构检查点
        for section in sections:
            check_points.append({
                "id": f"struct_{section['name']}",
                "category": "structure",
                "description": f"区块 '{section['name']}' 存在且结构完整",
                "selector": section["selector"],
                "weight": 0.15,
            })

        # 资源检查点
        if resources["css"]:
            check_points.append({
                "id": "res_css",
                "category": "resource",
                "description": f"CSS 资源下载成功 ({len(resources['css'])} 个)",
                "weight": 0.10,
            })

        if resources["images"]:
            check_points.append({
                "id": "res_images",
                "category": "resource",
                "description": f"图片资源下载成功 ({len(resources['images'])} 个)",
                "weight": 0.10,
            })

        # 样式检查点
        check_points.append({
            "id": "style_colors",
            "category": "style",
            "description": "主要颜色方案保持一致",
            "weight": 0.15,
        })
        check_points.append({
            "id": "style_layout",
            "category": "style",
            "description": "页面布局结构保持一致",
            "weight": 0.15,
        })
        check_points.append({
            "id": "style_fonts",
            "category": "style",
            "description": "字体样式保持一致",
            "weight": 0.10,
        })

        # 交互检查点
        check_points.append({
            "id": "interact_buttons",
            "category": "interaction",
            "description": "按钮/链接元素完整",
            "weight": 0.10,
        })
        check_points.append({
            "id": "interact_forms",
            "category": "interaction",
            "description": "表单元素完整",
            "weight": 0.10,
        })

        # 静态冻结检查点（防 SPA 二次渲染污染：app.js 等渲染脚本必须已中和）
        check_points.append({
            "id": "static_freeze",
            "category": "resource",
            "description": "渲染脚本已中和（app.js 等不会二次渲染）",
            "weight": 0.10,
        })

        # 视觉验收检查点（Playwright 真实浏览器打开样式验证，相似度 ≥ 阈值）
        check_points.append({
            "id": "visual_similarity",
            "category": "visual",
            "description": "Playwright 打开样式验证（视觉相似度 ≥ 阈值）",
            "weight": 0.20,
        })

        return check_points

    def _generate_plan_document(self, status_code, sections, resources, login_info, check_points):
        """生成计划文档 Markdown"""
        lines = [
            "# 复原计划",
            "",
            f"## 目标页面",
            f"- URL: {self.url}",
            f"- 域名: {self.domain}",
            f"- HTTP 状态: {status_code}",
            "",
            "## 页面结构分析",
            "",
            "| 区块 | 选择器 | 标签 | 节点数 | 深度 |",
            "|------|--------|------|--------|------|",
        ]

        for s in sections:
            lines.append(
                f"| {s['name']} | `{s['selector']}` | {s['tag']} | {s['node_count']} | {s['depth']} |"
            )

        lines.extend([
            "",
            "## 外部资源清单",
            "",
            f"### CSS ({len(resources['css'])} 个)",
        ])
        for css in resources["css"][:10]:
            lines.append(f"- `{css}`")
        if len(resources["css"]) > 10:
            lines.append(f"- ... 共 {len(resources['css'])} 个")

        lines.extend([
            "",
            f"### JS ({len(resources['js'])} 个)",
        ])
        for js in resources["js"][:10]:
            lines.append(f"- `{js}`")
        if len(resources["js"]) > 10:
            lines.append(f"- ... 共 {len(resources['js'])} 个")

        lines.extend([
            "",
            f"### Images ({len(resources['images'])} 个)",
        ])
        for img in resources["images"][:10]:
            lines.append(f"- `{img}`")
        if len(resources["images"]) > 10:
            lines.append(f"- ... 共 {len(resources['images'])} 个")

        lines.extend([
            "",
            "## 登录需求检测",
            f"- 类型: **{login_info['type']}**",
        ])
        if login_info["reason"]:
            lines.append(f"- 原因: {login_info['reason']}")

        lines.extend([
            "",
            "## 验证检查点",
            "",
            "| ID | 类别 | 描述 | 权重 |",
            "|----|------|------|------|",
        ])
        for cp in check_points:
            lines.append(
                f"| {cp['id']} | {cp['category']} | {cp['description']} | {cp['weight']:.0%} |"
            )

        lines.extend([
            "",
            "## 风险评估",
            "- 反爬机制: 未知，如遇到限制需调整策略",
            "- 动态内容: JS 渲染的内容可能无法完整抓取",
            "- 登录依赖: 如需登录，需提供有效凭证",
            "",
            "## 执行策略",
            "1. 使用 requests 获取原始 HTML",
            "2. 解析并下载所有外部资源",
            "3. 清洗广告和追踪脚本",
            "4. 改写路径为相对路径",
            "5. 生成单文件和多文件两个版本",
            "6. 按检查点逐项验证",
            "",
            "---",
            "*生成时间: 自动*",
        ])

        return "\n".join(lines)
