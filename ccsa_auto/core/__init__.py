"""CCSA Auto 核心模块"""

from ccsa_auto.core.config import Config
from ccsa_auto.core.database import Base, engine, get_db
from ccsa_auto.core.models import (
    User,
    Task,
    Announcement,
    AnnouncementRead,
    OperationLog,
    AuthSession,
    QuestionBank,
)


# 创建数据库表
def create_tables():
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
            print("默认管理员已创建")
    finally:
        db.close()
