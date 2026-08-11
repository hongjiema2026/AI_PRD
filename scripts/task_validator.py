#!/usr/bin/env python3
"""任务书校验工具 — 校验 Agent 通信文件的格式和完整性。"""

import sys
import os
import re
import yaml
from datetime import datetime

VALID_TASK_TYPES = {"kb", "prd", "proto", "version", "restore", "multi"}
VALID_STATUSES = {"pending", "in_progress", "blocked", "completed", "error"}
REQUIRED_FRONTMATTER_FIELDS = {"task_id", "type", "status"}
RECOMMENDED_FIELDS = {"created_at"}  # 缺失时为 warning 而非 error

STATUS_TRANSITIONS = {
    "pending": {"in_progress", "error"},
    "in_progress": {"completed", "blocked", "error"},
    "blocked": {"in_progress", "error"},
    "completed": set(),
    "error": {"pending", "in_progress"},
}


def parse_frontmatter(filepath):
    """从 Markdown 文件中提取 YAML frontmatter。"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None, content
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        return None, content
    return meta, content


def validate_task_book(filepath):
    """校验任务书文件，返回 (errors, warnings)。"""
    errors = []
    warnings = []

    if not os.path.exists(filepath):
        return [f"文件不存在: {filepath}"], []

    meta, content = parse_frontmatter(filepath)
    if meta is None:
        return ["无法解析 YAML frontmatter"], []

    # 检查必填字段
    for field in REQUIRED_FRONTMATTER_FIELDS:
        if field not in meta:
            errors.append(f"缺少必填字段: {field}")

    # 检查建议字段
    for field in RECOMMENDED_FIELDS:
        if field not in meta:
            warnings.append(f"缺少建议字段: {field}")

    # 校验类型
    if "type" in meta and meta["type"] not in VALID_TASK_TYPES:
        errors.append(f"无效的 type 值: {meta['type']}，允许值: {VALID_TASK_TYPES}")

    # 校验状态
    if "status" in meta and meta["status"] not in VALID_STATUSES:
        errors.append(f"无效的 status 值: {meta['status']}，允许值: {VALID_STATUSES}")

    # 检查必需章节
    required_sections = ["用户原始输入", "流水线配置", "期望交付物"]
    for section in required_sections:
        if section not in content:
            warnings.append(f"缺少建议章节: {section}")

    return errors, warnings


def _parse_pipeline_from_task(content):
    """从任务书正文解析 pipeline YAML 配置，返回步骤列表。"""
    import re
    match = re.search(r"```yaml\s*\npipeline:(.*?)```", content, re.DOTALL)
    if not match:
        return []
    try:
        pipeline_yaml = "pipeline:" + match.group(1)
        parsed = yaml.safe_load(pipeline_yaml)
        return parsed.get("pipeline", []) if parsed else []
    except yaml.YAMLError:
        return []


def validate_agent_output(task_book_path, agent_name):
    """校验指定 Agent 的输出文件是否存在且包含完成标志。

    优先从任务书 pipeline[].output_file 读取实际产出路径；
    如 output_file 为空，则回退到按约定路径推断。
    """
    task_dir = os.path.dirname(task_book_path)
    errors = []

    # 检查 BLOCKED 信号
    blocked_file = os.path.join(task_dir, "BLOCKED.md")
    if os.path.exists(blocked_file):
        return [f"Agent {agent_name} 处于 BLOCKED 状态，请检查 BLOCKED.md"]

    meta, content = parse_frontmatter(task_book_path)
    if not meta:
        return ["无法读取任务书元数据"]

    task_type = meta.get("type", "")
    version_dir = task_book_path.split("/agent_comm/")[0]

    # 尝试从任务书 pipeline 配置中读取 output_file
    pipeline = _parse_pipeline_from_task(content)
    task_book_dir = os.path.dirname(os.path.abspath(task_book_path))
    # task_book_dir = prj/versions/{v}/agent_comm/{task_id}，需要往上 4 层到项目根
    project_root = os.path.abspath(os.path.join(task_book_dir, "..", "..", "..", ".."))

    explicit_outputs = []
    for step in pipeline:
        step_agent = step.get("agent", "")
        if _agent_name_match(step_agent, agent_name):
            of = step.get("output_file")
            if of and of != "null":
                # output_file 可能是逗号分隔的多个路径
                for single_path in str(of).split(","):
                    single_path = single_path.strip()
                    if not single_path:
                        continue
                    if not os.path.isabs(single_path):
                        single_path = os.path.join(project_root, single_path)
                    explicit_outputs.append(single_path)

    if explicit_outputs:
        # 使用任务书中显式声明的产出路径
        for output_file in explicit_outputs:
            if "*" in output_file:
                import glob
                matches = glob.glob(output_file)
                if not matches:
                    errors.append(f"未找到匹配文件: {output_file}")
            elif not os.path.exists(output_file):
                errors.append(f"输出文件不存在: {output_file}")
    else:
        # 回退：按约定路径推断
        expected_outputs = _get_expected_outputs(task_type, agent_name, task_dir, version_dir)
        for output_file in expected_outputs:
            if "*" in output_file:
                import glob
                matches = glob.glob(output_file)
                if not matches:
                    errors.append(f"未找到匹配文件: {output_file}")
            elif not os.path.exists(output_file):
                errors.append(f"输出文件不存在: {output_file}")

    # 检查完成标志
    completion_found = False
    for root, dirs, files in os.walk(task_dir):
        for fname in files:
            if fname.endswith(".md") and fname != "00_task.md":
                fpath = os.path.join(root, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    if f"AGENT_COMPLETE: {agent_name}" in f.read():
                        completion_found = True
                        break

    if not completion_found and not errors:
        return [f"未找到完成标志: AGENT_COMPLETE: {agent_name}"]

    return errors


def _agent_name_match(step_agent, target):
    """判断 pipeline 步骤中的 agent 名称是否匹配目标。"""
    step_agent = step_agent.lower().replace("-", "_")
    target = target.lower().replace("-", "_")
    # "prd_agent" 匹配 "prd"
    if step_agent == target or step_agent.startswith(target) or target.startswith(step_agent):
        return True
    return False


def _get_expected_outputs(task_type, agent_name, task_dir, version_dir):
    """根据任务类型和 Agent 名称返回期望的输出文件列表（回退用）。"""
    outputs = []

    if agent_name in ("prd_agent", "prd"):
        outputs.append(os.path.join(task_dir, "01_research_summary.md"))
        outputs.append(os.path.join(version_dir, "prd", "prd_*.md"))
        outputs.append(os.path.join(task_dir, "03_prd_review_report.md"))

    elif agent_name in ("proto_agent", "proto"):
        outputs.append(os.path.join(task_dir, "01_proto_architecture.md"))
        proto_dir = os.path.join(version_dir, "prototype", "pages")
        if os.path.exists(proto_dir):
            html_files = [f for f in os.listdir(proto_dir) if f.endswith(".html")]
            if not html_files:
                outputs.append(os.path.join(proto_dir, "*.html"))
        outputs.append(os.path.join(task_dir, "03_proto_test_report.md"))

    elif agent_name in ("version_agent", "version"):
        outputs.append(os.path.join(task_dir, "version_report.md"))

    elif agent_name in ("restore_agent", "restore"):
        outputs.append(os.path.join(task_dir, "01_restore_plan.md"))
        outputs.append(os.path.join(task_dir, "03_restore_verification.md"))

    elif agent_name in ("kb_agent", "kb"):
        outputs.append(os.path.join(task_dir, "kb_review_report.md"))

    return outputs


def _parse_execution_log(content):
    """从任务书正文中解析执行日志表格，返回步骤列表。"""
    steps = []
    in_log_section = False
    in_table = False
    for line in content.split("\n"):
        stripped = line.strip()
        if "执行日志" in stripped:
            in_log_section = True
            continue
        if in_log_section and stripped.startswith("#"):
            break
        if in_log_section and stripped.startswith("|"):
            # 跳过分隔行
            if set(stripped.replace("|", "").replace("-", "").replace(" ", "")) == set():
                continue
            # 跳过表头行
            if "步骤" in stripped and "Agent" in stripped:
                in_table = True
                continue
            if in_table:
                cells = [c.strip() for c in stripped.split("|")[1:-1]]
                if len(cells) >= 4:
                    steps.append({
                        "step": cells[0],
                        "agent": cells[1],
                        "status": cells[2],
                        "time": cells[3],
                    })
    return steps


def check_timeout(task_book_path, timeout_minutes=10):
    """检查当前步骤是否超时。

    优先从执行日志中获取当前 in_progress 步骤的开始时间；
    如无执行日志，回退到任务书 created_at（但仅对非 multi 类型生效）。
    """
    meta, content = parse_frontmatter(task_book_path)
    if not meta:
        return None

    if meta.get("status") in ("completed", "error"):
        return None

    # 尝试从执行日志获取当前步骤开始时间
    steps = _parse_execution_log(content)
    active_step = None
    for step in steps:
        if step["status"] == "in_progress":
            active_step = step
            break

    if active_step:
        time_str = active_step["time"]
        # 尝试多种时间格式
        step_start = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                step_start = datetime.strptime(time_str, fmt)
                break
            except ValueError:
                continue
        if step_start:
            elapsed = (datetime.now() - step_start).total_seconds() / 60
            if elapsed > timeout_minutes:
                agent_name = active_step.get("agent", "unknown")
                return f"步骤 {active_step['step']}（{agent_name}）已运行 {elapsed:.0f} 分钟，超过 {timeout_minutes} 分钟超时限制"
            return None

    # 回退：对非 multi 类型使用 created_at
    if meta.get("type") == "multi":
        return None  # multi 类型无执行日志时不做超时判断

    created_str = meta.get("created_at", "")
    if not created_str:
        return None

    try:
        created = datetime.strptime(created_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

    elapsed = (datetime.now() - created).total_seconds() / 60
    if elapsed > timeout_minutes:
        return f"任务已运行 {elapsed:.0f} 分钟，超过 {timeout_minutes} 分钟超时限制"

    return None


def main():
    if len(sys.argv) < 2:
        print("用法: python task_validator.py <command> [args]")
        print("命令:")
        print("  validate <task_book_path>          — 校验任务书格式")
        print("  check-output <task_book> <agent>    — 检查 Agent 输出")
        print("  check-timeout <task_book> [minutes] — 检查是否超时")
        print("  full-check <task_book> <agent>      — 完整校验")
        sys.exit(1)

    command = sys.argv[1]

    if command == "validate":
        task_path = sys.argv[2]
        errors, warnings = validate_task_book(task_path)
        if errors:
            print("❌ 校验失败:")
            for e in errors:
                print(f"  - {e}")
        else:
            print("✅ 任务书格式校验通过")
        if warnings:
            print("⚠️  警告:")
            for w in warnings:
                print(f"  - {w}")
        sys.exit(1 if errors else 0)

    elif command == "check-output":
        task_path = sys.argv[2]
        agent = sys.argv[3]
        errors = validate_agent_output(task_path, agent)
        if errors:
            print("❌ 输出校验失败:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        print("✅ Agent 输出校验通过")
        sys.exit(0)

    elif command == "check-timeout":
        task_path = sys.argv[2]
        timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        result = check_timeout(task_path, timeout)
        if result:
            print(f"⏰ {result}")
            sys.exit(1)
        print("✅ 未超时")
        sys.exit(0)

    elif command == "full-check":
        task_path = sys.argv[2]
        agent = sys.argv[3]

        # 1. 校验任务书
        errors, warnings = validate_task_book(task_path)
        all_errors = list(errors)

        # 2. 校验输出
        output_errors = validate_agent_output(task_path, agent)
        all_errors.extend(output_errors)

        # 3. 超时检查
        timeout_msg = check_timeout(task_path)
        if timeout_msg:
            all_errors.append(timeout_msg)

        if all_errors:
            print("❌ 完整校验失败:")
            for e in all_errors:
                print(f"  - {e}")
            sys.exit(1)

        print("✅ 完整校验通过")
        if warnings:
            print("⚠️  警告:")
            for w in warnings:
                print(f"  - {w}")
        sys.exit(0)

    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
