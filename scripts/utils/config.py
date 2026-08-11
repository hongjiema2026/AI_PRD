#!/usr/bin/env python3
"""
统一配置加载器
职责：读取 project.yaml 并提供带默认值的访问接口
"""

import os

import yaml
from pathlib import Path
from typing import Any, Optional

_PROJECT_ROOT = Path(os.environ.get("PM_PROJECT_ROOT") or Path(__file__).resolve().parent.parent.parent).resolve()
_CONFIG_PATH = _PROJECT_ROOT / "config" / "project.yaml"

_config_cache: Optional[dict] = None
_config_cache_root: Optional[Path] = None


def _load_config() -> dict:
    """加载配置文件（带缓存；PM_PROJECT_ROOT 切换时自动失效）"""
    global _config_cache, _config_cache_root
    if _config_cache is not None and _config_cache_root == _PROJECT_ROOT:
        return _config_cache

    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = yaml.safe_load(f) or {}
    else:
        _config_cache = {}
    _config_cache_root = _PROJECT_ROOT

    return _config_cache


def reload_config():
    """强制重新加载配置"""
    global _config_cache, _config_cache_root
    _config_cache = None
    _config_cache_root = None
    return _load_config()


def get(key_path: str, default: Any = None) -> Any:
    """
    通过点分路径读取配置值

    用法:
        get("version.current") -> "v0.1.0"
        get("rules.max_retry", 3) -> 3
    """
    config = _load_config()
    keys = key_path.split(".")
    value = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value


def get_max_retry() -> int:
    """获取最大重试次数"""
    return get("rules.max_retry", 3)


def get_task_timeout_minutes() -> int:
    """获取任务超时时间（分钟）"""
    return get("rules.task_timeout_minutes", 10)


def get_crawler_timeout_seconds() -> int:
    """获取爬虫请求超时时间（秒）"""
    return get("restore.timeout_seconds", 30)


def get_max_resource_size_mb() -> float:
    """获取单个资源下载大小限制（MB）"""
    return get("restore.max_resource_size_mb", 10.0)


def get_allowed_resource_types() -> list:
    """获取允许下载的资源类型"""
    return get("restore.allowed_resource_types", [
        "css", "js", "png", "jpg", "jpeg", "gif", "svg", "ico",
        "webp", "woff", "woff2", "ttf", "eot", "otf",
    ])


def get_noise_selectors() -> list:
    """获取噪声选择器列表"""
    return get("restore.noise_selectors", [
        ".ad", ".ads", "[id*='ad-']", "[class*='advertisement']",
        "script[src*='google-analytics']", "script[src*='gtag']",
        "script[src*='facebook']", "script[src*='pixel']", "noscript",
    ])


def get_freeze_render_scripts() -> bool:
    """是否启用静态冻结（中和 SPA 渲染脚本，防止本地打开时二次渲染污染）。

    默认 True：即使老配置无此字段，新行为也自动生效。
    Playwright 抓取的是 Vue/React 渲染后的 DOM 快照；若保留 app.js 等渲染脚本，
    本地打开时框架会重新挂载 #app，因无后端 API/路由守卫/登录态导致白屏或样式错乱。
    关闭则恢复旧行为（保留渲染脚本）。
    """
    return get("restore.static_freeze.enabled", True)


def get_freeze_patterns() -> list:
    """获取渲染脚本匹配关键词列表（作为 src basename 的 stem 前缀）。

    匹配规则：取 src 的 basename，去掉扩展名得到 stem，若 stem 以任一关键词开头则视为渲染脚本。
    这样能兼容 webpack 加 hash 后的文件名（如 app_454640250ac3b3e5.js 的 stem 以 app 开头）。
    """
    return get("restore.static_freeze.render_script_patterns", [
        "app",        # Vue/React 主入口（webpack 编译的业务代码）
        "runtime",    # webpack 运行时
        "chunk-",     # webpack 异步 chunk（chunk-libs/chunk-elementUI 等）
    ])


def is_render_script(src: str, patterns: list) -> bool:
    """判断一个 script src 是否为渲染脚本（供 crawler 和 verifier 共用，保证判定一致）。

    Args:
        src: script 标签的 src 值（可能是 /static/js/app.js 或 assets/js/app_454640250ac3b3e5.js）
        patterns: get_freeze_patterns() 返回的关键词列表

    判定规则：取 src 的 basename，去扩展名得到 stem，再按以下规则匹配每个 pattern：
      - 若 pattern 以 '-' 结尾（如 'chunk-'）：stem 以该 pattern 开头即命中（前缀族）
      - 否则（如 'app'、'runtime'）：stem 去掉 hash 后缀（首个 '_' 起的部分）精确等于 pattern
        （兼容 app.js → app、app_454640250ac3b3e5.js → app；排除 application_form.js）
    """
    if not src or not patterns:
        return False
    # 取 basename（URL 的最后路径段，去掉 query）
    basename = src.split("/")[-1].split("?")[0]
    # 去 .js / .mjs 等扩展名得到 stem
    stem = basename.rsplit(".", 1)[0] if "." in basename else basename
    # 去 webpack hash 后缀：首个 '_' 起的部分（app_4546... → app）
    stem_base = stem.split("_", 1)[0] if "_" in stem else stem

    for p in patterns:
        if p.endswith("-"):
            # 前缀族（如 chunk-）：保留宽松前缀匹配
            if stem.startswith(p):
                return True
        else:
            # 精确匹配：去 hash 后的 stem 等于 pattern
            if stem_base == p:
                return True
    return False


def get_remove_preload_scripts() -> bool:
    """是否移除 head 中触发 JS 预加载的 <link rel="preload" as="script">。

    仅影响 script 类型 preload，不影响 font/image preload。默认 True。
    """
    return get("restore.static_freeze.remove_preload_scripts", True)


def get_visual_verification_enabled() -> bool:
    """是否启用 Playwright 视觉验收（真实浏览器打开样式验证）。

    默认 True：用 Playwright 截原始线上页面与本地复原页面对比，相似度需达阈值。
    """
    return get("restore.visual_verification.enabled", True)


def get_visual_threshold() -> float:
    """视觉相似度通过阈值（%），低于则 FAIL。默认 95。"""
    return get("restore.visual_verification.threshold", 95)


def get_visual_full_page() -> bool:
    """是否整页全截（true=整页，false=仅首屏视口）。默认 True。"""
    return get("restore.visual_verification.full_page", True)


def get_current_version() -> str:
    """获取当前版本号"""
    return get("version.current", "v0.1.0")


def get_playwright_mode() -> str:
    """获取页面获取模式: requests | playwright | auto"""
    return get("restore.playwright.mode", "auto")


def get_playwright_page_load_wait() -> float:
    """获取 Playwright 页面加载等待时间（秒）"""
    return get("restore.playwright.page_load_wait", 3.0)


def get_playwright_headless() -> bool:
    """是否无头模式运行浏览器（默认 False：有头，便于首次手动登录）"""
    return get("restore.playwright.headless", False)


def get_playwright_user_data_dir() -> str:
    """获取 Playwright 持久化浏览器 profile 目录（登录态随其持久化）"""
    return get(
        "restore.playwright.user_data_dir",
        "~/.cache/pm-restore-browser-profile",
    )


def get_project_root() -> Path:
    """获取项目根目录"""
    return _PROJECT_ROOT


