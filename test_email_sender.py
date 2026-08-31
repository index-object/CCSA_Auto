# -*- coding: utf-8 -*-
"""邮件发送测试 - 实际发送一封测试邮件验证 SMTP 链路"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from ccsa_auto.core.email_sender import send_email

if __name__ == "__main__":
    ok = send_email("[测试] 定时任务邮件提醒配置成功", "这是一封来自 CCAS_Auto 的测试邮件，收到即表示邮件通知链路正常。")
    print("发送结果:", "成功" if ok else "失败")
