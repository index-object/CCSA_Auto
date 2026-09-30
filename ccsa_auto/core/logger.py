"""统一日志模块（基于 Loguru）。

历史问题
--------
1. 旧实现每个模块导入时都调用一次 ``setup_logger()``，而它内部执行
   ``logger.remove()`` 并重新 ``add`` —— 全局副作用 + 重复创建 sink；
2. 所有进程（NiceGUI 热重载的父子进程、重复启动的实例）都往同一个
   ``logs/app.log`` 写，Windows 上重命名被占用导致轮转失败，于是
   "每天归档" 失效，日志全部堆在一个文件里；
3. 标准库 logging / print / loguru 三套输出并存，内容分散、格式不一。

本模块的设计
------------
* **每进程独立文件**：日志先写到 ``logs/live/<channel>.p<pid>_<启动时间>.log``。
  两个进程永远不会打开同一个文件，从根上消灭文件争抢与轮转失败。
* **每天归档**：Loguru 在 00:00 轮转并压缩；定时任务再把轮转产物按记录里的
  日期合并到 ``logs/archive/YYYY-MM-DD/<channel>.log``，并清理过期归档。
* **分渠道**：``app``（系统运行）、``task``（任务执行）、``access``（客户访问）
  三个业务渠道各自成文件；另外所有 ERROR 及以上级别统一汇总到 ``error`` 渠道。
* **上下文**：借助 ``contextvars``，在任意位置 ``log_context(request_id=..., user_id=...)``
  之后，该作用域内的每条日志都会自动带上这些字段，无需层层传参。
* **幂等初始化**：``setup_logging()`` 只生效一次；``get_logger()`` 未初始化时自动初始化。

用法
----
::

    from ccsa_auto.core.logger import get_logger, log_context

    logger = get_logger(__name__)                      # app 渠道
    task_log = get_logger(__name__, channel=CHANNEL_TASK)

    with log_context(task_id=1, user_id=8):
        task_log.info("开始执行")                       # 自动带上 task_id/user_id

    # 客户访问（写成 JSON 行，便于统计）
    from ccsa_auto.core.logger import log_access
    log_access(event="page_view", path="/admin_v2", status_code=200, client_ip="1.2.3.4")
"""

from __future__ import annotations

import atexit
import contextvars
import json
import os
import re
import shutil
import sys
import threading
import time
import uuid
import zipfile
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from loguru import logger as _logger

from ccsa_auto.core.config import Config

# ---------------------------------------------------------------------------
# 渠道定义
# ---------------------------------------------------------------------------
CHANNEL_APP = "app"  # 系统/应用运行
CHANNEL_TASK = "task"  # 任务执行
CHANNEL_ACCESS = "access"  # 客户访问
CHANNEL_ERROR = "error"  # 所有 ERROR 及以上的汇总

BUSINESS_CHANNELS = (CHANNEL_APP, CHANNEL_TASK, CHANNEL_ACCESS)
ALL_CHANNELS = BUSINESS_CHANNELS + (CHANNEL_ERROR,)

_ERROR_LEVEL_NO = 40  # loguru ERROR

# ---------------------------------------------------------------------------
# 路径与进程标识
# ---------------------------------------------------------------------------
LOG_DIR = Path(Config.LOG_DIR)
LIVE_DIR = LOG_DIR / "live"
ARCHIVE_DIR = LOG_DIR / "archive"
CONSOLE_DIR = LOG_DIR / "console"
_ARCHIVE_LOCK = LOG_DIR / ".archive.lock"

_START_TIME = time.time()
_PROCESS_TAG = f"p{os.getpid()}_{int(_START_TIME)}"

_FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <5} | {extra[channel]} | "
    "{extra[ctx]} | {name}:{line} | {message}"
)
_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <5}</level> | "
    "<cyan>{extra[channel]}</cyan> | <level>{extra[ctx]}</level> | "
    "<dim>{name}:{line}</dim> | <level>{message}</level>"
)
# access 渠道每行本身就是一个 JSON 对象（见 log_access），因此文件里只写 message
_ACCESS_FORMAT = "{message}"

_LIVE_RE = re.compile(r"^(?P<channel>[a-z]+)\.p(?P<pid>\d+)_(?P<stamp>\d+)\.log$")
_ROTATED_RE = re.compile(
    r"^(?P<channel>[a-z]+)\.p(?P<pid>\d+)_(?P<stamp>\d+)\."
    r"(?P<ts>\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_\d+)\.log(?:\.zip)?$"
)
_LINE_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)")

# ---------------------------------------------------------------------------
# 上下文（contextvars）
# ---------------------------------------------------------------------------
_log_context: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "ccsa_log_context", default=None
)

# 上下文中这些字段会出现在每条日志的 `key=value` 区域
_CTX_ORDER = (
    "trace_id",
    "request_id",
    "task_id",
    "task_name",
    "user_id",
    "user_name",
    "session_id",
    "client_ip",
    "event",
    "path",
    "method",
    "status",
    "duration_ms",
    "attempt",
)


def new_trace_id() -> str:
    """生成一个短 trace id，用于串联一次请求/一次任务的全部日志。"""
    return uuid.uuid4().hex[:12]


def get_context() -> Dict[str, Any]:
    """返回当前上下文副本。"""
    return dict(_log_context.get() or {})


def update_context(**fields: Any) -> Dict[str, Any]:
    """在当前上下文里就地更新字段（无需 with）。"""
    current = dict(_log_context.get() or {})
    current.update({k: v for k, v in fields.items() if v is not None})
    _log_context.set(current)
    return current


def bind_context(**fields: Any):
    """绑定上下文并返回 token，配合 ``reset_context(token)`` 使用。"""
    current = dict(_log_context.get() or {})
    current.update({k: v for k, v in fields.items() if v is not None})
    return _log_context.set(current)


def reset_context(token) -> None:
    """恢复 ``bind_context`` 返回的 token。"""
    try:
        _log_context.reset(token)
    except (ValueError, LookupError):
        _log_context.set({})


def clear_context() -> None:
    """清空当前上下文。"""
    _log_context.set({})


@contextmanager
def log_context(**fields: Any):
    """在作用域内为所有日志附加字段。

    在线程/协程内有效；子线程需要重新 ``log_context``（contextvars 不会自动继承到
    ``threading.Thread``，但会继承到 ``asyncio`` 任务）。
    """
    token = bind_context(**fields)
    try:
        yield get_context()
    finally:
        reset_context(token)


# ---------------------------------------------------------------------------
# 格式化辅助
# ---------------------------------------------------------------------------
def _fmt_value(value: Any, max_len: Optional[int] = None) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        text = "true" if value else "false"
    elif isinstance(value, float):
        text = f"{value:.3f}".rstrip("0").rstrip(".")
    else:
        text = str(value)
    text = text.replace("\n", "\\n").replace("\r", "\\r")
    limit = max_len if max_len is not None else Config.LOG_CONTEXT_VALUE_MAX_LEN
    if limit and len(text) > limit:
        text = text[:limit] + "…"
    if any(ch.isspace() for ch in text):
        text = '"' + text.replace('"', '\\"') + '"'
    return text


def _patcher(record: Dict[str, Any]) -> None:
    """Loguru patcher：为每条记录补全 channel / ctx 字段。"""
    try:
        extra = record["extra"]
        channel = extra.get("channel") or CHANNEL_APP
        extra["channel"] = channel

        ctx: Dict[str, Any] = dict(_log_context.get() or {})
        for key, value in list(extra.items()):
            if key in ("channel", "ctx", "context"):
                continue
            if value is not None:
                ctx[key] = value
        # 消息里显式传入的 level 覆盖
        ctx.pop("level", None)
        extra["context"] = ctx

        ordered = [(k, ctx[k]) for k in _CTX_ORDER if k in ctx]
        ordered += [
            (k, v) for k, v in ctx.items() if k not in _CTX_ORDER
        ]
        rendered = " ".join(f"{k}={_fmt_value(v)}" for k, v in ordered)
        extra["ctx"] = rendered or "-"
    except Exception:  # pragma: no cover - patcher 绝不能让日志本身报错
        record["extra"].setdefault("channel", CHANNEL_APP)
        record["extra"]["ctx"] = "-"


def _access_serialize(text: str) -> str:
    """access 渠道路由：把 message 原样写出（调用方已写入 JSON）。"""
    return text if text.endswith("\n") else text + "\n"


# ---------------------------------------------------------------------------
# 初始化
# ---------------------------------------------------------------------------
_setup_lock = threading.RLock()
_setup_done = False
_setup_pid: Optional[int] = None
_console_handler_id: Optional[int] = None


def _ensure_dirs() -> None:
    for directory in (LOG_DIR, LIVE_DIR, ARCHIVE_DIR, CONSOLE_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def _live_path(channel: str) -> str:
    return str(LIVE_DIR / f"{channel}.{_PROCESS_TAG}.log")


def _sink_options() -> Dict[str, Any]:
    return {
        "rotation": Config.LOG_ROTATION,
        "retention": f"{Config.LOG_RETENTION_DAYS} days",
        "compression": Config.LOG_COMPRESSION or None,
        "encoding": "utf-8",
        "enqueue": bool(Config.LOG_ENQUEUE),
        "catch": True,
        "backtrace": True,
        "diagnose": False,
        "colorize": False,
    }


def setup_logging(force: bool = False) -> None:
    """初始化日志系统（幂等）。

    Args:
        force: 强制重建全部 sink（进程 fork 后可用）。
    """
    global _setup_done, _setup_pid, _console_handler_id

    with _setup_lock:
        if _setup_done and not force and _setup_pid == os.getpid():
            return

        _ensure_dirs()
        _logger.remove()
        _logger.configure(patcher=_patcher)

        if Config.LOG_CONSOLE:
            _console_handler_id = _logger.add(
                sys.stderr,
                format=_CONSOLE_FORMAT,
                level=Config.LOG_LEVEL,
                colorize=sys.stderr.isatty(),
                backtrace=True,
                diagnose=False,
                catch=True,
            )
        else:
            _console_handler_id = None

        opts = _sink_options()
        for channel in BUSINESS_CHANNELS:
            fmt = _ACCESS_FORMAT if channel == CHANNEL_ACCESS else _FILE_FORMAT
            _logger.add(
                _live_path(channel),
                format=fmt,
                level=Config.LOG_LEVEL,
                filter=lambda record, _ch=channel: record["extra"].get("channel")
                == _ch,
                **opts,
            )

        # 错误汇总：所有 ERROR 及以上（跨渠道）
        _logger.add(
            _live_path(CHANNEL_ERROR),
            format=_FILE_FORMAT,
            level="ERROR",
            filter=lambda record: record["level"].no >= _ERROR_LEVEL_NO,
            **opts,
        )

        _setup_done = True
        _setup_pid = os.getpid()

    _logger.bind(channel=CHANNEL_APP).info(
        "日志系统已初始化 | pid={} process_tag={} dir={} level={} rotation={}",
        os.getpid(),
        _PROCESS_TAG,
        LOG_DIR,
        Config.LOG_LEVEL,
        Config.LOG_ROTATION,
    )


def ensure_process_logging() -> None:
    """fock/spawn 之后子进程 PID 会变化，重新绑定到自己的日志文件。

    该函数非常轻量，可在请求入口、任务入口处无条件调用。
    """
    if _setup_done and _setup_pid == os.getpid():
        return
    setup_logging(force=True)


def get_logger(name: Optional[str] = None, channel: str = CHANNEL_APP):
    """获取绑定了渠道的 logger。

    Args:
        name: 一般传 ``__name__``，会作为 ``{name}`` 显示在日志里。
        channel: ``app`` / ``task`` / ``access``。
    """
    if not _setup_done:
        setup_logging()
    elif _setup_pid != os.getpid():
        ensure_process_logging()

    # 说明：loguru 的 {name} 字段取自实际调用点所在模块，因此 name 参数只需保持
    # 兼容签名即可，无需额外绑定到 extra（否则会污染上下文）。
    _ = name
    return _logger.bind(channel=channel)


def get_task_logger(name: Optional[str] = None):
    return get_logger(name, channel=CHANNEL_TASK)


def get_access_logger(name: Optional[str] = None):
    return get_logger(name, channel=CHANNEL_ACCESS)


# 兼容旧 API：`setup_logger(__name__)` 曾用于各模块导入时初始化。
def setup_logger(name: Optional[str] = None):
    """已废弃，仅为兼容旧调用保留。请改用 ``get_logger``。"""
    return get_logger(name)


# ---------------------------------------------------------------------------
# 访问日志（JSON 行）
# ---------------------------------------------------------------------------
def log_access(
    event: str,
    *,
    user_id: Optional[int] = None,
    user_name: Optional[str] = None,
    session_id: Optional[str] = None,
    method: Optional[str] = None,
    path: Optional[str] = None,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    referer: Optional[str] = None,
    request_id: Optional[str] = None,
    level: str = "INFO",
    message: str = "",
    **extra_fields: Any,
) -> Dict[str, Any]:
    """写一条客户访问日志（access 渠道，JSON 行）。

    返回写入的 payload，便于调用方复用/落库。
    """
    if not Config.LOG_ACCESS_ENABLED:
        return {}

    ctx = get_context()
    payload: Dict[str, Any] = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "event": event,
    }
    fields = {
        "user_id": user_id,
        "user_name": user_name,
        "session_id": session_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
        "client_ip": client_ip,
        "user_agent": _shorten(user_agent, 200),
        "referer": referer,
        "request_id": request_id or ctx.get("request_id"),
    }
    for key, value in fields.items():
        if value is not None:
            payload[key] = value
    if message:
        payload["message"] = message
    for key, value in extra_fields.items():
        if value is not None:
            payload[key] = value

    try:
        text = json.dumps(payload, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        payload = {k: str(v) for k, v in payload.items()}
        text = json.dumps(payload, ensure_ascii=False)

    get_access_logger().log(level.upper(), text)
    return payload


def _shorten(value: Optional[str], limit: int) -> Optional[str]:
    if value is None:
        return None
    return value if len(value) <= limit else value[: limit - 1] + "…"


# ---------------------------------------------------------------------------
# 归档
# ---------------------------------------------------------------------------
def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":  # pragma: no cover - 仅在 Windows 生效
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            if kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return code.value == STILL_ACTIVE
            return False
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def _try_lock(handle) -> bool:
    try:
        if os.name == "nt":  # pragma: no cover - 仅在 Windows 生效
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _unlock(handle) -> None:
    try:
        if os.name == "nt":  # pragma: no cover
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


def _line_sort_key(line: str) -> str:
    """从一行日志里取出可排序的时间戳（普通格式或 access JSON）。"""
    match = _LINE_TS_RE.match(line)
    if match:
        return match.group(1)
    stripped = line.lstrip()
    if stripped.startswith("{"):
        try:
            payload = json.loads(stripped)
        except (ValueError, TypeError):
            return ""
        return str(payload.get("ts") or "")
    return ""


def _iter_candidate_files() -> Iterable[Path]:
    """挑出可以安全归档的文件。

    * ``*.log.zip``：Loguru 轮转产物，已经关闭，任何进程都可以处理；
    * ``*.log``：只有写它的进程已经退出（或它是轮转产物）才处理，
      绝不碰仍在写入的 live 文件。
    """
    if not LIVE_DIR.exists():
        return []
    candidates = []
    for path in sorted(LIVE_DIR.iterdir()):
        if not path.is_file():
            continue
        name = path.name
        if name.endswith(".log.zip"):
            if _ROTATED_RE.match(name[:-4]):
                candidates.append(path)
            continue
        if not name.endswith(".log"):
            continue
        live = _LIVE_RE.match(name)
        if live:
            if not _pid_alive(int(live.group("pid"))):
                candidates.append(path)
            continue
        if _ROTATED_RE.match(name):
            candidates.append(path)
    return candidates


def _read_lines(path: Path) -> Iterable[str]:
    if path.name.endswith(".zip"):
        try:
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    with archive.open(member) as handle:
                        for raw in handle:
                            yield raw.decode("utf-8", errors="replace").rstrip("\n")
        except (zipfile.BadZipFile, OSError):
            return
    else:
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for raw in handle:
                    yield raw.rstrip("\n")
        except OSError:
            return


def _channel_of(path: Path) -> str:
    name = path.name
    if name.endswith(".log.zip"):
        name = name[:-4]
    match = _ROTATED_RE.match(name)
    if match:
        return match.group("channel")
    match = _LIVE_RE.match(name)
    if match:
        return match.group("channel")
    return name.split(".")[0]


def archive_logs(
    retention_days: Optional[int] = None,
    min_age_seconds: int = 30,
    force: bool = False,
) -> Dict[str, Any]:
    """把 live 目录里已完成（轮转/进程退出）的日志按天合并归档。

    归档路径：``logs/archive/<YYYY-MM-DD>/<channel>.log``。
    日期取自日志记录本身的时间戳，而不是文件名，避免轮转发生在跨天之后
    导致归档日期错位。

    Args:
        retention_days: 归档保留天数，默认 ``Config.LOG_RETENTION_DAYS``。
        min_age_seconds: 跳过最近 N 秒内改动过的文件（避免读到正在压缩的文件）。
        force: 忽略 ``min_age_seconds``。
    """
    _ensure_dirs()
    retention = (
        Config.LOG_RETENTION_DAYS if retention_days is None else retention_days
    )
    stats: Dict[str, Any] = {
        "archived_files": 0,
        "archived_records": 0,
        "days": sorted(
            {p.name for p in ARCHIVE_DIR.iterdir() if p.is_dir()}
        )
        if ARCHIVE_DIR.exists()
        else [],
        "deleted_days": [],
        "skipped": False,
    }

    lock_handle = None
    try:
        lock_handle = open(_ARCHIVE_LOCK, "a+")
        if not _try_lock(lock_handle):
            stats["skipped"] = True
            return stats

        now = time.time()
        grouped: Dict[tuple, list] = {}
        processed: list = []

        for path in _iter_candidate_files():
            try:
                if not force and now - path.stat().st_mtime < min_age_seconds:
                    continue
            except OSError:
                continue

            channel = _channel_of(path)
            file_records = 0
            for line in _read_lines(path):
                if not line.strip():
                    continue
                key_time = _line_sort_key(line)
                day = key_time[:10] if len(key_time) >= 10 else "unknown"
                grouped.setdefault((day, channel), []).append((key_time, line))
                file_records += 1
            processed.append(path)
            stats["archived_files"] += 1
            stats["archived_records"] += file_records

        for (day, channel), records in grouped.items():
            records.sort(key=lambda item: item[0])
            target_dir = ARCHIVE_DIR / day
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f"{channel}.log"
            with target.open("a", encoding="utf-8") as handle:
                for _, line in records:
                    handle.write(line + "\n")

        # 写成功后再删除源文件
        for path in processed:
            try:
                path.unlink()
            except OSError:
                pass

        # 清理过期归档目录。本轮刚写入的日期不清理，避免“刚归档就被删”。
        written_days = {day for (day, _channel) in grouped}
        cutoff = (datetime.now() - timedelta(days=retention)).date()
        if ARCHIVE_DIR.exists():
            for day_dir in ARCHIVE_DIR.iterdir():
                if not day_dir.is_dir():
                    continue
                if day_dir.name in written_days:
                    continue
                try:
                    day = datetime.strptime(day_dir.name, "%Y-%m-%d").date()
                except ValueError:
                    continue
                if day < cutoff:
                    shutil.rmtree(day_dir, ignore_errors=True)
                    stats["deleted_days"].append(day_dir.name)

        stats["days"] = sorted(p.name for p in ARCHIVE_DIR.iterdir() if p.is_dir())
        return stats
    finally:
        if lock_handle is not None:
            _unlock(lock_handle)
            lock_handle.close()


# ---------------------------------------------------------------------------
# 诊断 / 生命周期
# ---------------------------------------------------------------------------
def log_paths() -> Dict[str, str]:
    """各渠道当前进程的 live 文件路径。"""
    return {channel: _live_path(channel) for channel in ALL_CHANNELS}


def logging_status() -> Dict[str, Any]:
    """返回日志系统状态，供管理后台/排障使用。"""
    _ensure_dirs()
    files = []
    for path in sorted(LIVE_DIR.glob("*.log*")):
        try:
            stat = path.stat()
        except OSError:
            continue
        files.append(
            {
                "name": path.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
        )
    archive_days = []
    if ARCHIVE_DIR.exists():
        for day_dir in sorted(ARCHIVE_DIR.iterdir()):
            if day_dir.is_dir():
                archive_days.append(
                    {
                        "day": day_dir.name,
                        "channels": sorted(
                            p.stem for p in day_dir.glob("*.log")
                        ),
                    }
                )
    return {
        "process_tag": _PROCESS_TAG,
        "pid": os.getpid(),
        "log_dir": str(LOG_DIR),
        "live_dir": str(LIVE_DIR),
        "archive_dir": str(ARCHIVE_DIR),
        "level": Config.LOG_LEVEL,
        "rotation": Config.LOG_ROTATION,
        "retention_days": Config.LOG_RETENTION_DAYS,
        "channels": list(ALL_CHANNELS),
        "live_files": files,
        "archive_days": archive_days[-30:],
    }


def trigger_rotation() -> None:
    """写一条心跳日志，促使 Loguru 在同一天的第一条日志时完成跨天轮转。"""
    get_logger(__name__).debug("日志心跳（用于触发跨天轮转）")


def shutdown_logging() -> None:
    """冲刷队列并移除 sink。"""
    try:
        _logger.complete()
    except Exception:  # pragma: no cover
        pass
    with _setup_lock:
        _logger.remove()


def _atexit_flush() -> None:  # pragma: no cover - 进程退出时调用
    try:
        _logger.complete()
    except Exception:
        pass


atexit.register(_atexit_flush)

# 模块导入即初始化，保证「任意位置直接 get_logger」都能用
setup_logging()


__all__ = [
    "CHANNEL_APP",
    "CHANNEL_TASK",
    "CHANNEL_ACCESS",
    "CHANNEL_ERROR",
    "BUSINESS_CHANNELS",
    "ALL_CHANNELS",
    "LOG_DIR",
    "LIVE_DIR",
    "ARCHIVE_DIR",
    "get_logger",
    "get_task_logger",
    "get_access_logger",
    "setup_logger",
    "setup_logging",
    "ensure_process_logging",
    "shutdown_logging",
    "log_context",
    "bind_context",
    "reset_context",
    "update_context",
    "clear_context",
    "get_context",
    "new_trace_id",
    "log_access",
    "archive_logs",
    "trigger_rotation",
    "logging_status",
    "log_paths",
    "logger",
]

# 兼容：from ccsa_auto.core.logger import logger 之后可直接用（未绑定渠道）
logger = _logger
