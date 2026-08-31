import json
import os
import smtplib
import ssl
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr

from loguru import logger

_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "email_config.json",
)


def _load_config():
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if not (cfg.get("smtp_user") and cfg.get("smtp_auth_code") and cfg.get("to")):
            return None
        return cfg
    except Exception:
        return None


def send_email(subject: str, body: str) -> bool:
    """发送邮件。配置缺失或发送失败时仅记日志，返回 False，不抛异常。"""
    cfg = _load_config()
    if not cfg:
        logger.warning("邮件提醒未启用：email_config.json 缺失或配置不完整")
        return False

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((cfg["smtp_user"], cfg["smtp_user"]))
    msg["To"] = ", ".join(cfg["to"])

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            cfg["smtp_host"], cfg["smtp_port"], context=context, timeout=15
        ) as server:
            server.login(cfg["smtp_user"], cfg["smtp_auth_code"])
            server.sendmail(cfg["smtp_user"], cfg["to"], msg.as_string())
        logger.info(f"发送邮件成功: {subject}")
        return True
    except Exception as e:
        logger.error(f"发送邮件失败: {e}")
        return False
