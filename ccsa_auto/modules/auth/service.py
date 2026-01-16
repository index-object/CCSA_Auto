import sys
import os
import requests  # 添加requests库用于发送HTTP请求
import threading
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath("."))

from refactored_code.auth_module import AuthModule
from refactored_code.config import Config as RefactoredConfig

from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import User
from ccsa_auto.modules.logging.service import LoggingService
from ccsa_auto.utils.password import hash_password
from ccsa_auto.utils.jwt import create_access_token

# 用于防止配置修改冲突的锁
_config_lock = threading.Lock()


class AuthService:
    """认证服务"""

    @staticmethod
    def save_external_token(user_id, token, expires_in_hours=24):
        """保存外部平台令牌到用户记录

        Args:
            user_id: 用户ID
            token: 访问令牌
            expires_in_hours: 令牌有效期（小时），默认24小时
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return False

            user.external_token = token
            user.token_expires_at = datetime.utcnow() + timedelta(
                hours=expires_in_hours
            )
            user.last_token_refresh = datetime.utcnow()
            user.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(user)
            return True
        except Exception as e:
            print(f"保存外部令牌失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    @staticmethod
    def get_valid_external_token(user_id, force_refresh=False):
        """获取用户的有效外部令牌（如果过期或强制刷新则尝试刷新）

        Args:
            user_id: 用户ID
            force_refresh: 是否强制刷新令牌（即使令牌未过期）

        Returns:
            str: 有效令牌，如果获取失败返回None
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return None

            # 检查是否有令牌
            if not user.external_token:
                return None

            # 如果强制刷新，直接尝试重新登录
            if force_refresh:
                print(f"强制刷新用户 {user_id} 的令牌...")
                if user.external_username and user.external_password:
                    auth_success, _, new_token = AuthService.authenticate_external(
                        user.external_username, user.external_password
                    )
                    if auth_success and new_token:
                        # 保存新令牌
                        AuthService.save_external_token(user_id, new_token)
                        return new_token
                return None

            # 检查令牌是否有效
            if user.is_token_valid():
                return user.external_token

            # 令牌已过期，尝试刷新
            print(f"用户 {user_id} 的令牌已过期，尝试刷新...")
            refreshed_token = AuthService.refresh_external_token(user)
            if refreshed_token:
                return refreshed_token

            # 刷新失败，尝试重新登录
            print(f"令牌刷新失败，尝试重新登录用户 {user_id}...")
            if user.external_username and user.external_password:
                auth_success, _, new_token = AuthService.authenticate_external(
                    user.external_username, user.external_password
                )
                if auth_success and new_token:
                    # 保存新令牌
                    AuthService.save_external_token(user_id, new_token)
                    return new_token

            return None
        finally:
            db.close()

    @staticmethod
    def refresh_external_token(user):
        """刷新外部平台令牌

        Args:
            user: User对象

        Returns:
            str: 新令牌，如果刷新失败返回None
        """
        # 注意：当前外部平台可能不支持令牌刷新，这里实现为重新登录
        # 如果有刷新令牌机制，可以在这里实现
        try:
            if user.external_username and user.external_password:
                auth_success, _, new_token = AuthService.authenticate_external(
                    user.external_username, user.external_password
                )
                if auth_success and new_token:
                    # 保存新令牌
                    AuthService.save_external_token(user.id, new_token)
                    return new_token
        except Exception as e:
            print(f"刷新令牌失败: {e}")

        return None

    @staticmethod
    def authenticate_external(username, password, return_error_info=False):
        """外部平台认证

        Args:
            username: 用户名
            password: 密码
            return_error_info: 如果为True，返回元组 (success, user_info, external_token, error_info)
                              如果为False，返回元组 (success, user_info, external_token)，保持向后兼容

        Returns:
            如果return_error_info为False: tuple (bool, dict, str) - (成功状态, 用户信息, 访问令牌)
            如果return_error_info为True: tuple (bool, dict, str, dict) - 第四个元素是错误信息字典
        """
        try:
            # 创建认证模块实例
            auth_module = AuthModule()

            # 创建独立的登录数据副本，避免修改全局配置
            login_data = RefactoredConfig.LOGIN_DATA.copy()
            login_data["username"] = username
            login_data["password"] = password

            # 临时修改认证模块的登录数据
            # 由于AuthModule直接使用Config.LOGIN_DATA，我们需要修改Config类
            # 使用锁保护配置修改，防止多个线程同时修改配置
            with _config_lock:
                # 保存原始配置
                original_username = RefactoredConfig.LOGIN_DATA["username"]
                original_password = RefactoredConfig.LOGIN_DATA["password"]

                try:
                    # 临时修改配置
                    RefactoredConfig.LOGIN_DATA["username"] = username
                    RefactoredConfig.LOGIN_DATA["password"] = password

                    # 尝试登录，获取详细错误信息
                    success, error_info = auth_module.login(return_error_info=True)

                    if success:
                        # 获取用户信息
                        user_info = AuthService.get_user_info(auth_module)
                        if return_error_info:
                            return True, user_info, auth_module.access_token, None
                        else:
                            return True, user_info, auth_module.access_token
                    else:
                        if return_error_info:
                            return False, None, None, error_info
                        else:
                            return False, None, None
                finally:
                    # 恢复原始配置
                    RefactoredConfig.LOGIN_DATA["username"] = original_username
                    RefactoredConfig.LOGIN_DATA["password"] = original_password

        except Exception as e:
            print(f"外部平台认证失败: {e}")
            error_info = {
                "code": 500,
                "msg": f"外部平台认证失败: {str(e)}",
                "data": None,
            }
            if return_error_info:
                return False, None, None, error_info
            else:
                return False, None, None

    @staticmethod
    def get_user_info(auth_module):
        """获取用户信息"""
        try:
            # 调用API获取用户信息
            headers = {
                "accept": "application/json, text/plain, */*",
                "authorization": f"Bearer {auth_module.access_token}",
                "clientid": RefactoredConfig.CLIENT_ID,
                "content-language": "zh_CN",
            }
            response = requests.get(
                f"{RefactoredConfig.BASE_URL}/system/app/userExtend/v2/getUserInfo",
                headers=headers,
            )
            response_data = response.json()

            if response.status_code == 200 and response_data.get("code") == 200:
                data = response_data.get("data", {})
                return {
                    "username": data.get("nickName", ""),
                    "company_name": data.get("companyName", ""),
                }
            else:
                print(f"获取用户信息失败: {response_data.get('msg', '未知错误')}")
                return {"username": "", "company_name": ""}
        except Exception as e:
            print(f"调用用户信息API时发生异常: {e}")
            return {"username": "", "company_name": ""}

    @staticmethod
    def auto_register(username, password, user_info=None, external_token=None):
        """自动注册用户
        Args:
            username: 用户名
            password: 密码
            user_info: 可选的用户信息，如果已从外部API获取则传入以避免重复调用
            external_token: 可选的访问令牌，如果已从外部API获取则传入
        """
        # 检查是否为管理员账号，管理员不通过此函数注册
        if username == "admin":
            return None

        db = SessionLocal()
        try:
            # 检查用户是否已存在
            existing_user = db.query(User).filter_by(username=username).first()

            # 如果用户已存在，更新公司信息（如果提供了user_info）
            if existing_user:
                if user_info and user_info.get("company_name"):
                    existing_user.company_name = user_info.get("company_name")

                if user_info and user_info.get("username"):
                    existing_user.external_username = user_info.get("username")

                if external_token:
                    existing_user.external_token = external_token
                    existing_user.token_expires_at = datetime.utcnow() + timedelta(
                        hours=24
                    )
                    existing_user.last_token_refresh = datetime.utcnow()

                db.commit()
                db.refresh(existing_user)
                return existing_user

            # 如果用户不存在且没有提供user_info，则需要获取用户信息
            if not user_info:
                auth_success, user_info, external_token = (
                    AuthService.authenticate_external(username, password)
                )
                if not auth_success:
                    return None

            # 创建新用户
            new_user = User(
                username=username,
                password=hash_password(password),
                external_username=username,
                external_password=password,
                company_name=user_info.get("company_name", ""),
                status=0,
                is_admin=False,  # 普通用户不是管理员
                external_token=external_token,
                token_expires_at=datetime.utcnow() + timedelta(hours=24)
                if external_token
                else None,
                last_token_refresh=datetime.utcnow() if external_token else None,
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            # 为新用户创建默认任务
            try:
                # 局部导入以避免循环导入
                from ccsa_auto.modules.task.service import TaskService

                TaskService.create_default_tasks_for_user(new_user.id)
                print(f"为用户 {new_user.id} 创建默认任务成功")
            except Exception as e:
                print(f"为用户 {new_user.id} 创建默认任务失败: {e}")
                # 任务创建失败不影响用户注册

            return new_user
        finally:
            db.close()

    @staticmethod
    def login(username, password):
        """用户登录"""
        # 首先检查是否为管理员登录
        if username == "admin":
            # 管理员使用本地数据库认证
            return AuthService.admin_login(username, password)
        else:
            # 普通用户使用外部平台认证
            return AuthService.user_login(username, password)

    @staticmethod
    def admin_login(username, password):
        """管理员登录"""
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(username=username, is_admin=True).first()
            if not user:
                LoggingService.log_auth(
                    user_id=None,
                    action="ADMIN_LOGIN",
                    success=False,
                    detail=f"管理员账号不存在: {username}",
                )
                return False, None, "管理员账号不存在"

            from ccsa_auto.utils.password import verify_password

            if not verify_password(user.password, password):
                LoggingService.log_auth(
                    user_id=user.id,
                    action="ADMIN_LOGIN",
                    success=False,
                    detail=f"密码错误: {username}",
                )
                return False, None, "密码错误"

            if user.status == 1:
                LoggingService.log_auth(
                    user_id=user.id,
                    action="ADMIN_LOGIN",
                    success=False,
                    detail=f"账号已被封禁: {username}",
                )
                return False, None, "账号已被封禁"

            access_token = create_access_token({"sub": str(user.id)})

            from ccsa_auto.modules.auth.session_manager import get_session_manager

            session_manager = get_session_manager()
            session_manager.create_db_session(user.id, access_token)

            LoggingService.log_auth(
                user_id=user.id,
                action="ADMIN_LOGIN",
                success=True,
                detail=f"管理员登录成功: {username}",
            )

            return (
                True,
                {
                    "access_token": access_token,
                    "external_token": None,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "nickname": user.nickname,
                        "company_name": user.company_name,
                        "is_admin": True,
                    },
                },
                "管理员登录成功",
            )
        finally:
            db.close()

    @staticmethod
    def user_login(username, password):
        """普通用户登录"""
        auth_success, user_info, external_token, error_info = (
            AuthService.authenticate_external(
                username, password, return_error_info=True
            )
        )
        if not auth_success:
            if error_info:
                error_msg = error_info.get("msg", "外部平台认证失败")
                error_code = error_info.get("code", "未知错误码")
                detailed_msg = f"外部平台认证失败 (错误码: {error_code}): {error_msg}"
            else:
                detailed_msg = "外部平台认证失败"

            LoggingService.log_auth(
                user_id=None,
                action="USER_LOGIN",
                success=False,
                detail=f"用户 {username} 登录失败: {detailed_msg}",
            )
            return False, None, detailed_msg

        user = AuthService.auto_register(username, password, user_info)
        if not user:
            LoggingService.log_auth(
                user_id=None,
                action="USER_LOGIN",
                success=False,
                detail=f"用户 {username} 注册失败",
            )
            return False, None, "用户注册失败"

        if user.status == 1:
            LoggingService.log_auth(
                user_id=user.id,
                action="USER_LOGIN",
                success=False,
                detail=f"用户 {username} 账号已被封禁",
            )
            return False, None, "账号已被封禁"

        if external_token:
            AuthService.save_external_token(user.id, external_token)

        access_token = create_access_token({"sub": str(user.id)})

        from ccsa_auto.modules.auth.session_manager import get_session_manager

        session_manager = get_session_manager()
        session_manager.create_db_session(user.id, access_token)

        LoggingService.log_auth(
            user_id=user.id,
            action="USER_LOGIN",
            success=True,
            detail=f"用户 {username} 登录成功",
        )

        # 使用从外部API获取的最新用户信息（特别是公司名称）
        # 注意：user_info是从外部API获取的，包含最新的nickName和companyName
        return (
            True,
            {
                "access_token": access_token,
                "external_token": external_token,
                "user": {
                    "id": user.id,
                    "username": user_info.get(
                        "username", user.username
                    ),  # 使用外部API的用户名
                    "company_name": user_info.get(
                        "company_name", user.company_name
                    ),  # 使用外部API的公司名称
                    "is_admin": False,
                },
            },
            "登录成功",
        )

    @staticmethod
    def get_scores_with_retry(user_id, max_retries=2):
        """获取用户积分信息（带令牌自动刷新重试）

        Args:
            user_id: 用户ID
            max_retries: 最大重试次数（包括令牌刷新）

        Returns:
            dict: 积分信息，如果获取失败返回None
        """
        for attempt in range(max_retries):
            try:
                # 获取有效令牌
                token = AuthService.get_valid_external_token(user_id)
                if not token:
                    print(f"获取用户 {user_id} 的令牌失败")
                    return None

                headers = {
                    "accept": "application/json, text/plain, */*",
                    "authorization": f"Bearer {token}",
                    "clientid": RefactoredConfig.CLIENT_ID,
                    "content-language": "zh_CN",
                }
                response = requests.get(
                    f"{RefactoredConfig.BASE_URL}/progress/app/regularStudyRecord/getRegularFractionInfo",
                    headers=headers,
                )

                # 检查响应状态
                if response.status_code != 200:
                    print(f"获取积分信息失败: HTTP状态码 {response.status_code}")
                    # 如果是认证失败，尝试刷新令牌
                    if response.status_code == 401 or response.status_code == 403:
                        print(f"认证失败，尝试刷新用户 {user_id} 的令牌...")
                        AuthService.get_valid_external_token(
                            user_id, force_refresh=True
                        )
                        continue
                    return None

                data = response.json()
                if data and data.get("code") == 200:
                    return {
                        "total_score": data["data"]["totalScore"],
                        "monthly_score": data["data"]["obtainScore"],
                    }
                else:
                    error_msg = data.get("msg", "未知错误") if data else "响应数据为空"
                    print(f"获取积分信息失败: {error_msg}")

                    # 检查是否是认证错误
                    if (
                        "认证" in error_msg
                        or "token" in error_msg.lower()
                        or "auth" in error_msg.lower()
                    ):
                        print(f"检测到认证错误，尝试刷新用户 {user_id} 的令牌...")
                        AuthService.get_valid_external_token(
                            user_id, force_refresh=True
                        )
                        continue

                    return None
            except Exception as e:
                print(f"调用积分信息API时发生异常: {e}")
                if attempt < max_retries - 1:
                    print(f"第 {attempt + 1} 次尝试失败，准备重试...")
                else:
                    return None

        return None

    @staticmethod
    def get_scores(token):
        """获取用户积分信息（向后兼容版本）

        Args:
            token: 访问令牌

        Returns:
            dict: 积分信息，如果获取失败返回None
        """
        try:
            headers = {
                "accept": "application/json, text/plain, */*",
                "authorization": f"Bearer {token}",
                "clientid": RefactoredConfig.CLIENT_ID,
                "content-language": "zh_CN",
            }
            response = requests.get(
                f"{RefactoredConfig.BASE_URL}/progress/app/regularStudyRecord/getRegularFractionInfo",
                headers=headers,
            )

            # 检查响应状态
            if response.status_code != 200:
                print(f"获取积分信息失败: HTTP状态码 {response.status_code}")
                return None

            data = response.json()
            if data and data.get("code") == 200:
                return {
                    "total_score": data["data"]["totalScore"],
                    "monthly_score": data["data"]["obtainScore"],
                }
            else:
                error_msg = data.get("msg", "未知错误") if data else "响应数据为空"
                print(f"获取积分信息失败: {error_msg}")
                return None
        except Exception as e:
            print(f"调用积分信息API时发生异常: {e}")
            return None

    @staticmethod
    def get_task_status_with_retry(user_id, max_retries=2):
        """获取任务完成情况（三个一：每日一题、每周一课、每月一考）（带令牌自动刷新重试）

        Args:
            user_id: 用户ID
            max_retries: 最大重试次数（包括令牌刷新）

        Returns:
            dict: 任务完成情况，如果获取失败返回None
        """
        for attempt in range(max_retries):
            try:
                # 获取有效令牌
                token = AuthService.get_valid_external_token(user_id)
                if not token:
                    print(f"获取用户 {user_id} 的令牌失败")
                    return None

                headers = {
                    "accept": "application/json, text/plain, */*",
                    "authorization": f"Bearer {token}",
                    "clientid": RefactoredConfig.CLIENT_ID,
                    "content-language": "zh_CN",
                }
                response = requests.get(
                    f"{RefactoredConfig.BASE_URL}/progress/app/regularStudy/getNewRegularStudyList",
                    headers=headers,
                )

                # 检查响应状态
                if response.status_code != 200:
                    print(f"获取任务完成情况失败: HTTP状态码 {response.status_code}")
                    # 如果是认证失败，尝试刷新令牌
                    if response.status_code == 401 or response.status_code == 403:
                        print(f"认证失败，尝试刷新用户 {user_id} 的令牌...")
                        AuthService.get_valid_external_token(
                            user_id, force_refresh=True
                        )
                        continue
                    return None

                data = response.json()
                if data and data.get("code") == 200:
                    response_data = data.get("data", {})

                    # 解析三个任务的状态
                    daily_info = response_data.get("regularStudyDayInfo", {})
                    weekly_info = response_data.get("repeatCourseWeekInfo", {})
                    monthly_info = response_data.get("regularExamMonthInfo", {})

                    # 状态映射：1=未完成，2=已完成
                    status_map = {1: "未完成", 2: "已完成"}

                    return {
                        "daily": {
                            "name": daily_info.get("studyName", "每日一题"),
                            "status": status_map.get(
                                daily_info.get("studyStatus", 1), "未知"
                            ),
                            "available_score": daily_info.get("availableScore", 0),
                            "obtained_score": daily_info.get("obtainedScore", 0),
                        },
                        "weekly": {
                            "name": weekly_info.get("courseName", "每周一课"),
                            "status": status_map.get(
                                weekly_info.get("studyStatus", 1), "未知"
                            ),
                            "available_score": weekly_info.get("availableScore", 0),
                            "obtained_score": weekly_info.get("obtainedScore", 0),
                        },
                        "monthly": {
                            "name": monthly_info.get("examName", "每月一考"),
                            "status": status_map.get(
                                monthly_info.get("studyStatus", 1), "未知"
                            ),
                            "available_score": monthly_info.get("availableScore", 0),
                            "obtained_score": monthly_info.get("obtainedScore", 0),
                        },
                    }
                else:
                    error_msg = data.get("msg", "未知错误") if data else "响应数据为空"
                    print(f"获取任务完成情况失败: {error_msg}")

                    # 检查是否是认证错误
                    if (
                        "认证" in error_msg
                        or "token" in error_msg.lower()
                        or "auth" in error_msg.lower()
                    ):
                        print(f"检测到认证错误，尝试刷新用户 {user_id} 的令牌...")
                        AuthService.get_valid_external_token(
                            user_id, force_refresh=True
                        )
                        continue

                    return None
            except Exception as e:
                print(f"调用任务完成情况API时发生异常: {e}")
                if attempt < max_retries - 1:
                    print(f"第 {attempt + 1} 次尝试失败，准备重试...")
                else:
                    return None

        return None

    @staticmethod
    def get_task_status(token):
        """获取任务完成情况（三个一：每日一题、每周一课、每月一考）（向后兼容版本）

        Args:
            token: 访问令牌

        Returns:
            dict: 任务完成情况，如果获取失败返回None
        """
        try:
            headers = {
                "accept": "application/json, text/plain, */*",
                "authorization": f"Bearer {token}",
                "clientid": RefactoredConfig.CLIENT_ID,
                "content-language": "zh_CN",
            }
            response = requests.get(
                f"{RefactoredConfig.BASE_URL}/progress/app/regularStudy/getNewRegularStudyList",
                headers=headers,
            )

            # 检查响应状态
            if response.status_code != 200:
                print(f"获取任务完成情况失败: HTTP状态码 {response.status_code}")
                return None

            data = response.json()
            if data and data.get("code") == 200:
                response_data = data.get("data", {})

                # 解析三个任务的状态
                daily_info = response_data.get("regularStudyDayInfo", {})
                weekly_info = response_data.get("repeatCourseWeekInfo", {})
                monthly_info = response_data.get("regularExamMonthInfo", {})

                # 状态映射：1=未完成，2=已完成
                status_map = {1: "未完成", 2: "已完成"}

                return {
                    "daily": {
                        "name": daily_info.get("studyName", "每日一题"),
                        "status": status_map.get(
                            daily_info.get("studyStatus", 1), "未知"
                        ),
                        "available_score": daily_info.get("availableScore", 0),
                        "obtained_score": daily_info.get("obtainedScore", 0),
                    },
                    "weekly": {
                        "name": weekly_info.get("courseName", "每周一课"),
                        "status": status_map.get(
                            weekly_info.get("studyStatus", 1), "未知"
                        ),
                        "available_score": weekly_info.get("availableScore", 0),
                        "obtained_score": weekly_info.get("obtainedScore", 0),
                    },
                    "monthly": {
                        "name": monthly_info.get("examName", "每月一考"),
                        "status": status_map.get(
                            monthly_info.get("studyStatus", 1), "未知"
                        ),
                        "available_score": monthly_info.get("availableScore", 0),
                        "obtained_score": monthly_info.get("obtainedScore", 0),
                    },
                }
            else:
                error_msg = data.get("msg", "未知错误") if data else "响应数据为空"
                print(f"获取任务完成情况失败: {error_msg}")
                return None
        except Exception as e:
            print(f"调用任务完成情况API时发生异常: {e}")
            return None
