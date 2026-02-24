import sys
import os
import threading
import time
from datetime import datetime

sys.path.insert(0, os.path.abspath("."))

from ccsa_auto.core.logger import setup_logger

logger = setup_logger("test_loguru")


def test_task(task_id: int):
    """测试任务函数"""
    thread_name = threading.current_thread().name
    logger.info(f"[任务{task_id}] 开始执行 | 线程: {thread_name}")

    for i in range(5):
        logger.info(f"[任务{task_id}] 第 {i + 1} 条日志")
        time.sleep(0.1)

    logger.info(f"[任务{task_id}] 执行完成")


def run_concurrent_test():
    """并发测试日志写入"""
    print("=" * 50)
    print("开始并发日志测试")
    print("=" * 50)

    threads = []
    for i in range(10):
        t = threading.Thread(target=test_task, args=(i + 1,), name=f"Task-{i + 1}")
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    print("=" * 50)
    print("所有任务完成，检查是否有日志轮转错误")
    print("=" * 50)


def run_sequential_test():
    """顺序测试日志写入"""
    print("=" * 50)
    print("开始顺序日志测试")
    print("=" * 50)

    for i in range(20):
        logger.info(f"[顺序测试] 第 {i + 1} 条日志")
        time.sleep(0.2)

    print("=" * 50)
    print("顺序测试完成")
    print("=" * 50)


if __name__ == "__main__":
    run_concurrent_test()
    run_sequential_test()
    print("测试完成")
