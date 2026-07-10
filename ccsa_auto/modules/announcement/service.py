from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import Announcement, AnnouncementRead, User
from ccsa_auto.utils.timezone import format_datetime_for_display


class AnnouncementService:
    """公告服务"""

    @staticmethod
    def get_announcements():
        """获取所有公告"""
        db = SessionLocal()
        try:
            announcements = (
                db.query(Announcement).order_by(Announcement.created_at.desc()).all()
            )
            return {
                "success": True,
                "announcements": [
                    {
                        "id": ann.id,
                        "title": ann.title,
                        "content": ann.content,
                        "created_at": format_datetime_for_display(ann.created_at),
                    }
                    for ann in announcements
                ],
            }
        finally:
            db.close()

    @staticmethod
    def get_unread_announcements(user_id):
        """获取用户未读公告"""
        db = SessionLocal()
        try:
            # 获取用户已读公告ID
            read_announcement_ids = (
                db.query(AnnouncementRead.announcement_id)
                .filter_by(user_id=user_id)
                .all()
            )
            read_announcement_ids = [item[0] for item in read_announcement_ids]

            # 获取未读公告
            unread_announcements = (
                db.query(Announcement)
                .filter(~Announcement.id.in_(read_announcement_ids))
                .all()
            )

            return {
                "success": True,
                "announcements": [
                    {
                        "id": ann.id,
                        "title": ann.title,
                        "content": ann.content,
                        "created_at": format_datetime_for_display(ann.created_at),
                    }
                    for ann in unread_announcements
                ],
            }
        finally:
            db.close()

    @staticmethod
    def mark_as_read(announcement_id, user_id):
        """标记公告已读"""
        db = SessionLocal()
        try:
            # 检查是否已经标记过
            existing_read = (
                db.query(AnnouncementRead)
                .filter_by(user_id=user_id, announcement_id=announcement_id)
                .first()
            )

            if not existing_read:
                # 创建阅读记录
                new_read = AnnouncementRead(
                    user_id=user_id, announcement_id=announcement_id
                )
                db.add(new_read)
                db.commit()

            return {"success": True, "message": "标记已读成功"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"标记已读失败: {str(e)}"}
        finally:
            db.close()

    @staticmethod
    def create_announcement(title, content):
        """创建公告"""
        db = SessionLocal()
        try:
            new_announcement = Announcement(title=title, content=content)
            db.add(new_announcement)
            db.commit()
            db.refresh(new_announcement)

            return {"success": True, "announcement": new_announcement}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"创建公告失败: {str(e)}"}
        finally:
            db.close()

    @staticmethod
    def update_announcement(announcement_id, title, content):
        """更新公告"""
        db = SessionLocal()
        try:
            announcement = db.query(Announcement).filter_by(id=announcement_id).first()
            if not announcement:
                return {"success": False, "message": "公告不存在"}

            announcement.title = title
            announcement.content = content
            db.commit()

            return {"success": True, "message": "公告更新成功"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"更新公告失败: {str(e)}"}
        finally:
            db.close()

    @staticmethod
    def delete_announcement(announcement_id):
        """删除公告"""
        db = SessionLocal()
        try:
            announcement = db.query(Announcement).filter_by(id=announcement_id).first()
            if not announcement:
                return {"success": False, "message": "公告不存在"}

            db.query(AnnouncementRead).filter_by(
                announcement_id=announcement_id
            ).delete()
            db.delete(announcement)
            db.commit()

            return {"success": True, "message": "公告删除成功"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"删除公告失败: {str(e)}"}
        finally:
            db.close()

    @staticmethod
    def get_announcement_stats():
        """获取公告阅读统计"""
        db = SessionLocal()
        try:
            announcements = db.query(Announcement).all()
            total_users = db.query(User).count()
            stats = []

            for ann in announcements:
                read_count = (
                    db.query(AnnouncementRead).filter_by(announcement_id=ann.id).count()
                )

                stats.append(
                    {
                        "announcement_id": ann.id,
                        "title": ann.title,
                        "total_users": total_users,
                        "read_count": read_count,
                        "unread_count": total_users - read_count,
                        "read_rate": f"{(read_count / total_users * 100):.2f}%"
                        if total_users > 0
                        else "0.00%",
                    }
                )

            return {"success": True, "stats": stats}
        finally:
            db.close()
