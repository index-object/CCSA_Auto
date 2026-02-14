from nicegui import app

ADMIN_PERMISSIONS = {
    "dashboard": ["view"],
    "users": ["view", "edit", "delete", "ban"],
    "tasks": ["view", "edit", "delete", "trigger"],
    "announcements": ["view", "create", "edit", "delete", "publish"],
    "logs": ["view", "export"],
    "settings": ["view", "edit"],
}


class AdminStore:
    @staticmethod
    def get_admin_id() -> int:
        return app.storage.user.get("admin_id")

    @staticmethod
    def get_admin_username() -> str:
        return app.storage.user.get("admin_username", "")

    @staticmethod
    def get_admin_role() -> str:
        return app.storage.user.get("admin_role", "admin")

    @staticmethod
    def is_super_admin() -> bool:
        return app.storage.user.get("is_super_admin", False)

    @staticmethod
    def has_permission(permission: str) -> bool:
        permissions = app.storage.user.get("permissions", [])
        return permission in permissions or AdminStore.is_super_admin()

    @staticmethod
    def can_access(module: str, action: str = "view") -> bool:
        if AdminStore.is_super_admin():
            return True
        permissions = app.storage.user.get("permissions", [])
        module_perms = ADMIN_PERMISSIONS.get(module, [])
        return action in module_perms or module in permissions
