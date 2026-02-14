from nicegui import app
from typing import Optional


class UIStore:
    """UI state management - theme, sidebar, modals, etc."""

    @staticmethod
    def get_theme() -> str:
        """Get current theme (light/dark)."""
        return app.storage.user.get("theme", "light")

    @staticmethod
    def set_theme(theme: str) -> None:
        """Set theme."""
        app.storage.user["theme"] = theme

    @staticmethod
    def is_sidebar_collapsed() -> bool:
        """Check if sidebar is collapsed."""
        return app.storage.user.get("sidebar_collapsed", False)

    @staticmethod
    def toggle_sidebar() -> bool:
        """Toggle sidebar collapsed state. Returns new state."""
        current = UIStore.is_sidebar_collapsed()
        app.storage.user["sidebar_collapsed"] = not current
        return not current

    @staticmethod
    def get_active_page() -> str:
        """Get currently active page."""
        return app.storage.user.get("active_page", "dashboard")

    @staticmethod
    def set_active_page(page: str) -> None:
        """Set active page."""
        app.storage.user["active_page"] = page

    @staticmethod
    def get_notifications() -> list:
        """Get notification list."""
        return app.storage.user.get("notifications", [])

    @staticmethod
    def add_notification(notification: dict) -> None:
        """Add a notification."""
        notifications = UIStore.get_notifications()
        notifications.append(
            {"id": app.storage.user.get("notification_id", 0) + 1, **notification}
        )
        app.storage.user["notification_id"] = notification.get("id", 0) + 1
        app.storage.user["notifications"] = notifications

    @staticmethod
    def clear_notifications() -> None:
        """Clear all notifications."""
        app.storage.user["notifications"] = []

    @staticmethod
    def get_loading_state(key: str) -> bool:
        """Get loading state for a specific component."""
        return app.storage.user.get(f"loading_{key}", False)

    @staticmethod
    def set_loading_state(key: str, loading: bool) -> None:
        """Set loading state for a specific component."""
        app.storage.user[f"loading_{key}"] = loading

    @staticmethod
    def get_toast() -> Optional[dict]:
        """Get current toast message."""
        return app.storage.user.get("toast")

    @staticmethod
    def show_toast(
        message: str, toast_type: str = "info", duration: int = 3000
    ) -> None:
        """Show a toast message."""
        app.storage.user["toast"] = {
            "message": message,
            "type": toast_type,
            "duration": duration,
        }

    @staticmethod
    def hide_toast() -> None:
        """Hide toast message."""
        app.storage.user["toast"] = None
