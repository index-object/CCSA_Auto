"""加载动画工具模块
为NiceGUI按钮提供加载动画和防抖功能
"""

import asyncio
from typing import Callable, Any
from functools import wraps
from nicegui import ui


def create_loading_button(text: str, on_click: Callable, **kwargs) -> ui.button:
    """创建带有加载动画功能的按钮 - 按照test_simple_loading.py的成功模式
    
    Args:
        text: 按钮文本
        on_click: 点击事件处理函数
        **kwargs: 传递给ui.button的其他参数
    
    Returns:
        配置好的按钮实例
    """
    # 创建按钮
    btn = ui.button(text, **kwargs)
    
    # 包装点击事件
    original_on_click = on_click
    
    async def wrapped_on_click():
        # 设置加载状态
        btn.props('loading')
        btn.disable()
        
        try:
            # 添加1秒延迟确保用户能看到加载动画
            await asyncio.sleep(1)
            
            # 执行原函数
            if asyncio.iscoroutinefunction(original_on_click):
                await original_on_click()
            else:
                original_on_click()
        except Exception as e:
            ui.notify(f'操作失败: {str(e)}', type='negative')
            raise
        finally:
            # 恢复按钮状态
            btn.enable()
            btn.props(remove='loading')
    
    # 替换点击事件
    btn.on_click(wrapped_on_click)
    
    return btn


def with_loading(button: ui.button = None, loading_text: str = "处理中..."):
    """为按钮点击事件添加加载动画的装饰器
    
    Args:
        button: 按钮实例，如果为None则从函数参数获取
        loading_text: 加载时显示的文本
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取按钮实例
            btn = button
            if btn is None:
                # 尝试从args或kwargs中获取按钮
                for arg in args:
                    if isinstance(arg, ui.button):
                        btn = arg
                        break
                if btn is None:
                    for key, value in kwargs.items():
                        if isinstance(value, ui.button):
                            btn = value
                            break
            
            if btn is None:
                # 如果没有找到按钮，直接执行原函数
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            try:
                # 设置加载状态
                btn.props(f'loading loading-text="{loading_text}"')
                btn.disable()
                
                # 添加1秒延迟确保用户能看到加载动画
                await asyncio.sleep(1)
                
                # 执行原函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                    
                return result
                
            except Exception as e:
                ui.notify(f'操作失败: {str(e)}', type='negative')
                raise
            finally:
                # 恢复按钮状态
                btn.enable()
                btn.props(remove='loading')
        
        return wrapper
    return decorator


def debounce(wait_time: float = 0.5):
    """防抖装饰器，防止函数被频繁调用
    
    Args:
        wait_time: 等待时间（秒）
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        last_called = 0
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_called
            import time
            
            current_time = time.time()
            if current_time - last_called < wait_time:
                return  # 忽略频繁调用
            
            last_called = current_time
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator
