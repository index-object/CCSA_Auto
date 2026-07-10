from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from ccsa_auto.core.database import Base
from ccsa_auto.utils.timezone import format_datetime_for_display


class AppLog(Base):
    """统一应用日志模型"""

    __tablename__ = "app_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_type = Column(String(20), nullable=False)
    operation = Column(String(100), nullable=False)
    content = Column(Text)
    user_id = Column(Integer)
    target_type = Column(String(50))
    target_id = Column(Integer)
    ip_address = Column(String(50))
    status = Column(String(20), default="success")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "log_type": self.log_type,
            "operation": self.operation,
            "content": self.content,
            "user_id": self.user_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "ip_address": self.ip_address,
            "status": self.status,
            "created_at": format_datetime_for_display(self.created_at),
        }
