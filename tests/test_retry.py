"""测试 retry 工具模块"""
import pytest
import time
from utils.retry import retry, retry_call


class TestRetryDecorator:
    """retry 装饰器测试"""

    def test_success_no_retry(self):
        """成功时不重试"""
        call_count = 0

        @retry(max_retries=3, retry_delay=0.01)
        def always_succeeds():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = always_succeeds()
        assert result == "ok"
        assert call_count == 1

    def test_retry_then_succeed(self):
        """重试后成功"""
        call_count = 0

        @retry(max_retries=3, retry_delay=0.01, exceptions=(ValueError,))
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        result = fails_twice()
        assert result == "ok"
        assert call_count == 3

    def test_retry_exhausted(self):
        """重试次数耗尽后抛出异常"""
        @retry(max_retries=2, retry_delay=0.01, exceptions=(ValueError,))
        def always_fails():
            raise ValueError("always fails")

        with pytest.raises(ValueError, match="always fails"):
            always_fails()

    def test_backoff(self):
        """指数退避"""
        call_times = []

        @retry(max_retries=3, retry_delay=0.05, backoff_factor=2.0, exceptions=(RuntimeError,))
        def track_timing():
            call_times.append(time.time())
            if len(call_times) < 4:
                raise RuntimeError("retry")

        track_timing()
        assert len(call_times) == 4
        # 第二次调用间隔应约 0.05s，第三次约 0.1s，第四次约 0.2s
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        delay3 = call_times[3] - call_times[2]
        assert delay2 > delay1 * 1.5  # 退避生效
        assert delay3 > delay2 * 1.5

    def test_only_catches_specified_exceptions(self):
        """只捕获指定类型的异常"""
        @retry(max_retries=3, retry_delay=0.01, exceptions=(ValueError,))
        def raises_type_error():
            raise TypeError("wrong type")

        with pytest.raises(TypeError):
            raises_type_error()

    def test_on_retry_callback(self):
        """on_retry 回调被正确调用"""
        callback_calls = []

        def on_retry(exc, attempt):
            callback_calls.append((str(exc), attempt))

        @retry(max_retries=2, retry_delay=0.01, exceptions=(ValueError,), on_retry=on_retry)
        def fails():
            raise ValueError("err")

        with pytest.raises(ValueError):
            fails()

        assert len(callback_calls) == 2
        assert callback_calls[0] == ("err", 1)
        assert callback_calls[1] == ("err", 2)


class TestRetryCall:
    """retry_call 函数式接口测试"""

    def test_success_first_try(self):
        """第一次就成功"""
        result = retry_call(lambda: 42, max_retries=3)
        assert result == 42

    def test_retry_then_succeed(self):
        """重试后成功"""
        call_count = 0

        def maybe_fail():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("fail")
            return "done"

        result = retry_call(maybe_fail, max_retries=3, retry_delay=0.01, exceptions=(RuntimeError,))
        assert result == "done"
        assert call_count == 2

    def test_all_retries_fail(self):
        """所有重试都失败"""
        def always_fail():
            raise ValueError("nope")

        with pytest.raises(ValueError, match="nope"):
            retry_call(always_fail, max_retries=2, retry_delay=0.01)

    def test_with_args_and_kwargs(self):
        """传递 args 和 kwargs"""
        def add(a, b, extra=0):
            return a + b + extra

        result = retry_call(add, args=(1, 2), kwargs={"extra": 10})
        assert result == 13