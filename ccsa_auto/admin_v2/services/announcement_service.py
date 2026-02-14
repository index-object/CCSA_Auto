import logging
from typing import Dict, Any, List, Optional

from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import Announcement, AnnouncementRead, User
from ccsa_auto.modules.announcement.service import (
    AnnouncementService as BaseAnnouncementService,
)
from ccsa_auto.utils.timezone import format_datetime_for_display

logger = logging.getLogger(__name__)


class AnnouncementManagementService:
    """Announcement management service for admin_v2"""

    @staticmethod
    def get_announcements(
        keyword: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Get announcement list with search"""
        db = SessionLocal()
        try:
            query = db.query(Announcement)

            if keyword:
                query = query.filter(Announcement.title.contains(keyword))

            total = query.count()
            announcements = (
                query.order_by(Announcement.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )

            announcement_list = []
            for ann in announcements:
                # Get read count
                read_count = (
                    db.query(AnnouncementRead).filter_by(announcement_id=ann.id).count()
                )

                announcement_dict = {
                    "id": ann.id,
                    "title": ann.title,
                    "content": ann.content,
                    "read_count": read_count,
                    "created_at": format_datetime_for_display(ann.created_at),
                    "updated_at": format_datetime_for_display(ann.updated_at),
                }
                announcement_list.append(announcement_dict)

            return {
                "success": True,
                "data": announcement_list,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.exception("Failed to get announcements")
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def get_announcement_detail(announcement_id: int) -> Dict[str, Any]:
        """Get announcement detail with read statistics"""
        db = SessionLocal()
        try:
            announcement = db.query(Announcement).filter_by(id=announcement_id).first()
            if not announcement:
                return {"success": False, "message": "Announcement not found"}

            total_users = db.query(User).count()
            read_count = (
                db.query(AnnouncementRead)
                .filter_by(announcement_id=announcement_id)
                .count()
            )

            # Get recent readers
            recent_reads = (
                db.query(AnnouncementRead, User)
                .join(User, AnnouncementRead.user_id == User.id)
                .filter(AnnouncementRead.announcement_id == announcement_id)
                .order_by(AnnouncementRead.read_at.desc())
                .limit(20)
                .all()
            )

            readers = []
            for read, user in recent_reads:
                readers.append(
                    {
                        "username": user.username,
                        "read_at": format_datetime_for_display(read.read_at)
                        if read.read_at
                        else None,
                    }
                )

            announcement_detail = {
                "id": announcement.id,
                "title": announcement.title,
                "content": announcement.content,
                "total_users": total_users,
                "read_count": read_count,
                "unread_count": total_users - read_count,
                "read_rate": f"{(read_count / total_users * 100):.2f}%"
                if total_users > 0
                else "0.00%",
                "created_at": format_datetime_for_display(announcement.created_at),
                "updated_at": format_datetime_for_display(announcement.updated_at),
                "recent_readers": readers,
            }

            return {"success": True, "data": announcement_detail}
        except Exception as e:
            logger.exception("Failed to get announcement detail")
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def create_announcement(title: str, content: str) -> Dict[str, Any]:
        """Create a new announcement"""
        try:
            result = BaseAnnouncementService.create_announcement(title, content)
            return result
        except Exception as e:
            logger.exception("Failed to create announcement")
            return {"success": False, "message": str(e)}

    @staticmethod
    def update_announcement(
        announcement_id: int, title: str, content: str
    ) -> Dict[str, Any]:
        """Update an announcement"""
        try:
            result = BaseAnnouncementService.update_announcement(
                announcement_id, title, content
            )
            return result
        except Exception as e:
            logger.exception("Failed to update announcement")
            return {"success": False, "message": str(e)}

    @staticmethod
    def delete_announcement(announcement_id: int) -> Dict[str, Any]:
        """Delete an announcement"""
        try:
            result = BaseAnnouncementService.delete_announcement(announcement_id)
            return result
        except Exception as e:
            logger.exception("Failed to delete announcement")
            return {"success": False, "message": str(e)}

    @staticmethod
    def get_read_stats() -> Dict[str, Any]:
        """Get announcement read statistics"""
        try:
            result = BaseAnnouncementService.get_announcement_stats()
            return result
        except Exception as e:
            logger.exception("Failed to get read stats")
            return {"success": False, "message": str(e)}
