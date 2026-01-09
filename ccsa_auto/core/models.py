from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from ccsa_auto.core.database import Base

class User(Base):
    """用户模型"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(100))
    external_username = Column(String(100))  # 外部平台用户名
    external_password = Column(String(255))  # 外部平台密码（加密存储）
    company_name = Column(String(255))  # 公司名称
    status = Column(Integer, default=0)  # 状态(0:正常, 1:封号)
    is_admin = Column(Boolean, default=False)  # 是否为管理员
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    tasks = relationship('Task', backref='user', lazy=True)
    announcement_reads = relationship('AnnouncementRead', backref='user', lazy=True)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'nickname': self.nickname,
            'external_username': self.external_username,
            'company_name': self.company_name,
            'status': self.status,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Task(Base):
    """任务模型"""
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    task_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    task_data = Column(Text)  # 任务数据
    execution_status = Column(String(20), default='pending')  # pending, running, completed
    external_status = Column(String(20), default='unknown')  # success, failed, unknown
    result = Column(Text)  # 执行结果
    scheduled_time = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'task_type': self.task_type,
            'task_data': self.task_data,
            'execution_status': self.execution_status,
            'external_status': self.external_status,
            'result': self.result,
            'scheduled_time': self.scheduled_time.isoformat(),
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Announcement(Base):
    """公告模型"""
    __tablename__ = 'announcements'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    reads = relationship('AnnouncementRead', backref='announcement', lazy=True)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class AnnouncementRead(Base):
    """公告阅读记录模型"""
    __tablename__ = 'announcement_reads'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    announcement_id = Column(Integer, ForeignKey('announcements.id'), nullable=False)
    read_at = Column(DateTime, default=datetime.utcnow)
    
    # 联合唯一约束
    __table_args__ = (
        UniqueConstraint('user_id', 'announcement_id', name='_user_announcement_uc'),
    )

class OperationLog(Base):
    """操作日志模型"""
    __tablename__ = 'operation_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    operation_type = Column(String(50), nullable=False)
    operation_content = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
