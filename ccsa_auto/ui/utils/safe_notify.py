"""安全通知模块

提供在UI上下文可能失效时仍能安全执行的notify封装
"""

import logging
from typing import Optional
from nicegui import ui

logger = logging.getLogger(__name__)


def safe_notify(
    message: str, type: str = "info", position: str = "top-right", timeout: int = 3000
) -> Optional[bool]:
    """安全地显示通知

    Args:
        message: 通知消息
        type: 通知类型 (positive/negative/warning/info)
        position: 通知位置
        timeout: 显示时长（毫秒）

    Returns:
        bool: True表示成功显示，False表示上下文已失效
    """
    try:
        ui.notify(message=message, type=type, position=position, timeout=timeout)
        return True
    except RuntimeError as e:
        if "deleted" in str(e).lower() or "parent" in str(e).lower():
            logger.warning(f"UI上下文已失效，跳过通知: {message}")
            return False
        raise


def safe_notify_success(message: str) -> Optional[bool]:
    """显示成功通知"""
    return safe_notify(message, type="positive")


def safe_notify_error(message: str) -> Optional[bool]:
    """显示错误通知"""
    return safe_notify(message, type="negative")


def safe_notify_warning(message: str) -> Optional[bool]:
    """显示警告通知"""
    return safe_notify(message, type="warning")


def safe_notify_info(message: str) -> Optional[bool]:
    """显示信息通知"""
    return safe_notify(message, type="info")
