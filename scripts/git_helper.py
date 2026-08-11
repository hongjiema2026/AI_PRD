#!/usr/bin/env python3
"""
Git Helper — 结构化原子提交工具

为 PM-Orchestrator 的每个流水线阶段生成规范的 Git 提交，
支持精确回滚和 git bisect 调试。

命令:
  commit-task-start <task_id> <type> <version>
      创建任务启动标记提交

  commit-stage <task_id> <stage> <type> <version> [files...]
      为指定阶段创建原子提交，stage 为子角色名
      (如 research, visualize, writer, feasibility, reviewer, architect, implementer, tester)

  commit-task-complete <task_id> <type> <version>
      创建任务完成标记提交

  release <version>
      创建版本发布标签（轻量标签）

  log [count]
      显示最近的结构化提交日志（默认 20 条）

提交消息格式:
  [type](version): stage - description

  示例:
  [prd](eBay议价策略_v0.2.0): research - 完成调研摘要
  [prd](eBay议价策略_v0.2.0): visualize - 4张标准图生成完毕
  [proto](temu资质证书_v0.1.0): implement - 5个组件原型创建
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(os.environ.get("PM_PROJECT_ROOT") or Path(__file__).resolve().parent.parent).resolve()

# 有效任务类型
VALID_TYPES = {"prd", "proto", "restore", "kb", "version", "doc", "component", "diagram"}

# 有效阶段名（按流水线分组）
VALID_STAGES = {
    # PRD 流水线
    "research", "visualize", "writer", "feasibility", "reviewer", "html-render",
    # 原型流水线
    "architect", "implementer", "tester",
    # 复原流水线
    "planner", "crawler", "verifier", "kb-extractor",
    # 通用
    "init", "complete", "sync",
}


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """执行 git 命令"""
    result = subprocess.run(
        ["git"] + args,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        print(f"Git error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result


def git_add_commit(message: str, files: Optional[List[str]] = None):
    """暂存文件并提交

    服务端改造（S2）：
    - 不再 git add --all（避免跨任务提交污染），文件列表必须显式给出；
    - files 为空时视为标记提交（task-start/complete），使用 --allow-empty；
    - 指定文件无实际变更时短路跳过，不产生空提交；
    - git identity 由调用方通过 GIT_AUTHOR_NAME/EMAIL 环境变量注入。
    """
    if files:
        for f in files:
            run_git(["add", f])
        # 指定文件无实际变更则短路
        status = run_git(["status", "--porcelain", "--"] + files, check=False)
        if not status.stdout.strip():
            print(f"No changes in specified files, skip commit: {message}")
            return
        run_git(["commit", "-m", message])
    else:
        # 标记提交，允许空提交
        run_git(["commit", "--allow-empty", "-m", message])
    print(f"Committed: {message}")


def commit_task_start(task_id: str, task_type: str, version: str):
    """创建任务启动标记提交"""
    if task_type not in VALID_TYPES:
        print(f"Invalid task type: {task_type}. Valid: {', '.join(sorted(VALID_TYPES))}")
        sys.exit(1)

    message = f"[{task_type}]({version}): start - {task_id} 开始执行"
    git_add_commit(message)


def commit_stage(task_id: str, stage: str, task_type: str, version: str, files: Optional[List[str]] = None):
    """为指定阶段创建原子提交"""
    if stage not in VALID_STAGES:
        print(f"Warning: '{stage}' not in standard stages. Proceeding anyway.")

    if task_type not in VALID_TYPES:
        print(f"Invalid task type: {task_type}. Valid: {', '.join(sorted(VALID_TYPES))}")
        sys.exit(1)

    # 阶段描述映射
    stage_descriptions = {
        "research": "完成调研摘要",
        "visualize": "图表生成完毕",
        "writer": "PRD 文档编写完成",
        "feasibility": "可行性验证完成",
        "reviewer": "评审通过",
        "html-render": "HTML 渲染完成",
        "architect": "原型设计文档完成",
        "implementer": "组件原型实现完成",
        "tester": "原型测试完成",
        "planner": "复原计划完成",
        "crawler": "页面爬取完成",
        "verifier": "复原验证完成",
        "kb-extractor": "知识提取完成",
        "init": "初始化完成",
        "complete": "任务完成",
        "sync": "同步更新",
    }

    desc = stage_descriptions.get(stage, stage)
    message = f"[{task_type}]({version}): {stage} - {desc}"
    git_add_commit(message, files)


def commit_task_complete(task_id: str, task_type: str, version: str):
    """创建任务完成标记提交"""
    if task_type not in VALID_TYPES:
        print(f"Invalid task type: {task_type}. Valid: {', '.join(sorted(VALID_TYPES))}")
        sys.exit(1)

    message = f"[{task_type}]({version}): complete - {task_id} 任务完成"
    git_add_commit(message)


def release(version: str):
    """创建版本发布标签"""
    tag_name = f"release/{version}"

    # 检查标签是否已存在
    result = run_git(["tag", "-l", tag_name], check=False)
    if result.stdout.strip():
        print(f"Tag already exists: {tag_name}")
        sys.exit(1)

    # 创建标签
    run_git(["tag", tag_name])
    print(f"Created tag: {tag_name}")


def log(count: int = 20):
    """显示结构化提交日志"""
    result = run_git([
        "log",
        f"-{count}",
        "--pretty=format:%h | %ai | %s",
        "--no-merges",
    ], check=False)
    print(result.stdout)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "commit-task-start":
        if len(sys.argv) < 5:
            print("Usage: git_helper.py commit-task-start <task_id> <type> <version>")
            sys.exit(1)
        commit_task_start(sys.argv[2], sys.argv[3], sys.argv[4])

    elif command == "commit-stage":
        if len(sys.argv) < 6:
            print("Usage: git_helper.py commit-stage <task_id> <stage> <type> <version> [files...]")
            sys.exit(1)
        files = sys.argv[6:] if len(sys.argv) > 6 else None
        commit_stage(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], files)

    elif command == "commit-task-complete":
        if len(sys.argv) < 5:
            print("Usage: git_helper.py commit-task-complete <task_id> <type> <version>")
            sys.exit(1)
        commit_task_complete(sys.argv[2], sys.argv[3], sys.argv[4])

    elif command == "release":
        if len(sys.argv) < 3:
            print("Usage: git_helper.py release <version>")
            sys.exit(1)
        release(sys.argv[2])

    elif command == "log":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        log(count)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
