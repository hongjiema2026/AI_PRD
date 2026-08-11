#!/usr/bin/env python3
"""
复原验证模块
职责：对比原始页面和复原页面，按检查点逐项验证
"""

import base64
import json
import re
import threading
import http.server
import socketserver
import requests
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

import sys
from pathlib import Path
# Add utils to path
_utils_dir = str(Path(__file__).parent.parent / "utils")
if _utils_dir not in sys.path:
    sys.path.insert(0, _utils_dir)
from utils.retry import retry_call
from utils.config import (
    get_freeze_patterns,
    is_render_script,
    get_visual_verification_enabled,
    get_visual_threshold,
    get_visual_full_page,
)

from auth_handler import AuthHandler


class RestoreVerifier:
    """复原质量验证器"""

    def __init__(self, original_url, restored_dir, check_points,
                 username=None, password=None, cookie=None, fetcher=None):
        self.original_url = original_url
        self.restored_dir = Path(restored_dir)
        self.check_points = check_points
        self.username = username
        self.password = password
        self.cookie = cookie
        self.fetcher = fetcher
        self.results = []
        # 视觉验收状态：None=未执行/不适用，float=分数（0-100），"pending"=待主会话回填
        self.visual_score = None
        self.visual_status = "skipped"  # skipped / pending / passed / failed
        self.visual_detail = ""

    def run(self):
        """执行验证"""
        # 获取原始页面
        if self.fetcher:
            # Playwright 模式：使用渲染后 HTML 作为对比基准
            try:
                original_html = self.fetcher.fetch_html(self.original_url)
                original_soup = BeautifulSoup(original_html, "html.parser")
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Playwright 获取原始页面失败: {e}",
                    "report": f"# 验证报告\n\n[ERROR] {e}",
                }
        else:
            # requests 模式（原有逻辑）
            session = requests.Session()
            session.headers.update({
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36"
                ),
            })

            if self.username or self.cookie:
                auth = AuthHandler(session)
                auth.login(
                    url=self.original_url,
                    username=self.username,
                    password=self.password,
                    cookie=self.cookie,
                )

            try:
                resp = retry_call(
                    session.get,
                    args=(self.original_url,),
                    kwargs={"timeout": 30},
                    max_retries=3,
                    retry_delay=1.0,
                )
                resp.raise_for_status()
                original_html = resp.text
                original_soup = BeautifulSoup(original_html, "html.parser")
            except Exception as e:
                return {
                    "success": False,
                    "error": f"无法获取原始页面: {e}",
                    "report": f"# 验证报告\n\n[ERROR] {e}",
                }

        # 获取复原 HTML
        restored_html_path = self.restored_dir / "index.html"
        if not restored_html_path.exists():
            return {
                "success": False,
                "error": "复原文件不存在",
                "report": "# 验证报告\n\n[ERROR] 复原文件不存在",
            }

        restored_html = restored_html_path.read_text(encoding="utf-8")
        restored_soup = BeautifulSoup(restored_html, "html.parser")

        # 执行各项检查
        dom_score = self._check_dom_structure(original_soup, restored_soup)
        style_score = self._check_styles(original_soup, restored_soup)
        resource_score = self._check_resources()
        interact_score = self._check_interactions(original_soup, restored_soup)

        # 视觉验收：Playwright 截两张图并产出对比任务文件（供主会话调 MCP 回填分数）
        self._capture_visual_baselines()

        # 按检查点评估
        passed = 0
        for cp in self.check_points:
            cp_result = self._evaluate_check_point(
                cp, dom_score, style_score, resource_score, interact_score,
                original_soup, restored_soup
            )
            self.results.append(cp_result)
            if cp_result["passed"]:
                passed += 1

        total = len(self.check_points)
        match_score = (
            dom_score * 0.30 +
            style_score * 0.30 +
            resource_score * 0.20 +
            interact_score * 0.20
        )

        # 生成报告
        report = self._generate_report(
            dom_score, style_score, resource_score, interact_score,
            match_score, passed, total
        )

        return {
            "success": True,
            "match_score": match_score,
            "dom_score": dom_score,
            "style_score": style_score,
            "resource_score": resource_score,
            "interact_score": interact_score,
            "passed": passed,
            "total": total,
            "report": report,
        }

    def _check_dom_structure(self, original, restored):
        """检查 DOM 结构匹配度"""
        # 统计标签分布
        def get_tag_stats(soup):
            stats = {}
            for tag in soup.find_all(True):
                name = tag.name
                stats[name] = stats.get(name, 0) + 1
            return stats

        orig_stats = get_tag_stats(original)
        rest_stats = get_tag_stats(restored)

        # 计算匹配度
        all_tags = set(orig_stats.keys()) | set(rest_stats.keys())
        if not all_tags:
            return 100.0

        total_diff = 0
        total_count = 0
        for tag in all_tags:
            o = orig_stats.get(tag, 0)
            r = rest_stats.get(tag, 0)
            total_count += max(o, r)
            total_diff += abs(o - r)

        if total_count == 0:
            return 100.0

        match = (1 - total_diff / total_count) * 100
        return max(0, min(100, match))

    def _check_styles(self, original, restored):
        """检查样式匹配度"""
        # 提取关键样式属性
        def extract_styles(soup):
            styles = {
                "colors": set(),
                "fonts": set(),
                "font_sizes": set(),
            }

            # 从 style 标签提取
            for style_tag in soup.find_all("style"):
                css = style_tag.get_text()
                # 提取颜色
                colors = re.findall(r'#[0-9a-fA-F]{3,8}\b', css)
                styles["colors"].update(colors)
                colors_rgb = re.findall(r'rgb\([^)]+\)', css)
                styles["colors"].update(colors_rgb)
                # 提取字体
                fonts = re.findall(r'font-family\s*:\s*([^;]+)', css)
                for f in fonts:
                    styles["fonts"].update(f.strip().replace("'", "").replace('"', "").split(","))
                # 提取字号
                sizes = re.findall(r'font-size\s*:\s*([^;]+)', css)
                styles["font_sizes"].update(sizes)

            # 从内联 style 提取
            for elem in soup.find_all(style=True):
                style = elem.get("style", "")
                colors = re.findall(r'color\s*:\s*([^;]+)', style)
                styles["colors"].update(colors)
                fonts = re.findall(r'font-family\s*:\s*([^;]+)', style)
                for f in fonts:
                    styles["fonts"].update(f.strip().replace("'", "").replace('"', "").split(","))

            return styles

        orig_styles = extract_styles(original)
        rest_styles = extract_styles(restored)

        # 计算各维度匹配度
        scores = []
        for key in ["colors", "fonts", "font_sizes"]:
            orig_set = orig_styles[key]
            rest_set = rest_styles[key]
            if not orig_set:
                continue
            intersection = len(orig_set & rest_set)
            union = len(orig_set | rest_set)
            if union > 0:
                scores.append(intersection / union * 100)

        return sum(scores) / len(scores) if scores else 50.0

    def _check_resources(self):
        """检查资源完整性

        按"复原 HTML 中资源引用的本地化比例"计分：
        - 扫描 index.html 中所有 src/href/url() 引用
        - 本地化 = 指向 assets/ 相对路径 或 data: 内联
        - 外部残留 = 指向 http(s) 或 /绝对路径（未下载/未改写）
        - resource_score = 本地化数 / 总引用数 × 100
        这种方式直接反映"页面打开时有多少资源能加载"，避免目录有无文件的误判。
        """
        index_html = self.restored_dir / "index.html"
        if not index_html.exists():
            return 0.0

        try:
            content = index_html.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return 0.0

        # 收集所有资源引用（src / href / url()）
        refs = set()

        # <tag src="..."> / <tag href="...">
        for m in re.finditer(r'(?:src|href)\s*=\s*"([^"]+)"', content):
            refs.add(m.group(1).strip())

        # CSS url(...)（含 @font-face、background-image 等）
        for m in re.finditer(r'url\(\s*[\'"]?([^\'")]+)[\'"]?\s*\)', content):
            refs.add(m.group(1).strip())

        # 过滤掉非资源引用（锚点 #、协议头 //w3.org、meta 属性等）
        resource_exts = (
            ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg",
            ".webp", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".otf",
        )
        resource_refs = {
            r for r in refs
            if r and not r.startswith("#")
            and not r.startswith("data:")
            and any(r.lower().split("?")[0].endswith(ext) for ext in resource_exts)
        }

        if not resource_refs:
            # 页面无资源引用（纯静态），视为完整
            return 100.0

        local_count = sum(
            1 for r in resource_refs
            if r.startswith("assets/") or r.startswith("./assets/")
        )
        return local_count / len(resource_refs) * 100.0

    def _check_interactions(self, original, restored):
        """检查交互元素完整性"""
        def count_interactive(soup):
            counts = {
                "buttons": len(soup.find_all("button")),
                "links": len(soup.find_all("a", href=True)),
                "inputs": len(soup.find_all("input")),
                "forms": len(soup.find_all("form")),
                "selects": len(soup.find_all("select")),
            }
            return counts

        orig_counts = count_interactive(original)
        rest_counts = count_interactive(restored)

        scores = []
        for key in orig_counts:
            o = orig_counts[key]
            r = rest_counts.get(key, 0)
            if o > 0:
                ratio = min(r / o, 1.0)
                scores.append(ratio * 100)
            else:
                scores.append(100.0)

        return sum(scores) / len(scores) if scores else 100.0

    def _serve_local_for_capture(self, directory):
        """起临时 HTTP 服务托管目录，返回 (httpd, url) 供 Playwright 截图本地复原页面。

        Chrome 扩展不允许导航到 file:// URL，必须通过 http:// 托管。
        用完由调用方 httpd.shutdown() 关闭。

        Returns:
            (httpd, url): 成功时 httpd 为 socketserver 实例，url 为 http://127.0.0.1:port/
            (None, None): 起服务失败
        """
        # 找一个可用端口
        for port in range(18000, 18100):
            try:
                handler = lambda *args: http.server.SimpleHTTPRequestHandler(
                    *args, directory=directory
                )
                httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
                httpd.daemon_threads = True
                thread = threading.Thread(target=httpd.serve_forever, daemon=True)
                thread.start()
                import time as _time
                _time.sleep(0.5)  # 等服务就绪
                return httpd, f"http://127.0.0.1:{port}/"
            except OSError:
                continue  # 端口被占，换下一个
        return None, None

    def _capture_visual_baselines(self):
        """视觉验收：用 Playwright 截两张图并产出对比任务文件。

        - 截图①：原始线上页面（基准图）→ baseline_online.png
        - 截图②：本地复原 index.html（file://）→ restored_local.png
        - 两图转 base64 写入 04_visual_compare_task.json，供主会话调 MCP 对比回填分数
        - Playwright 不可用 → visual 检查点直接 FAIL（用户明确要求）
        - 视觉验收关闭 → visual 检查点 skipped
        """
        # 关闭则跳过
        if not get_visual_verification_enabled():
            self.visual_score = None
            self.visual_status = "skipped"
            self.visual_detail = "视觉验收未启用（配置 restore.visual_verification.enabled=false）"
            return

        # 检查点是否要求视觉验收（避免无谓截图）
        has_visual_cp = any(cp.get("category") == "visual" for cp in self.check_points)
        if not has_visual_cp:
            self.visual_status = "skipped"
            self.visual_detail = "本次检查点未包含视觉验收项"
            return

        # Playwright 不可用 → 直接 FAIL（用户明确要求）
        if not self.fetcher:
            self.visual_score = 0.0
            self.visual_status = "failed"
            self.visual_detail = "Playwright 不可用（未启用真实浏览器），视觉验收直接 FAIL"
            return

        # 截图①：原始线上页面（基准图）
        baseline_path = self.restored_dir / "baseline_online.png"
        saved_baseline = self.fetcher.capture_full_page(self.original_url, str(baseline_path))

        # 截图②：本地复原 index.html
        # Playwright 原生支持 file://；仍优先起临时 HTTP 服务托管 restored_dir，
        # 让页面内相对路径资源（css/js/img）按同源加载，截图更接近真实效果
        index_html = self.restored_dir / "index.html"
        restored_shot_path = self.restored_dir / "restored_local.png"
        http_server, local_url = self._serve_local_for_capture(str(self.restored_dir))
        restored_access_url = ""
        try:
            if http_server:
                restored_access_url = local_url
                saved_restored = self.fetcher.capture_full_page(local_url, str(restored_shot_path))
            else:
                # HTTP 服务起不来 → 降级用 file://（Playwright 支持，但相对资源可能受路径影响）
                restored_access_url = index_html.resolve().as_uri()
                saved_restored = self.fetcher.capture_full_page(restored_access_url, str(restored_shot_path))
        finally:
            if http_server:
                http_server.shutdown()

        # 任一截图失败 → FAIL
        if not saved_baseline or not Path(saved_baseline).exists():
            self.visual_score = 0.0
            self.visual_status = "failed"
            self.visual_detail = f"线上基准图截取失败: {self.original_url}"
            return
        if not saved_restored or not Path(saved_restored).exists():
            self.visual_score = 0.0
            self.visual_status = "failed"
            self.visual_detail = f"本地复原图截取失败（HTTP 服务托管 index.html）"
            return

        # 两图转 base64，写入对比任务文件供主会话调 MCP
        try:
            baseline_b64 = base64.b64encode(
                Path(saved_baseline).read_bytes()
            ).decode("ascii")
            restored_b64 = base64.b64encode(
                Path(saved_restored).read_bytes()
            ).decode("ascii")
        except Exception as e:
            self.visual_score = 0.0
            self.visual_status = "failed"
            self.visual_detail = f"截图转 base64 失败: {e}"
            return

        threshold = get_visual_threshold()
        task = {
            "task": "visual_similarity_compare",
            "baseline_image": str(saved_baseline),
            "restored_image": str(saved_restored),
            "baseline_b64": baseline_b64,
            "restored_b64": restored_b64,
            "original_url": self.original_url,
            "local_access_url": restored_access_url,
            "full_page": get_visual_full_page(),
            "threshold": threshold,
            "prompt": (
                "请对比这两张网页截图的视觉相似度（基准图为线上原始页面，"
                "对比图为本地复原的静态原型）。从布局结构、配色、字体、间距、"
                "图标/图片完整性、整体视觉一致性六个维度综合判断，"
                "给出一个 0-100 的整数分数（100=完全一致）。"
                "仅关注静态视觉呈现，忽略交互行为差异。"
            ),
            "status": "pending",
            "instruction": (
                "主会话执行：读取本任务的 baseline_b64/restored_b64（或用 Read 工具读取两张 PNG 路径），"
                "调 MCP analyze_image 或直接视觉判断得到 0-100 分数，"
                f"≥{threshold} 则 PASS，< {threshold} 则 FAIL，"
                "回填到本文件 score/passed 字段，并同步更新 03_restore_verification.md 的 visual_similarity 检查点。"
            ),
        }
        task_path = self.restored_dir / "04_visual_compare_task.json"
        try:
            task_path.write_text(
                json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            self.visual_score = 0.0
            self.visual_status = "failed"
            self.visual_detail = f"任务文件写入失败: {e}"
            return

        # 截图成功但分数待主会话回填 → pending
        self.visual_score = "pending"
        self.visual_status = "pending"
        self.visual_detail = (
            f"已截取基准图与复原图，待主会话调 MCP 对比回填分数"
            f"（任务文件: {task_path.name}，阈值 {threshold}%）"
        )

    def _evaluate_check_point(self, cp, dom_score, style_score, resource_score,
                              interact_score, original, restored):
        """评估单个检查点"""
        cp_id = cp["id"]
        category = cp["category"]

        if category == "structure":
            selector = cp.get("selector", "")
            orig_found = bool(original.select(selector))
            rest_found = bool(restored.select(selector))
            passed = orig_found == rest_found
            detail = f"原始: {'存在' if orig_found else '不存在'}, 复原: {'存在' if rest_found else '不存在'}"

        elif category == "resource":
            if cp_id == "static_freeze":
                # 扫描 index.html，确认无活跃的渲染脚本引用（防二次渲染污染）
                index_html = self.restored_dir / "index.html"
                try:
                    content = index_html.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    passed = False
                    detail = "index.html 无法读取"
                else:
                    patterns = get_freeze_patterns()
                    soup_check = BeautifulSoup(content, "html.parser")
                    leaked = [
                        s.get("src", "") for s in soup_check.find_all("script", src=True)
                        if is_render_script(s.get("src", ""), patterns)
                    ]
                    passed = len(leaked) == 0
                    detail = "无残留渲染脚本" if passed else f"检测到残留: {leaked}"
            elif "css" in cp_id:
                passed = resource_score >= 80
                detail = f"资源完整性: {resource_score:.1f}%"
            elif "images" in cp_id:
                assets_dir = self.restored_dir / "assets" / "images"
                has_images = assets_dir.exists() and any(assets_dir.iterdir())
                passed = has_images
                detail = f"图片目录存在: {has_images}"
            else:
                passed = resource_score >= 70
                detail = f"资源完整性: {resource_score:.1f}%"

        elif category == "style":
            if "color" in cp_id:
                passed = style_score >= 70
                detail = f"样式匹配度: {style_score:.1f}%"
            elif "layout" in cp_id:
                passed = dom_score >= 70
                detail = f"DOM 匹配度: {dom_score:.1f}%"
            elif "font" in cp_id:
                passed = style_score >= 60
                detail = f"样式匹配度: {style_score:.1f}%"
            else:
                passed = style_score >= 70
                detail = f"样式匹配度: {style_score:.1f}%"

        elif category == "interaction":
            passed = interact_score >= 70
            detail = f"交互完整性: {interact_score:.1f}%"

        elif category == "visual":
            # 视觉验收：依据 _capture_visual_baselines 设置的状态判定
            threshold = get_visual_threshold()
            if self.visual_status == "pending":
                # 截图已成功，分数待主会话回填 → 暂不判定为通过
                passed = False
                detail = f"[待回填] {self.visual_detail}"
            elif self.visual_status == "passed":
                passed = True
                detail = f"视觉相似度: {self.visual_score:.1f}% (≥{threshold}%)"
            elif self.visual_status == "failed":
                passed = False
                if isinstance(self.visual_score, (int, float)):
                    detail = f"视觉相似度: {self.visual_score:.1f}% (<{threshold}%) — {self.visual_detail}"
                else:
                    detail = f"[FAIL] {self.visual_detail}"
            else:  # skipped
                passed = True  # 跳过时不阻塞其它检查点
                detail = f"[SKIPPED] {self.visual_detail}"

        else:
            passed = True
            detail = "未分类检查点"

        return {
            "id": cp_id,
            "category": category,
            "description": cp["description"],
            "passed": passed,
            "detail": detail,
        }

    def _generate_report(self, dom_score, style_score, resource_score,
                         interact_score, match_score, passed, total):
        """生成验证报告"""
        status = "PASS" if match_score >= 90 else ("CONDITIONAL PASS" if match_score >= 80 else "FAIL")

        lines = [
            "# 复原验证报告",
            "",
            f"## 总体评估",
            f"- **状态**: {status}",
            f"- **总匹配度**: {match_score:.1f}%",
            f"- **通过检查点**: {passed}/{total}",
            "",
            "## 分项评分",
            f"| 维度 | 得分 | 权重 |",
            f"|------|------|------|",
            f"| DOM 结构 | {dom_score:.1f}% | 30% |",
            f"| 样式匹配 | {style_score:.1f}% | 30% |",
            f"| 资源完整 | {resource_score:.1f}% | 20% |",
            f"| 交互完整 | {interact_score:.1f}% | 20% |",
        ]

        # 视觉验收维度（独立于四维加权，单独展示）
        threshold = get_visual_threshold()
        if self.visual_status == "skipped":
            lines.append(f"| 视觉验收(Playwright) | SKIPPED | 阈值 {threshold}% |")
        elif self.visual_status == "pending":
            lines.append(f"| 视觉验收(Playwright) | 待回填 | 阈值 {threshold}% |")
        elif isinstance(self.visual_score, (int, float)):
            lines.append(f"| 视觉验收(Playwright) | {self.visual_score:.1f}% | 阈值 {threshold}% |")
        else:
            lines.append(f"| 视觉验收(Playwright) | N/A | 阈值 {threshold}% |")

        lines.extend([
            "",
            "## 检查点明细",
            "",
            "| ID | 类别 | 描述 | 结果 | 详情 |",
            "|----|------|------|------|------|",
        ])

        for r in self.results:
            result_icon = "PASS" if r["passed"] else "FAIL"
            lines.append(
                f"| {r['id']} | {r['category']} | {r['description']} | {result_icon} | {r['detail']} |"
            )

        lines.extend([
            "",
            "## 判定规则",
            "- PASS: 总匹配度 >= 90%",
            "- CONDITIONAL PASS: 总匹配度 80-89%（存在已知差异）",
            "- FAIL: 总匹配度 < 80%",
            "- 视觉验收: 独立判定，相似度 < 阈值则该检查点 FAIL",
            "",
        ])

        # 视觉验收待回填时，追加主会话操作指引
        if self.visual_status == "pending":
            task_path = self.restored_dir / "04_visual_compare_task.json"
            lines.extend([
                "## ⚠️ 视觉验收待执行（需主会话介入）",
                "",
                f"Verifier 已用 Playwright 截取基准图与复原图，并产出对比任务文件：",
                f"- 任务文件: `{task_path}`",
                f"- 基准图(线上): `{self.restored_dir / 'baseline_online.png'}`",
                f"- 对比图(本地): `{self.restored_dir / 'restored_local.png'}`",
                f"- 通过阈值: **{threshold}%**",
                "",
                "**执行步骤**:",
                f"1. 读取 `{task_path.name}`（含两图 base64 + 标准提示词）",
                "2. 调用 MCP analyze_image 对比两图，或用 Read 工具直接读取两张 PNG 做视觉判断",
                "3. 得到 0-100 分数",
                f"4. ≥{threshold}% → 将本检查点结果改为 PASS；< {threshold}% → 保持 FAIL",
                f"5. 回填分数到 `{task_path.name}` 的 score/passed 字段，并更新本报告 visual_similarity 行",
                "",
            ])

        if status == "FAIL":
            lines.extend([
                "## 修复建议",
                "1. 检查是否有反爬机制导致页面获取不完整",
                "2. 尝试提供登录凭证重新复原",
                "3. 检查目标页面是否为 SPA（单页应用），可能需要使用无头浏览器",
                "4. 增加重试次数",
                "",
            ])

        lines.append("---")
        lines.append("*报告生成: 自动*")

        return "\n".join(lines)
