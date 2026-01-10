from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import User, Task, Announcement
from ccsa_auto.modules.announcement.service import AnnouncementService

class AdminService:
    """管理服务"""
    
    @staticmethod
    def is_admin(user_id):
        """检查是否为管理员"""
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(id=int(user_id)).first()
            return user and user.is_admin
        finally:
            db.close()
    
    @staticmethod
    def get_users():
        """获取用户列表"""
        db = SessionLocal()
        try:
            users = db.query(User).all()
            
            user_list = []
            for user in users:
                user_list.append({
                    'id': user.id,
                    'username': user.username,
                    'external_username': user.external_username,
                    'company_name': user.company_name,
                    'status': user.status,
                    'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return {
                'success': True,
                'users': user_list
            }
        finally:
            db.close()
    
    @staticmethod
    def update_user_status(user_id, status):
        """修改用户状态"""
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(id=user_id).first()
            
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            if user.username == 'admin':
                return {
                    'success': False,
                    'message': '不能修改管理员状态'
                }
            
            user.status = status
            db.commit()
            
            return {
                'success': True,
                'message': '用户状态更新成功'
            }
        except Exception as e:
            db.rollback()
            return {
                'success': False,
                'message': f"更新用户状态失败: {str(e)}"
            }
        finally:
            db.close()
    
    @staticmethod
    def delete_user(user_id):
        """删除用户"""
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(id=user_id).first()
            
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            if user.username == 'admin':
                return {
                    'success': False,
                    'message': '不能删除管理员'
                }
            
            # 删除用户相关数据
            db.query(Task).filter_by(user_id=user_id).delete()
            db.delete(user)
            db.commit()
            
            return {
                'success': True,
                'message': '用户删除成功'
            }
        except Exception as e:
            db.rollback()
            return {
                'success': False,
                'message': f"删除用户失败: {str(e)}"
            }
        finally:
            db.close()
    
    @staticmethod
    def get_all_tasks():
        """获取所有任务"""
        db = SessionLocal()
        try:
            tasks = db.query(Task).all()
            
            task_list = []
            for task in tasks:
                user = db.query(User).filter_by(id=task.user_id).first()
                task_list.append({
                    'id': task.id,
                    'user_id': task.user_id,
                    'username': user.username if user else '',
                    'task_type': task.task_type,
                    'execution_status': task.execution_status,
                    'external_status': task.external_status,
                    'result': task.result,
                    'scheduled_time': task.scheduled_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'executed_at': task.executed_at.strftime('%Y-%m-%d %H:%M:%S') if task.executed_at else None,
                    'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return {
                'success': True,
                'tasks': task_list
            }
        finally:
            db.close()
    
    @staticmethod
    def get_statistics():
        """获取平台统计数据"""
        db = SessionLocal()
        try:
            # 用户数量
            total_users = db.query(User).count()
            active_users = db.query(User).filter_by(status=0).count()
            banned_users = db.query(User).filter_by(status=1).count()
            
            # 任务数量
            total_tasks = db.query(Task).count()
            pending_tasks = db.query(Task).filter_by(execution_status='pending').count()
            completed_tasks = db.query(Task).filter_by(execution_status='completed').count()
            
            # 公告数量
            total_announcements = db.query(Announcement).count()
            
            return {
                'success': True,
                'data': {
                    'users': {
                        'total': total_users,
                        'active': active_users,
                        'banned': banned_users
                    },
                    'tasks': {
                        'total': total_tasks,
                        'pending': pending_tasks,
                        'completed': completed_tasks
                    },
                    'announcements': {
                        'total': total_announcements
                    }
                }
            }
        finally:
            db.close()
