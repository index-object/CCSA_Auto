# -*- coding: utf-8 -*-
"""失败日报重复播报回归测试。

复现并验证修复：
旧实现把"上次报告时间"保存在进程内存（`_last_report_utc = utcnow() - 24h`），
进程每次重启窗口都会回退 24 小时，于是把重启前的历史失败重新算作本轮新失败，
在没有真实失败的情况下发出"任务失败日报"邮件。

修复后水位持久化在 system_configs（app_logs.id），重启不回退。

用法：
  uv run python test_failure_report.py
"""

import os
import tempfile
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ccsa_auto.core import models  # noqa: F401  注册表结构
from ccsa_auto.core import system_config as system_config_module
from ccsa_auto.core.database import Base
from ccsa_auto.modules.logging.models import AppLog
from ccsa_auto.modules.logging.service import LogType
from ccsa_auto.modules.task import scheduler as scheduler_module

_passed = 0


def check(name, condition, detail=""):
    global _passed
    if condition:
        _passed += 1
        print(f"  [PASS] {name}")
    else:
        raise AssertionError(f"[FAIL] {name} {detail}")


def main():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    engine = create_engine(f"sqlite:///{tmp.name}")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    # 让调度器与系统配置服务都读写隔离的测试库
    scheduler_module.SessionLocal = TestSession
    system_config_module.SessionLocal = TestSession

    sent = []

    def fake_send(subject, body):
        sent.append((subject, body))
        return True

    scheduler_module.send_email = fake_send

    def add_log(status, content, when=None):
        db = TestSession()
        try:
            db.add(
                AppLog(
                    log_type=LogType.TASK,
                    operation="daily",
                    content=content,
                    user_id=999,
                    target_type="task",
                    target_id=999,
                    status=status,
                    created_at=when or datetime.utcnow(),
                )
            )
            db.commit()
        finally:
            db.close()

    print("\n[1] 首次运行：建立水位，不发送")
    base = datetime.utcnow() - timedelta(days=2)
    add_log("failed", "历史失败A", base)
    add_log("failed", "历史失败B", base + timedelta(minutes=1))
    add_log("success", "成功记录", base + timedelta(minutes=2))

    scheduler_module.daily_failure_report_job()
    check("首次运行不发送邮件", len(sent) == 0)

    print("\n[2] 模拟进程重启（水位持久化在 DB）：历史失败不得重复播报")
    scheduler_module.daily_failure_report_job()
    check("重启后仍不发送历史失败", len(sent) == 0)

    print("\n[3] 出现真实失败：应发送一封，且只含新失败")
    add_log("failed", "新失败C")
    add_log("failed", "新失败D")
    scheduler_module.daily_failure_report_job()
    check("发送一封邮件", len(sent) == 1, len(sent))
    subject, body = sent[-1]
    check("主题含失败条数", "共2条失败" in subject, subject)
    check("包含新失败C", "新失败C" in body)
    check("包含新失败D", "新失败D" in body)
    check("不含历史失败A/B", "历史失败A" not in body and "历史失败B" not in body)
    check("正文统计为 2 条", "共 2 条失败记录" in body)

    print("\n[4] 发送成功后水位推进：再次运行不重复发送")
    scheduler_module.daily_failure_report_job()
    check("无新增失败时不重复发送", len(sent) == 1, len(sent))

    print("\n[5] 发送失败时不推进水位：下次重试补发")
    scheduler_module.send_email = lambda s, b: False
    add_log("failed", "新失败E")
    scheduler_module.daily_failure_report_job()
    check("发送失败时不推进水位", len(sent) == 1, len(sent))

    scheduler_module.send_email = fake_send
    scheduler_module.daily_failure_report_job()
    check("下次运行补发", len(sent) == 2, len(sent))
    check("补发包含新失败E", "新失败E" in sent[-1][1])

    # 清理
    engine.dispose()
    os.unlink(tmp.name)

    print("\n" + "=" * 60)
    print(f"全部通过：{_passed} 项检查")
    print("=" * 60)


if __name__ == "__main__":
    main()
