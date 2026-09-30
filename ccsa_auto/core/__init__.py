"""CCSA Auto 核心模块"""

from ccsa_auto.core.config import Config
from ccsa_auto.core.database import Base, engine, get_db
from ccsa_auto.core.logger import get_logger
from ccsa_auto.core.models import (
    User,
    Task,
    Announcement,
    AnnouncementRead,
    OperationLog,
    AuthSession,
    QuestionBank,
)

# 注意：这里不能命名为 logger，否则会遮蔽子模块 ccsa_auto.core.logger
_logger = get_logger(__name__)


# 创建数据库表
def create_tables():
    # 日志相关表定义在 modules.logging.models，这里显式导入以注册到 Base.metadata，
    # 保证 app_logs / task_run_logs 会被 create_all 创建。
    from ccsa_auto.modules.logging import models as _logging_models  # noqa: F401

    Base.metadata.create_all(bind=engine)


# 初始化默认管理员
def init_admin():
    from sqlalchemy.orm import Session
    from ccsa_auto.utils.password import hash_password

    db = Session(engine)
    try:
        admin_user = db.query(User).filter_by(username="admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                password=hash_password("admin123"),
                nickname="管理员",
                status=0,
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()
            _logger.info("默认管理员已创建")
    finally:
        db.close()
