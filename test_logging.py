# -*- coding: utf-8 -*-
"""日志模块回归测试。

覆盖：
  1. 渠道分离（app/task/access/error）与上下文自动注入；
  2. 访问日志为可解析的 JSON 行；
  3. 多进程并发写日志 —— 每进程独立文件，互不争抢；
  4. 每日归档 —— 轮转产物按“记录里的日期”拆分合并到 archive/<日期>/<渠道>.log；
  5. 归档保留期清理；
  6. 任务运行记录（task_run_logs 表）写入与查询。

用法：
  .venv/bin/python test_logging.py
"""

import glob
import json
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

# 必须在导入 ccsa_auto.core.logger 之前设置，Config 在导入时读取环境变量
_TMP_LOG_DIR = tempfile.mkdtemp(prefix="ccsa_log_test_")
os.environ["CCSA_LOG_DIR"] = _TMP_LOG_DIR
os.environ["CCSA_LOG_LEVEL"] = "DEBUG"
os.environ["CCSA_LOG_CONSOLE"] = "0"
os.environ["CCSA_LOG_ACCESS"] = "1"
os.environ["CCSA_LOG_ACCESS_DB"] = "0"
sys.path.insert(0, REPO_ROOT)

from ccsa_auto.core.logger import (  # noqa: E402
    ARCHIVE_DIR,
    LIVE_DIR,
    get_logger,
    get_task_logger,
    log_access,
    log_context,
    archive_logs,
    logging_status,
)

_passed = 0


def check(name, condition, detail=""):
    global _passed
    if condition:
        _passed += 1
        print(f"  [PASS] {name}")
    else:
        raise AssertionError(f"[FAIL] {name} {detail}")


def _read(path):
    return Path(path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
def test_channels_and_context():
    print("\n[1] 渠道分离与上下文注入")
    app_log = get_logger("test.app")
    task_log = get_task_logger("test.task")

    with log_context(request_id="req-abc", user_id=42, client_ip="1.2.3.4"):
        app_log.info("应用渠道日志")
        task_log.info("任务渠道日志")
        app_log.error("错误渠道日志")

    log_access(
        event="page_view",
        user_id=42,
        path="/admin_v2/logs",
        method="GET",
        status_code=200,
        duration_ms=8.5,
        client_ip="1.2.3.4",
        request_id="req-abc",
    )

    status = logging_status()
    names = {f["name"] for f in status["live_files"]}
    app_file = next(n for n in names if n.startswith("app."))
    task_file = next(n for n in names if n.startswith("task."))
    error_file = next(n for n in names if n.startswith("error."))
    access_file = next(n for n in names if n.startswith("access."))

    app_text = _read(LIVE_DIR / app_file)
    task_text = _read(LIVE_DIR / task_file)
    error_text = _read(LIVE_DIR / error_file)
    access_text = _read(LIVE_DIR / access_file)

    check("app 渠道含应用日志", "应用渠道日志" in app_text)
    check("app 渠道含错误日志", "错误渠道日志" in app_text)
    check("task 渠道只含任务日志", "任务渠道日志" in task_text and "应用渠道日志" not in task_text)
    check("error 渠道汇总错误", "错误渠道日志" in error_text and "应用渠道日志" not in error_text)
    check("上下文注入 app 日志", "request_id=req-abc" in app_text and "user_id=42" in app_text)
    check("上下文注入 task 日志", "request_id=req-abc" in task_text)

    lines = [l for l in access_text.splitlines() if l.strip()]
    check("access 渠道为 JSON 行", len(lines) == 1 and lines[0].startswith("{"))
    payload = json.loads(lines[0])
    check("access JSON 字段完整",
          payload.get("event") == "page_view"
          and payload.get("path") == "/admin_v2/logs"
          and payload.get("status_code") == 200
          and payload.get("user_id") == 42
          and payload.get("request_id") == "req-abc",
          payload)
    check("access JSON 含毫秒时间戳", len(str(payload.get("ts"))) >= 19, payload.get("ts"))


# ---------------------------------------------------------------------------
_CHILD_SCRIPT = """
import os, sys
sys.path.insert(0, {repo!r})
os.environ["CCSA_LOG_DIR"] = {log_dir!r}
os.environ["CCSA_LOG_CONSOLE"] = "0"
from ccsa_auto.core.logger import get_logger
lg = get_logger("child")
tag = sys.argv[1]
for i in range(25):
    lg.info("child {{}} line {{}}", tag, i)
print("child-done", tag, os.getpid())
"""


def test_multiprocess_isolation():
    print("\n[2] 多进程并发写日志：每进程独立文件")
    before = {p.name for p in LIVE_DIR.glob("app.*.log")}

    script = _CHILD_SCRIPT.format(repo=REPO_ROOT, log_dir=_TMP_LOG_DIR)
    env = dict(os.environ)
    procs = [
        subprocess.Popen(
            [sys.executable, "-c", script, f"c{i}"],
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for i in range(2)
    ]
    pids = []
    for proc in procs:
        out, err = proc.communicate(timeout=60)
        check(f"子进程退出码为 0 (pid={proc.pid})", proc.returncode == 0, err.decode()[-500:])
        text = out.decode()
        if "child-done" in text:
            pids.append(int(text.split()[-1]))

    after = {p.name for p in LIVE_DIR.glob("app.*.log")}
    new_files = after - before
    check("两个子进程各自生成独立日志文件", len(new_files) == 2, new_files)

    for pid in pids:
        matches = [n for n in new_files if f"p{pid}_" in n]
        check(f"pid {pid} 有独立文件", len(matches) == 1, new_files)

    for name in new_files:
        content = _read(LIVE_DIR / name)
        check(f"{name} 写入 25 行且无串行错乱",
              content.count("child c") == 25, content.count("child c"))

    status = logging_status()
    check("状态接口能列出所有 live 文件", len(status["live_files"]) >= 5)
    return new_files


def test_daily_archive():
    print("\n[3] 每日归档：按记录日期拆分合并")
    # 合成一个轮转产物（模拟跨天轮转），文件名时间戳与内容日期故意不一致
    zip_name = LIVE_DIR / "task.p999999_1700000000.2026-01-02_00-00-05_000001.log.zip"
    member = "task.p999999_1700000000.2026-01-02_00-00-05_000001.log"
    with zipfile.ZipFile(zip_name, "w") as archive:
        archive.writestr(
            member,
            "2026-01-01 23:59:00.000 | INFO  | task | - | x:1 | 第一天记录\n"
            "2026-01-02 00:00:30.000 | INFO  | task | - | x:1 | 第二天记录\n",
        )

    stats = archive_logs(force=True)
    check("归档未因锁被跳过", not stats.get("skipped"))

    day1 = ARCHIVE_DIR / "2026-01-01" / "task.log"
    day2 = ARCHIVE_DIR / "2026-01-02" / "task.log"
    check("第一天文件生成", day1.exists())
    check("第二天文件生成", day2.exists())
    check("第一天内容正确", "第一天记录" in _read(day1) and "第二天记录" not in _read(day1))
    check("第二天内容正确", "第二天记录" in _read(day2))
    check("轮转产物已从 live 移除", not zip_name.exists())

    check("多次归档幂等（追加不重复）", _read(day1).count("第一天记录") == 1)


def test_archive_retention():
    print("\n[4] 归档保留期清理")
    old_dir = ARCHIVE_DIR / "2000-01-01"
    old_dir.mkdir(parents=True, exist_ok=True)
    (old_dir / "app.log").write_text("很久以前\n", encoding="utf-8")

    stats = archive_logs(retention_days=30, force=True)
    check("过期归档目录被删除", "2000-01-01" in stats.get("deleted_days", []), stats)
    check("过期目录确实不存在", not old_dir.exists())


def test_task_run_records():
    print("\n[5] 任务运行记录（task_run_logs）")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from ccsa_auto.core.database import Base
    from ccsa_auto.core import models  # noqa: F401  注册任务等表
    from ccsa_auto.modules.logging import models as log_models  # noqa: F401
    from ccsa_auto.modules import logging as logging_module

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    engine = create_engine(f"sqlite:///{tmp.name}")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    service = logging_module.LoggingService
    original = logging_module.service.SessionLocal
    logging_module.service.SessionLocal = TestSession
    try:
        started = datetime.utcnow()
        run_id = service.log_task_run_start(
            task_id=7,
            user_id=3,
            task_type="daily",
            task_name="每日一题",
            trigger="schedule",
            trace_id="trace-1",
            started_at=started,
        )
        check("写入运行开始记录返回主键", isinstance(run_id, int), run_id)

        service.log_task_run_finish(
            run_id,
            "success",
            duration_ms=1234,
            message="执行成功",
            result={
                "success": True,
                "message": "执行成功",
                "result": {"foo": "bar"},
                "score_strategy": {
                    "score": 20,
                    "max_score": 20,
                    "correct_questions": 10,
                    "wrong_questions": 0,
                },
            },
        )

        result = service.get_task_runs(task_id=7)
        check("查询到 1 条运行记录", result.get("total") == 1, result)
        run = result["runs"][0]
        check("状态为 success", run["status"] == "success", run)
        check("耗时正确", run["duration_ms"] == 1234, run)
        check("得分正确", run["score"] == 20 and run["max_score"] == 20, run)
        check("trace_id 保留", run["trace_id"] == "trace-1", run)
        check("开始时间已格式化", len(str(run["started_at"])) >= 19, run["started_at"])

        stats = service.get_task_run_statistics(days=1)
        check("统计成功 1 次", stats.get("success") == 1 and stats.get("total") == 1, stats)

        # run_id 缺失时应退化为直接插入完整记录
        service.log_task_run_finish(
            None,
            "failed",
            task_id=8,
            user_id=4,
            task_type="weekly",
            task_name="每周一课",
            message="失败",
            error_type="SubmitError",
        )
        result2 = service.get_task_runs(task_id=8)
        check("run_id 缺失时仍写入记录", result2.get("total") == 1, result2)
        check("失败记录含错误类型",
              result2["runs"][0]["status"] == "failed"
              and result2["runs"][0]["error_type"] == "SubmitError",
              result2["runs"][0])
    finally:
        logging_module.service.SessionLocal = original
        engine.dispose()
        os.unlink(tmp.name)


def test_scheduler_task_run_end_to_end():
    print("\n[6] 调度器端到端：一次任务运行 = 一条精确记录")
    from datetime import timezone

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from ccsa_auto.core.database import Base
    from ccsa_auto.core.models import Task, User
    from ccsa_auto.modules.task import scheduler as scheduler_module
    from ccsa_auto.modules import logging as logging_module

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    engine = create_engine(f"sqlite:///{tmp.name}")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    db = TestSession()
    user = User(
        username="tester",
        password="x",
        name="测试用户",
        external_username="ext",
        external_password="pw",
    )
    db.add(user)
    db.commit()
    task = Task(
        user_id=user.id,
        task_type="daily",
        task_name="每日一题",
        cron_expression="0 8 * * *",
        is_active=True,
    )
    db.add(task)
    db.commit()
    task_id, user_id = task.id, user.id
    db.close()

    originals = {
        "scheduler.SessionLocal": scheduler_module.SessionLocal,
        "service.SessionLocal": logging_module.service.SessionLocal,
        "TaskService.execute_task": scheduler_module.TaskService.execute_task,
        "add_task_to_scheduler": scheduler_module.add_task_to_scheduler,
    }
    scheduler_module.SessionLocal = TestSession
    logging_module.service.SessionLocal = TestSession
    scheduler_module.add_task_to_scheduler = lambda tid: True

    try:
        scheduler_module.TaskService.execute_task = staticmethod(
            lambda t, u: {
                "success": True,
                "message": "每日一题执行成功",
                "result": {"ok": True},
                "score_strategy": {
                    "score": 20.0,
                    "max_score": 20.0,
                    "correct_questions": 10,
                    "wrong_questions": 0,
                },
            }
        )
        scheduler_module.execute_user_task(task_id, trigger="manual")

        result = logging_module.LoggingService.get_task_runs(task_id=task_id)
        check("成功运行写入 1 条记录", result["total"] == 1, result)
        run = result["runs"][0]
        check("记录状态 success", run["status"] == "success", run)
        check("记录触发方式 manual", run["trigger"] == "manual", run)
        check("记录含耗时", isinstance(run["duration_ms"], int), run)
        check("记录含得分", run["score"] == 20.0, run)
        check("记录含 trace_id", bool(run["trace_id"]), run)
        check(
            "运行结束后写入下次运行时间",
            run["next_run_time"] not in (None, "未设置"),
            run.get("next_run_time"),
        )

        # 台账（失败日报依赖的 app_logs）也应写入
        logs = logging_module.LoggingService.get_logs(log_type="task")
        check("任务台账同步写入", logs["total"] >= 1, logs)

        # 失败场景
        scheduler_module.TaskService.execute_task = staticmethod(
            lambda t, u: {
                "success": False,
                "message": "提交答案失败：平台错误",
                "error_type": "SubmitError",
            }
        )
        scheduler_module.execute_user_task(task_id, trigger="manual")
        runs = logging_module.LoggingService.get_task_runs(task_id=task_id)
        check("失败运行写入第二条记录", runs["total"] == 2, runs)
        failed = [r for r in runs["runs"] if r["status"] == "failed"]
        check("失败记录存在且错误类型正确",
              len(failed) == 1 and failed[0]["error_type"] == "SubmitError", failed)

        db = TestSession()
        task_row = db.query(Task).filter_by(id=task_id).first()
        check("任务表状态更新为 failed", task_row.execution_status == "failed", task_row.execution_status)
        db.close()
    finally:
        scheduler_module.SessionLocal = originals["scheduler.SessionLocal"]
        logging_module.service.SessionLocal = originals["service.SessionLocal"]
        scheduler_module.TaskService.execute_task = originals["TaskService.execute_task"]
        scheduler_module.add_task_to_scheduler = originals["add_task_to_scheduler"]
        engine.dispose()
        os.unlink(tmp.name)


def main():
    print("=" * 60)
    print(f"日志模块测试 | 日志目录: {_TMP_LOG_DIR}")
    print("=" * 60)

    test_channels_and_context()
    test_multiprocess_isolation()
    test_daily_archive()
    test_archive_retention()
    test_task_run_records()
    test_scheduler_task_run_end_to_end()

    print("\n" + "=" * 60)
    print(f"全部通过：{_passed} 项检查")
    print(f"（日志目录保留在 {_TMP_LOG_DIR}，可手动删除）")
    print("=" * 60)


if __name__ == "__main__":
    main()
