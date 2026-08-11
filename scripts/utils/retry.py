#!/usr/bin/env python3
"""
通用重试工具模块
职责：为网络请求、文件操作等提供可配置的重试机制
"""

import time
import logging
import functools
from typing import Callable, TypeVar, Any, Tuple, Type

logger = logging.getLogger(__name__)

T = TypeVar("T")

# 默认重试配置
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0  # 秒
DEFAULT_BACKOFF_FACTOR = 2.0  # 指数退避因子
DEFAULT_MAX_DELAY = 30.0  # 最大延迟


def retry(
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    max_delay: float = DEFAULT_MAX_DELAY,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable[[Exception, int], None] = None,
):
    """
    通用重试装饰器

    Args:
        max_retries: 最大重试次数
        retry_delay: 初始重试延迟（秒）
        backoff_factor: 退避因子（每次重试延迟乘以此值）
        max_delay: 最大延迟时间
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = retry_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        current_delay = min(delay, max_delay)
                        logger.warning(
                            "[%s] 第 %d/%d 次重试（%.1fs 后）: %s",
                            func.__name__, attempt + 1, max_retries,
                            current_delay, str(e)
                        )
                        if on_retry:
                            on_retry(e, attempt + 1)
                        time.sleep(current_delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            "[%s] 重试 %d 次后仍失败: %s",
                            func.__name__, max_retries, str(e)
                        )
            raise last_exception
        return wrapper
    return decorator


def retry_call(
    func: Callable[..., T],
    args: tuple = (),
    kwargs: dict = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    max_delay: float = DEFAULT_MAX_DELAY,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> T:
    """
    对函数调用进行重试（函数式用法，非装饰器）

    用法:
        result = retry_call(requests.get, args=("https://example.com",), kwargs={"timeout": 10})
    """
    if kwargs is None:
        kwargs = {}
    delay = retry_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                current_delay = min(delay, max_delay)
                logger.warning(
                    "[%s] 第 %d/%d 次重试（%.1fs 后）: %s",
                    func.__name__, attempt + 1, max_retries,
                    current_delay, str(e)
                )
                time.sleep(current_delay)
                delay *= backoff_factor
            else:
                logger.error(
                    "[%s] 重试 %d 次后仍失败: %s",
                    func.__name__, max_retries, str(e)
                )
    raise last_exception
