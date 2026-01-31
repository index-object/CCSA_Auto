import requests
from datetime import datetime, timedelta

from ccsa_auto.core.config import Config
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import Task
from ccsa_auto.utils.timezone import (
    get_current_time,
    shanghai_to_utc,
    SHANGHAI_TZ,
)
from ccsa_auto.core.logger import setup_logger

logger = setup_logger(__name__)


class TaskService:
    """任务服务"""

    @staticmethod
    def generate_random_time(hour_range, minute_range=(0, 59)):
        """
        生成随机时间

        Args:
            hour_range: 小时范围元组 (min_hour, max_hour)
            minute_range: 分钟范围元组 (min_minute, max_minute)，默认0-59

        Returns:
            tuple: (hour, minute) 随机生成的小时和分钟
        """
        import random

        min_hour, max_hour = hour_range
        min_minute, max_minute = minute_range

        # 生成随机小时和分钟
        hour = random.randint(min_hour, max_hour)
        minute = random.randint(min_minute, max_minute)

        return hour, minute

    @staticmethod
    def execute_daily_question(access_token, user_id, user_name="未知"):
        """
        执行每日一题

        Args:
            access_token: 访问令牌
            user_id: 用户ID
            user_name: 用户姓名
        """
        try:
            import random
            import json

            logger.info(f"每日一题开始执行，用户：{user_name}({user_id})")

            study_url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"]["GET_STUDY_LIST"]
            study_headers = {
                "Authorization": f"Bearer {access_token}",
                **Config.EXTERNAL_PLATFORM["HEADERS"],
            }

            study_response = requests.get(study_url, headers=study_headers)
            study_response_json = study_response.json()

            if study_response_json.get("code") != 200:
                error_msg = f"获取每日一学列表失败：{study_response_json.get('msg', '未知错误')}"
                logger.error(error_msg)
                return {"success": False, "message": error_msg}

            study_data = study_response_json.get("data", {})
            daily_info = study_data.get("regularStudyDayInfo", {})
            study_id = daily_info.get("id")

            if not study_id:
                error_msg = "未能获取每日一学ID"
                logger.error(error_msg)
                return {"success": False, "message": error_msg}

            # 2. 获取试题信息
            question_url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"][
                "GET_DAILY_QUESTIONS"
            ]
            question_params = {
                "examAssociationId": study_id,
                "isReExam": 0,
                "regularStudyType": 1,
                "isRepair": 0,
            }

            question_response = requests.get(
                question_url, params=question_params, headers=study_headers
            )
            question_response_json = question_response.json()

            if question_response_json.get("code") != 200:
                error_msg = question_response_json.get("msg", "未知错误")
                if "您已完成此考试！" in error_msg:
                    logger.info(f"每日一题已完成，用户：{user_name}({user_id})")

                    from ccsa_auto.modules.task.score_tracker import ScoreTracker
                    from ccsa_auto.modules.task.score_strategy import ScoreStrategy

                    score_strategy = ScoreStrategy.calculate_strategy(
                        user_id, "daily", 0, 0.0
                    )

                    ScoreTracker.record_score(
                        user_id=user_id,
                        task_id=None,
                        task_type="daily",
                        total_questions=0,
                        correct_questions=score_strategy["correct_questions"],
                        score=score_strategy["score"],
                        max_score=score_strategy["max_score"],
                    )

                    return {
                        "success": True,
                        "message": f"每日一题已完成：{error_msg}",
                        "result": question_response_json.get("data", {}),
                        "score_strategy": score_strategy,
                    }
                else:
                    logger.error(f"获取试题信息失败：{error_msg}")
                    return {
                        "success": False,
                        "message": f"获取试题信息失败：{error_msg}",
                    }

            question_data = question_response_json.get("data", {})
            question_list = question_data.get("questionList", [])

            questions = [
                {
                    "id": question.get("id"),
                    "questionType": question.get("questionType"),
                    "questionPoint": question.get("questionPoint"),
                    "questionAnswer": question.get("questionAnswera", "").strip('"'),
                }
                for question in question_list
            ]

            from ccsa_auto.modules.task.score_strategy import ScoreStrategy

            questions, score_strategy = ScoreStrategy.modify_answers_for_score_control(
                questions, "daily", user_id
            )
            logger.info(
                f"每日一题获取{len(questions)}道试题，控分策略：{score_strategy['score']}/{score_strategy['max_score']}，用户：{user_name}({user_id})"
            )

            # 3. 准备提交数据
            use_time = random.randint(120, 300)  # 随机生成 2~5 分钟的答题时间
            payload = {
                "practiceRegularId": study_id,
                "regularType": 2,
                "useTime": use_time,
                "isAgain": 0,
                "examType": 1,
                "isRepair": None,
                "courseExamAnswerInfoBos": questions,
                "fullPoint": 20,
                "examDuration": 30,
            }

            submit_url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"]["SUBMIT_EXAM"]
            submit_headers = {
                "Authorization": f"Bearer {access_token}",
                **Config.EXTERNAL_PLATFORM["HEADERS"],
                "Content-Type": "application/json;charset=UTF-8",
            }

            submit_response = requests.post(
                submit_url, headers=submit_headers, data=json.dumps(payload)
            )
            submit_json = submit_response.json()

            if submit_json.get("code") == 200:
                from ccsa_auto.modules.task.score_tracker import ScoreTracker

                ScoreTracker.record_score(
                    user_id=user_id,
                    task_id=None,
                    task_type="daily",
                    total_questions=len(questions),
                    correct_questions=score_strategy["correct_questions"],
                    score=score_strategy["score"],
                    max_score=score_strategy["max_score"],
                )

                logger.info(
                    f"每日一题完成，得分：{score_strategy['score']}/{score_strategy['max_score']}，用户：{user_name}({user_id})"
                )
                return {
                    "success": True,
                    "message": "每日一题执行成功",
                    "result": submit_json.get("data", {}),
                    "score_strategy": score_strategy,
                }
            else:
                error_msg = submit_json.get("msg", "未知错误")
                if "您已完成此考试！" in error_msg:
                    logger.info(f"每日一题已完成，用户：{user_name}({user_id})")

                    from ccsa_auto.modules.task.score_tracker import ScoreTracker

                    ScoreTracker.record_score(
                        user_id=user_id,
                        task_id=None,
                        task_type="daily",
                        total_questions=len(questions),
                        correct_questions=score_strategy["correct_questions"],
                        score=score_strategy["score"],
                        max_score=score_strategy["max_score"],
                    )

                    return {
                        "success": True,
                        "message": f"每日一题已完成：{error_msg}",
                        "result": submit_json.get("data", {}),
                        "score_strategy": score_strategy,
                    }
                else:
                    logger.error(
                        f"每日一题提交失败：{error_msg}，用户：{user_name}({user_id})"
                    )
                    return {"success": False, "message": f"提交答案失败：{error_msg}"}

        except Exception as e:
            error_msg = f"每日一题异常：{str(e)}"
            logger.exception(error_msg)
            return {"success": False, "message": error_msg}

    @staticmethod
    def get_weekly_lesson_details(access_token, lesson_id):
        """
        获取每周一课详细信息

        Args:
            access_token: 访问令牌
            lesson_id: 课程ID

        Returns:
            dict: 课程详细信息
        """
        try:
            url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"]["GET_WEEKLY_LESSON"].format(
                lesson_id=lesson_id
            )
            params = {"id": lesson_id}
            headers = {
                "Authorization": f"Bearer {access_token}",
                **Config.EXTERNAL_PLATFORM["HEADERS"],
            }

            response = requests.get(url, headers=headers, params=params)
            response_json = response.json()

            if response_json.get("code") != 200:
                error_msg = (
                    f"获取每周一课详情失败：{response_json.get('msg', '未知错误')}"
                )
                logger.error(error_msg)
                return {"success": False, "message": error_msg}

            lesson_info = response_json.get("data", {})

            return {
                "success": True,
                "data": {
                    "resourceDuration": lesson_info.get("resourceDuration"),
                    "resourceId": lesson_info.get("resourceId"),
                    "resourceUrl": lesson_info.get("resourceUrl"),
                    "resourceName": lesson_info.get("resourceName"),
                    "lesson_id": lesson_info.get("id"),
                },
            }

        except Exception as e:
            error_msg = f"获取每周一课详情异常：{str(e)}"
            logger.exception(error_msg)
            return {"success": False, "message": error_msg}

    @staticmethod
    def get_video_url(access_token, vod_id, resource_relation_id):
        """
        获取视频链接

        Args:
            access_token: 访问令牌
            vod_id: 视频ID
            resource_relation_id: 资源关联ID

        Returns:
            dict: 视频链接信息
        """
        try:
            url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"]["GET_VIDEO_URL"]
            headers = {
                "Authorization": f"Bearer {access_token}",
                **Config.EXTERNAL_PLATFORM["HEADERS"],
                "Content-Type": "application/json;charset=UTF-8",
            }
            payload = {
                "vodId": vod_id,
                "getPlayType": 2,
                "resourceRelationId": resource_relation_id,
                "courseType": 4,
            }

            response = requests.post(url, headers=headers, json=payload)
            response_json = response.json()

            if response_json.get("code") != 200:
                error_msg = f"获取视频链接失败：{response_json.get('msg', '未知错误')}"
                logger.error(error_msg)
                return {"success": False, "message": error_msg}

            return {"success": True, "data": response_json.get("data", {})}

        except Exception as e:
            error_msg = f"获取视频链接异常：{str(e)}"
            logger.exception(error_msg)
            return {"success": False, "message": error_msg}

    @staticmethod
    def execute_weekly_lesson(access_token, user_id, user_name="未知"):
        """
        执行每周一课

        Args:
            access_token: 访问令牌
            user_id: 用户ID
            user_name: 用户姓名
        """
        try:
            import random
            import json

            logger.info(f"每周一课开始执行，用户：{user_name}({user_id})")

            study_url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"]["GET_STUDY_LIST"]
            study_headers = {
                "Authorization": f"Bearer {access_token}",
                **Config.EXTERNAL_PLATFORM["HEADERS"],
            }

            study_response = requests.get(study_url, headers=study_headers)
            study_response_json = study_response.json()

            if study_response_json.get("code") != 200:
                error_msg = f"获取每周一课列表失败：{study_response_json.get('msg', '未知错误')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg,
                }

            study_data = study_response_json.get("data", {})
            week_info = study_data.get("repeatCourseWeekInfo", {})
            week_id = week_info.get("id")

            if not week_id:
                error_msg = "未能获取每周一课ID"
                logger.error(error_msg)
                return {"success": False, "message": error_msg}

            details_result = TaskService.get_weekly_lesson_details(
                access_token, week_id
            )
            if not details_result.get("success"):
                logger.error(f"获取课程详情失败：{details_result.get('message')}")
                return details_result

            lesson_details = details_result.get("data", {})
            resource_duration = lesson_details.get("resourceDuration", 300)
            resource_id = lesson_details.get("resourceId")
            resource_url = lesson_details.get("resourceUrl")

            if resource_url:
                video_result = TaskService.get_video_url(
                    access_token, resource_url, week_id
                )
                if not video_result.get("success"):
                    error_msg = f"获取视频链接失败：{video_result.get('message')}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "message": error_msg,
                    }

            submit_url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"][
                "SUBMIT_STUDY_SCHEDULE"
            ]
            submit_headers = {
                "Authorization": f"Bearer {access_token}",
                **Config.EXTERNAL_PLATFORM["HEADERS"],
                "Content-Type": "application/json;charset=UTF-8",
            }

            payload = {
                "studyProgressTime": resource_duration,
                "studyDuration": resource_duration,
                "studyAssociationId": week_id,
                "studyType": 4,
                "courseResourceRelationId": resource_id,
                "studySchedule": 100,
            }

            submit_response = requests.post(
                submit_url, headers=submit_headers, json=payload
            )
            submit_json = submit_response.json()

            if submit_json.get("code") == 200:
                from ccsa_auto.modules.task.score_tracker import ScoreTracker

                ScoreTracker.record_score(
                    user_id=user_id,
                    task_id=None,
                    task_type="weekly",
                    total_questions=0,
                    correct_questions=0,
                    score=50.0,
                    max_score=50.0,
                )

                logger.info(f"每周一课完成，得分：50/50，用户：{user_name}({user_id})")
                return {
                    "success": True,
                    "message": "每周一课执行成功",
                    "result": submit_json.get("data", {}),
                    "score_strategy": {
                        "correct_questions": 0,
                        "score": 50.0,
                        "max_score": 50.0,
                        "score_ratio": 1.0,
                        "reason": "每周一课固定50分",
                    },
                }
            else:
                error_msg = f"提交学习记录失败：{submit_json.get('msg', '未知错误')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg,
                }

        except Exception as e:
            error_msg = f"每周一课异常：{str(e)}"
            logger.exception(error_msg)
            return {"success": False, "message": error_msg}

    @staticmethod
    def execute_monthly_exam(access_token, user_id):
        """
        执行每月一考
        """
        try:
            import random
            import json

            # 1. 获取每月一考列表
            study_url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"]["GET_STUDY_LIST"]
            study_headers = {
                "Authorization": f"Bearer {access_token}",
                **Config.EXTERNAL_PLATFORM["HEADERS"],
            }

            study_response = requests.get(study_url, headers=study_headers)
            study_response_json = study_response.json()

            if study_response_json.get("code") != 200:
                return {
                    "success": False,
                    "message": f"获取每月一考列表失败: {study_response_json.get('msg', '未知错误')}",
                }

            # 提取每月一考信息
            study_data = study_response_json.get("data", {})
            month_info = study_data.get("regularExamMonthInfo", {})
            month_id = month_info.get("id")

            if not month_id:
                return {"success": False, "message": "未能获取每月一考ID"}

            # 2. 获取试题信息
            question_url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"][
                "GET_MONTHLY_QUESTIONS"
            ]
            question_params = {
                "examAssociationId": month_id,
                "isReExam": 0,
                "regularStudyType": 2,
                "isRepair": 0,
            }

            question_response = requests.get(
                question_url, params=question_params, headers=study_headers
            )
            question_response_json = question_response.json()

            if question_response_json.get("code") != 200:
                error_msg = question_response_json.get("msg", "未知错误")
                # 检查是否包含"您已完成此考试！"的消息，如果是则视为成功
                if "您已完成此考试！" in error_msg:
                    logger.info(f"检测到已完成考试消息: {error_msg}，视为任务成功")

                    # 记录得分（即使已完成，也记录得分）
                    from ccsa_auto.modules.task.score_tracker import ScoreTracker
                    from ccsa_auto.modules.task.score_strategy import ScoreStrategy

                    # 获取控分策略
                    score_strategy = ScoreStrategy.calculate_strategy(
                        user_id, "monthly", 0, 0.0
                    )

                    ScoreTracker.record_score(
                        user_id=user_id,
                        task_id=None,
                        task_type="monthly",
                        total_questions=0,
                        correct_questions=score_strategy["correct_questions"],
                        score=score_strategy["score"],
                        max_score=score_strategy["max_score"],
                    )

                    return {
                        "success": True,
                        "message": f"每月一考已完成: {error_msg}",
                        "result": question_response_json.get("data", {}),
                        "score_strategy": score_strategy,
                    }
                else:
                    return {
                        "success": False,
                        "message": f"获取试题信息失败: {error_msg}",
                    }

            # 封装试题数据
            question_data = question_response_json.get("data", {})
            question_list = question_data.get("questionList", [])

            questions = [
                {
                    "id": question.get("id"),
                    "questionType": question.get("questionType"),
                    "questionPoint": question.get("questionPoint"),
                    "questionAnswer": question.get("questionAnswera", "").strip(
                        '"'
                    ),  # 去掉答案的引号
                }
                for question in question_list
            ]

            # 应用控分策略
            from ccsa_auto.modules.task.score_strategy import ScoreStrategy

            questions, score_strategy = ScoreStrategy.modify_answers_for_score_control(
                questions, "monthly", user_id
            )
            logger.info(
                f"控分策略: {score_strategy['reason']}, 预期得分: {score_strategy['score']}/{score_strategy['max_score']}"
            )

            # 3. 准备提交数据
            use_time = random.randint(300, 500)  # 随机生成答题时间
            payload = {
                "practiceRegularId": month_id,
                "regularType": 2,
                "useTime": use_time,
                "isAgain": 0,
                "examType": 2,
                "isRepair": None,
                "courseExamAnswerInfoBos": questions,
                "fullPoint": 100,
                "examDuration": 80,
            }

            # 4. 提交答案
            submit_url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"]["SUBMIT_EXAM"]
            submit_headers = {
                "Authorization": f"Bearer {access_token}",
                **Config.EXTERNAL_PLATFORM["HEADERS"],
                "Content-Type": "application/json;charset=UTF-8",
            }

            submit_response = requests.post(
                submit_url, headers=submit_headers, data=json.dumps(payload)
            )
            submit_json = submit_response.json()

            if submit_json.get("code") == 200:
                # 记录得分
                from ccsa_auto.modules.task.score_tracker import ScoreTracker

                ScoreTracker.record_score(
                    user_id=user_id,
                    task_id=None,
                    task_type="monthly",
                    total_questions=len(questions),
                    correct_questions=score_strategy["correct_questions"],
                    score=score_strategy["score"],
                    max_score=score_strategy["max_score"],
                )

                return {
                    "success": True,
                    "message": "每月一考执行成功",
                    "result": submit_json.get("data", {}),
                    "score_strategy": score_strategy,
                }
            else:
                error_msg = submit_json.get("msg", "未知错误")
                # 检查是否包含"您已完成此考试！"的消息，如果是则视为成功
                if "您已完成此考试！" in error_msg:
                    logger.info(f"检测到已完成考试消息: {error_msg}，视为任务成功")

                    # 记录得分（即使已完成，也记录得分）
                    from ccsa_auto.modules.task.score_tracker import ScoreTracker

                    ScoreTracker.record_score(
                        user_id=user_id,
                        task_id=None,
                        task_type="monthly",
                        total_questions=len(questions),
                        correct_questions=score_strategy["correct_questions"],
                        score=score_strategy["score"],
                        max_score=score_strategy["max_score"],
                    )

                    return {
                        "success": True,
                        "message": f"每月一考已完成: {error_msg}",
                        "result": submit_json.get("data", {}),
                        "score_strategy": score_strategy,
                    }
                else:
                    return {
                        "success": False,
                        "message": f"提交考试答案失败: {error_msg}",
                    }

        except Exception as e:
            return {"success": False, "message": f"执行每月一考异常: {str(e)}"}

    @staticmethod
    def execute_task(task, user, max_retries=2):
        """
        执行任务（带令牌自动刷新重试）

        Args:
            task: 任务对象
            user: 用户对象
            max_retries: 最大重试次数（包括令牌刷新）

        Returns:
            dict: 执行结果
        """
        for attempt in range(max_retries):
            try:
                # 1. 验证外部平台账号
                if not user.external_username or not user.external_password:
                    return {"success": False, "message": "未设置外部平台账号信息"}

                # 2. 获取有效的外部平台令牌（优先使用已保存的令牌）
                # 如果是重试且不是第一次尝试，强制刷新令牌
                force_refresh = attempt > 0
                access_token = AuthService.get_valid_external_token(
                    user.id, force_refresh=force_refresh
                )

                # 如果令牌获取失败，尝试重新登录
                if access_token is None:
                    logger.info(f"用户 {user.id} 没有有效令牌，尝试重新登录...")
                    # authenticate_external returns (success, user_info, token) when return_error_info=False
                    auth_result = AuthService.authenticate_external(
                        user.external_username, user.external_password
                    )
                    if not auth_result[0]:  # Check success flag
                        return {"success": False, "message": "外部平台认证失败"}
                    access_token = auth_result[2]  # Get token from tuple

                    # 保存新获取的令牌
                    if access_token:
                        AuthService.save_external_token(user.id, access_token)

                # 3. 执行任务
                user_name = user.name if user else "未知"
                if task.task_type == "daily":
                    result = TaskService.execute_daily_question(
                        access_token, user.id, user_name
                    )
                elif task.task_type == "weekly":
                    result = TaskService.execute_weekly_lesson(
                        access_token, user.id, user_name
                    )
                elif task.task_type == "monthly":
                    result = TaskService.execute_monthly_exam(access_token, user.id)
                else:
                    return {"success": False, "message": "任务类型无效"}

                # 4. 检查结果，如果是认证错误则重试
                if not result.get("success"):
                    error_msg = result.get("message", "")
                    # 检查是否是认证相关错误
                    if any(
                        keyword in error_msg
                        for keyword in [
                            "认证",
                            "token",
                            "auth",
                            "Auth",
                            "Token",
                            "未授权",
                            "无权限",
                        ]
                    ):
                        logger.info(
                            f"检测到认证错误: {error_msg}，尝试刷新令牌并重试..."
                        )
                        if attempt < max_retries - 1:
                            continue  # 继续下一次重试

                return result
            except Exception as e:
                logger.exception(f"执行任务异常: {str(e)}")
                error_msg = str(e)
                # 检查是否是认证相关异常
                if any(
                    keyword in error_msg
                    for keyword in [
                        "认证",
                        "token",
                        "auth",
                        "Auth",
                        "Token",
                        "未授权",
                        "无权限",
                    ]
                ):
                    logger.info(f"检测到认证异常: {error_msg}，尝试刷新令牌并重试...")
                    if attempt < max_retries - 1:
                        continue  # 继续下一次重试

                return {"success": False, "message": f"执行任务异常: {str(e)}"}

        # 所有重试都失败
        return {"success": False, "message": f"任务执行失败，已重试{max_retries}次"}

    @staticmethod
    def create_default_tasks_for_user(user_id):
        """
        为用户创建默认任务（每日一题、每周一课、每月一考）

        Args:
            user_id: 用户ID

        Returns:
            list: 创建的任务列表
        """
        db = SessionLocal()
        try:
            logger.info(f"为用户 {user_id} 创建默认任务")

            # 从配置中获取默认任务配置
            default_tasks = [
                {
                    "task_type": "daily",
                    "task_name": Config.TASK_DETAILS["DAILY"]["name"],
                    "description": Config.TASK_DETAILS["DAILY"]["description"],
                    "cron_expression": Config.TASK_SCHEDULE["DAILY"],
                },
                {
                    "task_type": "weekly",
                    "task_name": Config.TASK_DETAILS["WEEKLY"]["name"],
                    "description": Config.TASK_DETAILS["WEEKLY"]["description"],
                    "cron_expression": Config.TASK_SCHEDULE["WEEKLY"],
                },
                {
                    "task_type": "monthly",
                    "task_name": Config.TASK_DETAILS["MONTHLY"]["name"],
                    "description": Config.TASK_DETAILS["MONTHLY"]["description"],
                    "cron_expression": Config.TASK_SCHEDULE["MONTHLY"],
                },
            ]

            created_tasks = []

            for task_config in default_tasks:
                # 检查是否已存在相同类型的任务
                existing_task = (
                    db.query(Task)
                    .filter_by(user_id=user_id, task_type=task_config["task_type"])
                    .first()
                )

                if existing_task:
                    logger.info(
                        f"用户 {user_id} 的 {task_config['task_name']} 任务已存在，跳过创建"
                    )
                    continue

                # 计算下次运行时间（使用配置中的随机时间范围）
                now_shanghai = get_current_time()
                next_run_time = None

                if task_config["task_type"] == "daily":
                    # 每天7-11点之间随机时间
                    hour_range = Config.TASK_DETAILS["DAILY"]["hour_range"]
                    minute_range = Config.TASK_DETAILS["DAILY"]["minute_range"]

                    # 生成随机时间
                    hour, minute = TaskService.generate_random_time(
                        hour_range, minute_range
                    )

                    # 计算今天的执行时间（上海时间）
                    today_execution = datetime(
                        now_shanghai.year,
                        now_shanghai.month,
                        now_shanghai.day,
                        hour,
                        minute,
                        0,
                    ).replace(tzinfo=SHANGHAI_TZ)

                    # 如果当前时间已经过了今天的执行时间，则使用明天的时间
                    if now_shanghai >= today_execution:
                        next_run_date = now_shanghai.date() + timedelta(days=1)
                    else:
                        next_run_date = now_shanghai.date()

                    next_run_shanghai = datetime(
                        next_run_date.year,
                        next_run_date.month,
                        next_run_date.day,
                        hour,
                        minute,
                        0,
                    ).replace(tzinfo=SHANGHAI_TZ)
                    next_run_time = shanghai_to_utc(next_run_shanghai)

                elif task_config["task_type"] == "weekly":
                    # 每周二8-11点之间随机时间
                    weekday = Config.TASK_DETAILS["WEEKLY"]["weekday"]  # 2=周二
                    hour_range = Config.TASK_DETAILS["WEEKLY"]["hour_range"]
                    minute_range = Config.TASK_DETAILS["WEEKLY"]["minute_range"]

                    # 生成随机时间
                    hour, minute = TaskService.generate_random_time(
                        hour_range, minute_range
                    )

                    # 计算距离下周二还有多少天（基于上海时间）
                    days_until_target = (weekday - now_shanghai.weekday()) % 7

                    # 计算目标日期的执行时间（上海时间）
                    target_execution = datetime(
                        now_shanghai.year,
                        now_shanghai.month,
                        now_shanghai.day,
                        hour,
                        minute,
                        0,
                    ).replace(tzinfo=SHANGHAI_TZ)

                    if days_until_target == 0:
                        # 如果是今天，检查是否已经过了执行时间
                        if now_shanghai >= target_execution:
                            days_until_target = 7  # 下周的这一天

                    target_date = now_shanghai.date() + timedelta(
                        days=days_until_target
                    )
                    target_execution = datetime(
                        target_date.year,
                        target_date.month,
                        target_date.day,
                        hour,
                        minute,
                        0,
                    ).replace(tzinfo=SHANGHAI_TZ)
                    next_run_time = shanghai_to_utc(target_execution)

                elif task_config["task_type"] == "monthly":
                    # 每月15日9-15点之间随机时间
                    day = Config.TASK_DETAILS["MONTHLY"]["day"]
                    hour_range = Config.TASK_DETAILS["MONTHLY"]["hour_range"]
                    minute_range = Config.TASK_DETAILS["MONTHLY"]["minute_range"]

                    # 生成随机时间
                    hour, minute = TaskService.generate_random_time(
                        hour_range, minute_range
                    )

                    # 计算下个月15日（基于上海时间）
                    if now_shanghai.month == 12:
                        next_year = now_shanghai.year + 1
                        next_month = 1
                    else:
                        next_year = now_shanghai.year
                        next_month = now_shanghai.month + 1

                    # 创建下个月15日的时间（上海时间）
                    next_run_shanghai = datetime(
                        next_year, next_month, day, hour, minute, 0
                    ).replace(tzinfo=SHANGHAI_TZ)

                    # 如果当前日期是15日且还未到执行时间，则使用本月的15日
                    if now_shanghai.day == day:
                        today_execution = datetime(
                            now_shanghai.year, now_shanghai.month, day, hour, minute, 0
                        ).replace(tzinfo=SHANGHAI_TZ)
                        if now_shanghai < today_execution:
                            next_run_shanghai = today_execution

                    next_run_time = shanghai_to_utc(next_run_shanghai)

                # 创建新任务
                new_task = Task(
                    user_id=user_id,
                    task_type=task_config["task_type"],
                    task_name=task_config["task_name"],
                    description=task_config["description"],
                    cron_expression=task_config["cron_expression"],
                    is_active=True,
                    task_data="{}",  # 空JSON
                    execution_status="pending",
                    external_status="unknown",
                    scheduled_time=datetime.utcnow(),
                    next_run_time=next_run_time,
                )

                db.add(new_task)
                created_tasks.append(new_task)
                logger.info(
                    f"为用户 {user_id} 创建 {task_config['task_name']} 任务成功"
                )

            db.commit()

            # 刷新任务对象以获取ID
            for task in created_tasks:
                db.refresh(task)

            # 将新创建的任务添加到调度器
            from ccsa_auto.modules.task.scheduler import add_task_to_scheduler

            for task in created_tasks:
                try:
                    add_task_to_scheduler(task.id)
                    logger.info(f"任务 {task.id} 已添加到调度器")
                except Exception as e:
                    logger.error(f"将任务 {task.id} 添加到调度器失败: {e}")

            logger.info(
                f"为用户 {user_id} 创建了 {len(created_tasks)} 个默认任务并已添加到调度器"
            )
            return created_tasks

        except Exception as e:
            db.rollback()
            logger.error(f"为用户 {user_id} 创建默认任务失败: {str(e)}")
            raise
        finally:
            db.close()
