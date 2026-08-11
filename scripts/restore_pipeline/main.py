#!/usr/bin/env python3
"""
原型复原流水线入口
用法: python3 scripts/restore_pipeline/main.py <URL> [--version v1.0.0]

执行流程:
1. Planner 分析页面，生成复原计划
2. Crawler 抓取页面（含登录处理）
3. Verifier 验证复原质量
"""

import argparse
import logging
import sys
import yaml
from pathlib import Path
from urllib.parse import urlparse

import sys
from pathlib import Path
# Add utils to path
_utils_dir = str(Path(__file__).parent.parent / "utils")
if _utils_dir not in sys.path:
    sys.path.insert(0, _utils_dir)
from utils.config import get_current_version as config_get_current_version, get_max_retry, get_playwright_mode, get_playwright_page_load_wait

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

PROJECT_ROOT = Path(__file__).parent.parent.parent

# 使用绝对导入（运行前需确保工作目录正确，或通过 PYTHONPATH 设置）
# 推荐用法: cd 项目根目录 && PYTHONPATH=scripts/restore_pipeline python3 -m main <URL>
import importlib.util

_pipeline_dir = PROJECT_ROOT / "scripts" / "restore_pipeline"
for module_name in ["planner", "crawler", "auth_handler", "verifier", "playwright_fetcher"]:
    module_path = _pipeline_dir / f"{module_name}.py"
    if module_path.exists():
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

from planner import RestorePlanner
from crawler import RestoreCrawler
from verifier import RestoreVerifier
from playwright_fetcher import create_fetcher, PlaywrightError


def get_current_version():
    """读取当前版本"""
    return config_get_current_version()


def ensure_agent_comm_dir(version, task_id):
    """确保 Agent 通信目录存在"""
    comm_dir = PROJECT_ROOT / "versions" / version / "agent_comm" / task_id
    comm_dir.mkdir(parents=True, exist_ok=True)
    return comm_dir


def write_task_book(comm_dir, url, version):
    """生成任务书"""
    task_content = f"""---
task_id: restore_{Path(comm_dir).name}
type: prototype_restoration
status: in_progress
pipeline: [planner, crawler, verifier]
current_step: planner
---

# 任务：复原页面原型

## 输入
- URL: {url}
- 版本目标: {version}

## 上下文
- 用户意图：获取在线页面作为原型参考
- 优先级：高

## 期望输出
- 复原后的 HTML 原型文件
- 验证通过报告
"""
    task_path = comm_dir / "00_task.md"
    task_path.write_text(task_content, encoding="utf-8")
    logging.info(f"[OK] 任务书创建: {task_path}")


def main():
    parser = argparse.ArgumentParser(description="原型复原流水线")
    parser.add_argument("url", help="目标页面 URL")
    parser.add_argument("--version", help="目标版本 (默认当前版本)")
    parser.add_argument("--username", help="登录账号")
    parser.add_argument("--password", help="登录密码")
    parser.add_argument("--captcha", help="验证码")
    parser.add_argument("--cookie", help="Cookie 字符串（复杂登录场景）")
    parser.add_argument("--output-dir", help="输出目录（覆盖默认版本目录）")
    parser.add_argument(
        "--acquisition-mode",
        choices=["requests", "playwright", "auto"],
        help="页面获取模式 (默认: 从配置文件读取，或 auto)",
    )
    args = parser.parse_args()

    version = args.version or get_current_version()
    version_path = PROJECT_ROOT / "versions" / version
    if not version_path.exists():
        logging.error(f"[ERROR] 版本不存在: {version}")
        return 1

    # 生成任务ID
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = urlparse(args.url).netloc.replace(".", "_")
    task_id = f"restore_{domain}_{timestamp}"

    comm_dir = ensure_agent_comm_dir(version, task_id)
    write_task_book(comm_dir, args.url, version)

    logging.info("=== 复原流水线启动 ===")
    logging.info(f"URL: {args.url}")
    logging.info(f"版本: {version}")
    logging.info(f"任务ID: {task_id}\n")

    # 解析页面获取模式
    acquisition_mode = args.acquisition_mode or get_playwright_mode()
    try:
        fetcher = create_fetcher(
            acquisition_mode,
            session_name=f"restore-{task_id}",
            page_load_wait=get_playwright_page_load_wait(),
        )
    except PlaywrightError as e:
        logging.error(f"[ERROR] Playwright 不可用: {e}")
        return 1

    if fetcher:
        logging.info("[INFO] 使用 Playwright 获取页面 (模式: %s)", acquisition_mode)
    else:
        logging.info("[INFO] 使用 requests 获取页面 (模式: %s)", acquisition_mode)

    try:
        # ========== Step 1: Planner ==========
        logging.info("[Step 1/3] 生成复原计划...")
        planner = RestorePlanner(args.url, fetcher=fetcher)
        plan_result = planner.analyze()

        if not plan_result["success"]:
            logging.error(f"[ERROR] 计划生成失败: {plan_result.get('error')}")
            return 1

        plan_path = comm_dir / "01_restore_plan.md"
        plan_path.write_text(plan_result["plan"], encoding="utf-8")
        logging.info(f"[OK] 复原计划: {plan_path}")

        # 检查登录需求
        login_req = plan_result.get("login_required", "none")
        if login_req != "none":
            if fetcher:
                logging.info("[INFO] Playwright 持久化浏览器模式复用 profile 中已保存的登录态，跳过凭证检查")
            else:
                logging.warning(f"[NOTICE] 检测到登录需求: {login_req}")
                if args.cookie:
                    logging.info("[INFO] 将使用提供的 Cookie")
                elif args.username and args.password:
                    logging.info("[INFO] 将使用提供的账号密码")
                else:
                    logging.warning("[BLOCKED] 需要提供登录凭证")
                    logging.info("  请提供以下参数之一:")
                    logging.info("    --cookie 'your_cookie_string'")
                    logging.info("    --username xxx --password xxx [--captcha xxx]")
                    return 1

        # ========== Step 2: Crawler ==========
        logging.info("[Step 2/3] 执行页面复原...")

        output_dir = args.output_dir or str(
            version_path / "prototype" / "restored" / f"{domain}_{timestamp}"
        )

        crawler = RestoreCrawler(
            url=args.url,
            output_dir=output_dir,
            username=args.username,
            password=args.password,
            captcha=args.captcha,
            cookie=args.cookie,
            fetcher=fetcher,
        )
        crawl_result = crawler.run()

        if not crawl_result["success"]:
            logging.error(f"[ERROR] 复原失败: {crawl_result.get('error')}")
            return 1

        logging.info(f"[OK] 复原完成: {output_dir}")
        logging.info(f"  - HTML: {crawl_result.get('html_file')}")
        logging.info(f"  - 资源数: {crawl_result.get('resource_count', 0)}")

        # ========== Step 3: Verifier ==========
        logging.info("[Step 3/3] 验证复原质量...")
        verifier = RestoreVerifier(
            original_url=args.url,
            restored_dir=output_dir,
            check_points=plan_result.get("check_points", []),
            username=args.username,
            password=args.password,
            cookie=args.cookie,
            fetcher=fetcher,
        )
        verify_result = verifier.run()

        report_path = comm_dir / "03_restore_verification.md"
        report_path.write_text(verify_result["report"], encoding="utf-8")
        logging.info(f"[OK] 验证报告: {report_path}")

        # 汇总
        logging.info("=== 流水线执行完成 ===")
        logging.info(f"匹配度: {verify_result.get('match_score', 0):.1f}%")
        logging.info(f"通过检查点: {verify_result.get('passed', 0)}/{verify_result.get('total', 0)}")

        if verify_result.get("match_score", 0) >= 90:
            logging.info("[PASS] 复原质量优秀")
        elif verify_result.get("match_score", 0) >= 80:
            logging.info("[CONDITIONAL PASS] 复原质量可接受，存在已知差异")
        else:
            logging.error("[FAIL] 复原质量不达标，建议重试")
            logging.info("  可尝试: 重新运行命令，或检查目标页面是否有反爬机制")
            return 1

    finally:
        if fetcher:
            fetcher.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
