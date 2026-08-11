"""测试通用 fixtures"""
import os
import sys
import shutil
import tempfile
import pytest
from pathlib import Path

# 确保项目根目录在 path 中
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "utils"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "restore_pipeline"))


@pytest.fixture
def tmp_project(tmp_path):
    """创建临时项目目录结构"""
    dirs = [
        "versions/v0.1.0/prd",
        "versions/v0.1.0/prototype/pages",
        "versions/v0.1.0/prototype/components",
        "versions/v0.1.0/prototype/assets/css",
        "versions/v0.1.0/prototype/assets/js",
        "versions/v0.1.0/prototype/assets/images",
        "versions/v0.1.0/agent_comm",
        "versions/archive",
        "config",
        "docs/knowledge-base/user-research",
        "docs/knowledge-base/competitor",
        "templates",
    ]
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)

    # 创建基础配置文件
    import yaml
    config = {
        "project": {"name": "Test-Project", "description": "测试项目", "created_at": "2026-04-28"},
        "version": {"current": "v0.1.0", "latest_release": None, "scheme": "semver"},
        "rules": {"max_retry": 3, "task_timeout_minutes": 10},
        "restore": {
            "timeout_seconds": 30,
            "max_resource_size_mb": 10,
            "allowed_resource_types": ["css", "js", "png", "jpg"],
            "noise_selectors": [".ad", ".ads"],
        },
    }
    config_path = tmp_path / "config" / "project.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    return tmp_path


@pytest.fixture
def sample_html():
    """返回一个简单的 HTML 页面字符串"""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>测试页面</title>
    <link rel="stylesheet" href="https://example.com/style.css">
    <style>
        body { color: #333; font-family: Arial, sans-serif; font-size: 14px; }
        .header { background: #fff; border-bottom: 1px solid #eee; }
    </style>
</head>
<body>
    <header class="header">
        <nav><a href="/home">首页</a><a href="/about">关于</a></nav>
    </header>
    <main>
        <h1>测试标题</h1>
        <p>测试内容</p>
        <form action="/submit" method="post">
            <input type="text" name="username" placeholder="用户名">
            <input type="password" name="password" placeholder="密码">
            <button type="submit">提交</button>
        </form>
    </main>
    <footer>版权所有</footer>
    <div class="ad">广告内容</div>
    <script src="https://example.com/app.js"></script>
</body>
</html>"""


@pytest.fixture
def sample_task_md(tmp_path):
    """创建一个示例任务书文件"""
    task_content = """---
task_id: test_task_001
type: prd
status: in_progress
created_at: "2026-04-28 10:00:00"
---

# 任务书 — 测试任务

## 用户原始输入
请帮我写一份 PRD

## 流水线配置

```yaml
pipeline:
  - agent: prd_agent
    step: 01
    status: completed
    output_file: null
  - agent: proto_agent
    step: 02
    status: in_progress
    output_file: null
```

## 期望交付物
1. PRD 文档

## 执行日志

| 步骤 | Agent | 状态 | 时间 | 备注 |
|------|-------|------|------|------|
| 01 | prd_agent | completed | 2026-04-28 10:01:00 | - |
| 02 | proto_agent | in_progress | 2026-04-28 10:05:00 | - |
"""
    task_path = tmp_path / "00_task.md"
    task_path.write_text(task_content, encoding="utf-8")
    return str(task_path)