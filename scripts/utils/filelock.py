#!/usr/bin/env python3
"""
文件锁工具
职责：为 Agent 通信文件提供并发安全保护
"""

import os
import time
import logging
import fcntl
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30  # 等待锁的超时时间（秒）
DEFAULT_RETRY_INTERVAL = 0.1  # 重试间隔（秒）


@contextmanager
def file_lock(lock_path: str, timeout: float = DEFAULT_TIMEOUT):
    """
    基于文件的互斥锁上下文管理器

    用法:
        with file_lock("/tmp/agent_comm.lock"):
            # 在此区间内，其他进程无法获取同一锁
            write_task_file(...)

    Args:
        lock_path: 锁文件路径（通常放在 agent_comm 目录下）
        timeout: 等待锁的超时时间，超时抛出 TimeoutError
    """
    lock_file = None
    try:
        lock_dir = Path(lock_path).parent
        lock_dir.mkdir(parents=True, exist_ok=True)

        lock_file = open(lock_path, "w")
        start_time = time.time()

        while True:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (IOError, OSError):
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise TimeoutError(
                        f"获取文件锁超时 ({timeout}s): {lock_path}"
                    )
                time.sleep(DEFAULT_RETRY_INTERVAL)

        yield

    finally:
        if lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            except Exception:
                pass


@contextmanager
def task_lock(task_dir: str, timeout: float = DEFAULT_TIMEOUT):
    """
    任务级别的文件锁

    为特定任务目录提供互斥访问，防止多个 Agent 同时写同一任务目录。

    用法:
        with task_lock("versions/v0.1.0/agent_comm/restore_task_123"):
            # 安全地读写任务文件
            update_task_status(...)
    """
    lock_path = os.path.join(task_dir, ".task.lock")
    with file_lock(lock_path, timeout):
        yield


def safe_write(filepath: str, content: str, encoding: str = "utf-8",
               timeout: float = DEFAULT_TIMEOUT):
    """
    带锁的安全文件写入

    在写入前获取文件锁，写入完成后释放。适合 Agent 并发写通信文件。

    Args:
        filepath: 目标文件路径
        content: 写入内容
        encoding: 文件编码
        timeout: 锁超时时间
    """
    lock_path = filepath + ".lock"
    with file_lock(lock_path, timeout):
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(filepath, "w", encoding=encoding) as f:
            f.write(content)
    # 清理锁文件
    try:
        os.remove(lock_path)
    except OSError:
        pass


def safe_read(filepath: str, encoding: str = "utf-8",
              timeout: float = DEFAULT_TIMEOUT) -> Optional[str]:
    """
    带锁的安全文件读取

    Args:
        filepath: 目标文件路径
        encoding: 文件编码
        timeout: 锁超时时间

    Returns:
        文件内容，文件不存在时返回 None
    """
    if not os.path.exists(filepath):
        return None

    lock_path = filepath + ".lock"
    try:
        with file_lock(lock_path, timeout):
            with open(filepath, "r", encoding=encoding) as f:
                return f.read()
    except TimeoutError:
        logger.warning("读取文件超时: %s", filepath)
        return None