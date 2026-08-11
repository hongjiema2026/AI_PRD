"""测试 filelock 模块"""
import pytest
import os
import sys
import time
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "utils"))

from filelock import file_lock, task_lock, safe_write, safe_read


class TestFileLock:
    """文件锁测试"""

    def test_basic_lock(self, tmp_path):
        """基本加锁"""
        lock_path = str(tmp_path / "test.lock")
        with file_lock(lock_path):
            assert os.path.exists(lock_path)

    def test_lock_is_released(self, tmp_path):
        """锁释放后可再次获取"""
        lock_path = str(tmp_path / "test.lock")
        with file_lock(lock_path):
            pass
        with file_lock(lock_path, timeout=1):
            pass  # 不应超时

    def test_concurrent_access(self, tmp_path):
        """并发访问测试"""
        lock_path = str(tmp_path / "test.lock")
        counter_file = tmp_path / "counter.txt"
        counter_file.write_text("0")

        results = []
        errors = []

        def increment():
            try:
                with file_lock(lock_path, timeout=5):
                    val = int(counter_file.read_text())
                    time.sleep(0.01)  # 模拟耗时操作
                    counter_file.write_text(str(val + 1))
                    results.append(val)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=increment) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert int(counter_file.read_text()) == 5


class TestTaskLock:
    """任务级锁测试"""

    def test_task_lock(self, tmp_path):
        """任务目录锁"""
        task_dir = str(tmp_path / "task_001")
        os.makedirs(task_dir, exist_ok=True)
        with task_lock(task_dir):
            assert os.path.exists(os.path.join(task_dir, ".task.lock"))


class TestSafeIO:
    """安全文件读写测试"""

    def test_safe_write_and_read(self, tmp_path):
        """安全写入和读取"""
        filepath = str(tmp_path / "test.txt")
        safe_write(filepath, "hello world")
        content = safe_read(filepath)
        assert content == "hello world"

    def test_safe_read_nonexistent(self, tmp_path):
        """读取不存在的文件"""
        filepath = str(tmp_path / "nonexistent.txt")
        result = safe_read(filepath)
        assert result is None

    def test_safe_write_creates_dirs(self, tmp_path):
        """写入时自动创建目录"""
        filepath = str(tmp_path / "a" / "b" / "c" / "test.txt")
        safe_write(filepath, "deep nested")
        assert safe_read(filepath) == "deep nested"

    def test_concurrent_writes(self, tmp_path):
        """并发写入"""
        filepath = str(tmp_path / "counter.txt")
        errors = []

        def write_val(val):
            try:
                for _ in range(3):
                    safe_write(filepath, str(val))
                    time.sleep(0.005)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write_val, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # 文件应该有内容
        content = safe_read(filepath)
        assert content is not None