import requests
import threading
import time
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
from ccsa_auto.core.logger import get_task_logger

logger = get_task_logger(__name__)


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
    def _build_headers(access_token):
        """构造带鉴权信息的业务请求头。"""
        return {
            "Authorization": f"Bearer {access_token}",
            **Config.EXTERNAL_PLATFORM["HEADERS"],
        }

    @staticmethod
    def _normalize_question_answer(raw):
        """将平台返回的 questionAnswera 规范化为提交格式。

        平台返回值可能是 JSON 字符串（如 ``"\\"D\\""``）、列表或紧凑字符串
        （如 ``"ABD"``）。提交时统一为 ``A`` / ``A,B,C`` 形式，与前端
        ``answer.join(",")`` 以及本地题库格式保持一致。
        """
        import json
        import re

        if raw is None:
            return None

        value = raw
        if isinstance(value, str):
            text = value.strip()
            if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
                try:
                    value = json.loads(text)
                except Exception:
                    value = text
            else:
                value = text

        if isinstance(value, (list, tuple, set)):
            letters = [str(item).strip().upper() for item in value if str(item).strip()]
        elif isinstance(value, str):
            if re.fullmatch(r"[A-Za-z]+", value):
                letters = list(value.upper())
            else:
                letters = re.findall(r"[A-Za-z]", value)
        else:
            return str(value)

        # 去重并按字母排序（多选答案与顺序无关）
        letters = sorted({letter for letter in letters if letter})
        return ",".join(letters) if letters else None

    @staticmethod
    def _build_questions_from_api(question_list, fallback_exam_type):
        """由平台返回的 questionList 构造提交题目（含 bankId 与标准答案）。

        平台的 ``questionAnswera`` 即标准答案；缺失时回退到本地题库。
        """
        from ccsa_auto.core.database import SessionLocal
        from ccsa_auto.core.models import QuestionBank
        from sqlalchemy import func

        questions = []
        db = SessionLocal()
        try:
            for q in question_list or []:
                qid = q.get("id")
                qtype = q.get("questionType")
                qpoint = q.get("questionPoint", 0)
                bank_id = q.get("bankId")

                answer = TaskService._normalize_question_answer(
                    q.get("questionAnswera")
                )
                substituted = False
                if not answer:
                    bank_q = db.query(QuestionBank).filter_by(question_id=qid).first()
                    if bank_q and bank_q.question_answer:
                        answer = bank_q.question_answer
                    else:
                        sub = (
                            db.query(QuestionBank)
                            .filter_by(
                                question_type=qtype,
                                source_exam_type=fallback_exam_type,
                            )
                            .order_by(func.random())
                            .first()
                        )
                        if sub:
                            qid = sub.question_id
                            answer = sub.question_answer
                            substituted = True

                if not qid or not answer:
                    continue

                item = {
                    "id": qid,
                    "questionType": qtype,
                    "questionPoint": qpoint,
                    "questionAnswer": answer,
                }
                # 替换过题号时不再沿用原 bankId，避免题目与题库不匹配
                if bank_id and not substituted:
                    item["bankId"] = bank_id
                questions.append(item)
        finally:
            db.close()

        return questions

    @staticmethod
    def _fetch_regular_study_info(access_token, endpoint_key, label, user_name, user_id):
        """获取每日/每月/每周任务信息。

        Returns:
            dict: 成功时返回 ``{"success": True, "data": {...}}``，
                  失败时返回 ``{"success": False, "message": ...}``
        """
        url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"][endpoint_key]
        response = requests.get(url, headers=TaskService._build_headers(access_token))
        response_json = response.json()

        if response_json.get("code") != 200:
            error_msg = f"获取{label}信息失败：{response_json.get('msg', '未知错误')}"
            logger.error(f"{error_msg}，用户：{user_name}({user_id})")
            return {
                "success": False,
                "message": error_msg,
                "error_type": "PlatformApiError",
            }

        data = response_json.get("data") or {}
        if not data.get("id"):
            error_msg = f"未能获取{label}ID"
            logger.error(f"{error_msg}，用户：{user_name}({user_id}) | data={data}")
            return {
                "success": False,
                "message": error_msg,
                "error_type": "EmptyDataError",
            }

        return {"success": True, "data": data}

    @staticmethod
    def _record_completed_exam(user_id, task_type, label, user_name):
        """任务已完成时的得分记录与返回结果。"""
        from ccsa_auto.modules.task.score_strategy import ScoreStrategy
        from ccsa_auto.modules.task.score_tracker import ScoreTracker

        if ScoreStrategy.is_enabled_for(user_id):
            score_strategy = ScoreStrategy.calculate_strategy(user_id, task_type, 0, 0.0)
        else:
            score_strategy = {
                "score": 0,
                "max_score": 0,
                "correct_questions": 0,
                "wrong_questions": 0,
                "reason": "控分策略已关闭",
            }

        ScoreTracker.record_score(
            user_id=user_id,
            task_id=None,
            task_type=task_type,
            total_questions=0,
            correct_questions=score_strategy["correct_questions"],
            score=score_strategy["score"],
            max_score=score_strategy["max_score"],
        )

        logger.info(f"{label}已完成，用户：{user_name}({user_id})")
        return {
            "success": True,
            "message": f"{label}已完成",
            "result": {},
            "score_strategy": score_strategy,
        }

    @staticmethod
    def _execute_regular_exam(access_token, user_id, task_type, user_name="未知"):
        """执行每日一题(examType=1) / 每月一考(examType=2) 的通用流程。

        新版平台把每日/每月状态拆分为独立接口，且试题接口直接返回标准答案
        ``questionAnswera`` 与 ``bankId``。
        """
        import json
        import random

        is_daily = task_type == "daily"
        label = "每日一题" if is_daily else "每月一考"
        exam_type = 1 if is_daily else 2
        regular_study_type = 1 if is_daily else 2
        info_endpoint = "GET_REGULAR_STUDY_DAY" if is_daily else "GET_REGULAR_STUDY_MONTH"
        questions_endpoint = "GET_DAILY_QUESTIONS" if is_daily else "GET_MONTHLY_QUESTIONS"

        try:
            logger.info(f"{label}开始执行，用户：{user_name}({user_id})")

            # 1. 获取任务信息
            info_result = TaskService._fetch_regular_study_info(
                access_token, info_endpoint, label, user_name, user_id
            )
            if not info_result.get("success"):
                return info_result

            info = info_result["data"]
            practice_id = info["id"]

            # studyStatus：1=未完成 2=已完成
            if info.get("studyStatus") == 2:
                return TaskService._record_completed_exam(
                    user_id, task_type, label, user_name
                )

            # 2. 获取试题（含标准答案）
            question_params = {
                "examAssociationId": practice_id,
                "isReExam": 0,
                "regularStudyType": regular_study_type,
                "isRepair": 0,
                "source": 1,
            }
            question_response = requests.get(
                Config.EXTERNAL_PLATFORM["API_ENDPOINTS"][questions_endpoint],
                params=question_params,
                headers=TaskService._build_headers(access_token),
            )
            question_json = question_response.json()

            if question_json.get("code") != 200:
                error_msg = question_json.get("msg", "未知错误")
                if "您已完成此考试" in error_msg:
                    return TaskService._record_completed_exam(
                        user_id, task_type, label, user_name
                    )
                logger.error(f"获取{label}试题失败：{error_msg}，用户：{user_name}({user_id})")
                return {
                    "success": False,
                    "message": f"获取试题信息失败：{error_msg}",
                    "error_type": "QuestionFetchError",
                }

            question_data = question_json.get("data") or {}
            question_list = question_data.get("questionList") or []
            if not question_list:
                error_msg = f"{label}未返回任何试题"
                logger.error(f"{error_msg}，用户：{user_name}({user_id})")
                return {
                    "success": False,
                    "message": error_msg,
                    "error_type": "EmptyQuestionError",
                }

            questions = TaskService._build_questions_from_api(
                question_list, exam_type
            )
            if not questions:
                error_msg = f"{label}试题缺少答案，无法作答"
                logger.error(f"{error_msg}，用户：{user_name}({user_id})")
                return {
                    "success": False,
                    "message": error_msg,
                    "error_type": "NoAnswerError",
                }

            if len(questions) != len(question_list):
                logger.warning(
                    f"{label}题量变化: API {len(question_list)} 题, 实际 {len(questions)} 题, 用户：{user_name}({user_id})"
                )

            # 3. 应用控分策略
            from ccsa_auto.modules.task.score_strategy import ScoreStrategy

            if ScoreStrategy.is_enabled_for(user_id):
                questions, score_strategy = (
                    ScoreStrategy.modify_answers_for_score_control(
                        questions, task_type, user_id
                    )
                )
            else:
                max_score = sum(q.get("questionPoint", 0) for q in questions)
                score_strategy = {
                    "score": max_score,
                    "max_score": max_score,
                    "correct_questions": len(questions),
                    "wrong_questions": 0,
                    "reason": "控分策略已关闭，全部满分",
                }

            logger.info(
                f"{label}获取{len(questions)}道试题，控分策略："
                f"{score_strategy['score']}/{score_strategy['max_score']}，用户：{user_name}({user_id})"
            )

            # 4. 提交答卷
            use_time = random.randint(120, 300) if is_daily else random.randint(300, 500)
            full_point = question_data.get("questionTotalPoint")
            if full_point is None:
                full_point = sum(q.get("questionPoint", 0) for q in questions)

            payload = {
                "practiceRegularId": practice_id,
                "regularType": 2,
                "useTime": use_time,
                "isAgain": 0,
                "examType": exam_type,
                "isRepair": None,
                "courseExamAnswerInfoBos": questions,
                "fullPoint": full_point,
                "examDuration": question_data.get("examLimitTime", 0) or 0,
                "scoreSource": 1,
            }
            if question_data.get("examDetailId"):
                payload["examDetailId"] = question_data["examDetailId"]

            submit_response = requests.post(
                Config.EXTERNAL_PLATFORM["API_ENDPOINTS"]["SUBMIT_EXAM"],
                headers=TaskService._build_headers(access_token),
                data=json.dumps(payload, ensure_ascii=False),
            )
            submit_json = submit_response.json()

            if submit_json.get("code") == 200:
                from ccsa_auto.modules.task.score_tracker import ScoreTracker

                ScoreTracker.record_score(
                    user_id=user_id,
                    task_id=None,
                    task_type=task_type,
                    total_questions=len(questions),
                    correct_questions=score_strategy["correct_questions"],
                    score=score_strategy["score"],
                    max_score=score_strategy["max_score"],
                )

                logger.info(
                    f"{label}完成，得分：{score_strategy['score']}/"
                    f"{score_strategy['max_score']}，用户：{user_name}({user_id})"
                )
                return {
                    "success": True,
                    "message": f"{label}执行成功",
                    "result": submit_json.get("data", {}),
                    "score_strategy": score_strategy,
                }

            error_msg = submit_json.get("msg", "未知错误")
            if "您已完成此考试" in error_msg:
                return TaskService._record_completed_exam(
                    user_id, task_type, label, user_name
                )

            logger.error(f"{label}提交失败：{error_msg}，用户：{user_name}({user_id})")
            return {
                "success": False,
                "message": f"提交答案失败：{error_msg}",
                "error_type": "SubmitError",
            }

        except Exception as e:
            error_msg = f"{label}异常：{str(e)}"
            logger.exception(f"{error_msg}，用户：{user_name}({user_id})")
            return {
                "success": False,
                "message": error_msg,
                "error_type": type(e).__name__,
            }

    @staticmethod
    def execute_daily_question(access_token, user_id, user_name="未知"):
        """
        执行每日一题

        Args:
            access_token: 访问令牌
            user_id: 用户ID
            user_name: 用户姓名
        """
        return TaskService._execute_regular_exam(
            access_token, user_id, "daily", user_name
        )

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
            headers = TaskService._build_headers(access_token)

            response = requests.get(url, headers=headers, params=params)
            response_json = response.json()

            if response_json.get("code") != 200:
                error_msg = (
                    f"获取每周一课详情失败：{response_json.get('msg', '未知错误')}"
                )
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg,
                    "error_type": "PlatformApiError",
                }

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
            return {
                "success": False,
                "message": error_msg,
                "error_type": type(e).__name__,
            }

    @staticmethod
    def get_video_url(access_token, lesson_id, vod_id=None, resource_relation_id=None):
        """
        获取视频播放鉴权信息

        新版接口：GET progress-v2/app/regularCourseWeek/courseWeekPlayAuth/{lesson_id}
        返回 ``{vodId, playType, previewTime, results}``，其中 results 为播放凭证。

        Args:
            access_token: 访问令牌
            lesson_id: 每周一课ID（studyAssociationId）
            vod_id: 兼容旧调用保留，可选
            resource_relation_id: 兼容旧调用保留，可选

        Returns:
            dict: 视频鉴权信息
        """
        try:
            url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"]["GET_VIDEO_URL"].format(
                lesson_id=lesson_id
            )
            headers = TaskService._build_headers(access_token)

            response = requests.get(url, headers=headers)
            response_json = response.json()

            if response_json.get("code") != 200:
                error_msg = f"获取视频鉴权失败：{response_json.get('msg', '未知错误')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg,
                    "error_type": "VideoAuthError",
                }

            return {"success": True, "data": response_json.get("data", {})}

        except Exception as e:
            error_msg = f"获取视频鉴权异常：{str(e)}"
            logger.exception(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error_type": type(e).__name__,
            }

    @staticmethod
    def execute_weekly_lesson(access_token, user_id, user_name="未知"):
        """
        执行每周一课

        Args:
            access_token: 访问令牌
            user_id: 用户ID
            user_name: 用户姓名
        """
        # 在try块外定义变量，确保异常处理时可用
        start_time = time.time()
        thread_id = threading.current_thread().ident

        try:
            import random
            import json

            start_datetime = datetime.now().isoformat()
            logger.info(
                f"[每周一课] 开始执行 | user={user_name}({user_id}) | thread_id={thread_id} | start_time={start_datetime}"
            )

            # 新版接口：GET progress-v2/app/regularStudy/getRegularStudyWeek，data 即周课信息
            week_url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"][
                "GET_REGULAR_STUDY_WEEK"
            ]
            study_headers = TaskService._build_headers(access_token)

            # 请求周课信息
            logger.info(
                f"[每周一课] 请求周课信息 | user={user_id} | url={week_url} | thread_id={thread_id}"
            )
            req_start = time.time()
            study_response = requests.get(week_url, headers=study_headers)
            req_end = time.time()
            req_duration = req_end - req_start
            study_response_json = study_response.json()
            logger.info(
                f"[每周一课] 周课信息响应 | user={user_id} | status={study_response.status_code} | duration={req_duration:.3f}s | code={study_response_json.get('code')} | thread_id={thread_id}"
            )
            logger.debug(
                f"[每周一课] 周课信息数据 | user={user_id} | data={study_response_json} | thread_id={thread_id}"
            )

            if study_response_json.get("code") != 200:
                error_msg = f"获取每周一课信息失败：{study_response_json.get('msg', '未知错误')}"
                logger.error(
                    f"[每周一课] {error_msg} | user={user_id} | thread_id={thread_id}"
                )
                return {
                    "success": False,
                    "message": error_msg,
                    "error_type": "PlatformApiError",
                }

            week_info = study_response_json.get("data") or {}
            week_id = week_info.get("id")

            if not week_id:
                error_msg = "未能获取每周一课ID"
                logger.error(
                    f"[每周一课] {error_msg} | user={user_id} | data={week_info} | thread_id={thread_id}"
                )
                return {
                    "success": False,
                    "message": error_msg,
                    "error_type": "EmptyDataError",
                }

            logger.info(
                f"[每周一课] 解析到week_id | user={user_id} | week_id={week_id} | studyStatus={week_info.get('studyStatus')} | thread_id={thread_id}"
            )

            # 获取课程详情
            logger.info(
                f"[每周一课] 请求课程详情 | user={user_id} | week_id={week_id} | thread_id={thread_id}"
            )
            details_start = time.time()
            details_result = TaskService.get_weekly_lesson_details(
                access_token, week_id
            )
            details_end = time.time()
            details_duration = details_end - details_start
            logger.info(
                f"[每周一课] 课程详情响应 | user={user_id} | duration={details_duration:.3f}s | success={details_result.get('success')} | thread_id={thread_id}"
            )

            if not details_result.get("success"):
                logger.error(
                    f"[每周一课] 获取课程详情失败 | user={user_id} | message={details_result.get('message')} | thread_id={thread_id}"
                )
                return details_result

            lesson_details = details_result.get("data", {})
            resource_duration = lesson_details.get("resourceDuration", 300)
            resource_id = lesson_details.get("resourceId")
            resource_url = lesson_details.get("resourceUrl")
            logger.info(
                f"[每周一课] 课程详情 | user={user_id} | resource_duration={resource_duration} | resource_id={resource_id} | resource_url={resource_url} | thread_id={thread_id}"
            )

            if resource_url:
                # 视频播放鉴权（新版：GET courseWeekPlayAuth/{lesson_id}）
                logger.info(
                    f"[每周一课] 请求视频鉴权 | user={user_id} | week_id={week_id} | vod_id={resource_url} | thread_id={thread_id}"
                )
                video_start = time.time()
                video_result = TaskService.get_video_url(access_token, week_id)
                video_end = time.time()
                video_duration = video_end - video_start
                logger.info(
                    f"[每周一课] 视频鉴权响应 | user={user_id} | duration={video_duration:.3f}s | success={video_result.get('success')} | thread_id={thread_id}"
                )

                if not video_result.get("success"):
                    error_msg = f"获取视频鉴权失败：{video_result.get('message')}"
                    logger.error(
                        f"[每周一课] {error_msg} | user={user_id} | thread_id={thread_id}"
                    )
                    return {
                        "success": False,
                        "message": error_msg,
                        "error_type": "VideoAuthError",
                    }

            submit_url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"][
                "SUBMIT_STUDY_SCHEDULE"
            ]
            submit_headers = TaskService._build_headers(access_token)

            payload = {
                "studyProgressTime": resource_duration,
                "studyDuration": resource_duration,
                "studyAssociationId": week_id,
                "studyType": 4,
                "courseResourceRelationId": resource_id,
                "studySchedule": 100,
            }

            logger.info(
                f"[每周一课] 提交学习记录 | user={user_id} | week_id={week_id} | resource_duration={resource_duration} | payload={payload} | thread_id={thread_id}"
            )
            submit_start = time.time()
            submit_response = requests.post(
                submit_url, headers=submit_headers, json=payload
            )
            submit_end = time.time()
            submit_duration = submit_end - submit_start
            submit_json = submit_response.json()
            logger.info(
                f"[每周一课] 提交响应 | user={user_id} | status={submit_response.status_code} | duration={submit_duration:.3f}s | response_code={submit_json.get('code')} | msg={submit_json.get('msg')} | thread_id={thread_id}"
            )
            logger.debug(
                f"[每周一课] 提交响应数据 | user={user_id} | data={submit_json.get('data')} | thread_id={thread_id}"
            )

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

                end_time = time.time()
                total_duration = end_time - start_time
                logger.info(
                    f"[每周一课] 执行成功 | user={user_name}({user_id}) | total_duration={total_duration:.3f}s | thread_id={thread_id} | result={submit_json.get('data', {})}"
                )
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
                end_time = time.time()
                total_duration = end_time - start_time
                logger.error(
                    f"[每周一课] 执行失败 | user={user_name}({user_id}) | total_duration={total_duration:.3f}s | error={error_msg} | thread_id={thread_id} | response={submit_json}"
                )
                return {
                    "success": False,
                    "message": error_msg,
                    "error_type": "SubmitError",
                }

        except Exception as e:
            end_time = time.time()
            total_duration = end_time - start_time
            error_msg = f"每周一课异常：{str(e)}"
            logger.exception(
                f"[每周一课] 执行异常 | user={user_name}({user_id}) | total_duration={total_duration:.3f}s | error={str(e)} | thread_id={thread_id}"
            )
            return {
                "success": False,
                "message": error_msg,
                "error_type": type(e).__name__,
            }

    @staticmethod
    def execute_monthly_exam(access_token, user_id, user_name="未知"):
        """
        执行每月一考

        Args:
            access_token: 访问令牌
            user_id: 用户ID
            user_name: 用户姓名
        """
        return TaskService._execute_regular_exam(
            access_token, user_id, "monthly", user_name
        )

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
                    return {
                        "success": False,
                        "message": "未设置外部平台账号信息",
                        "error_type": "ConfigError",
                    }

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
                        return {
                            "success": False,
                            "message": "外部平台认证失败",
                            "error_type": "AuthError",
                        }
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
                    result = TaskService.execute_monthly_exam(
                        access_token, user.id, user_name
                    )
                else:
                    return {
                        "success": False,
                        "message": "任务类型无效",
                        "error_type": "InvalidTaskType",
                    }

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

                return {
                    "success": False,
                    "message": f"执行任务异常: {str(e)}",
                    "error_type": type(e).__name__,
                }

        # 所有重试都失败
        return {
            "success": False,
            "message": f"任务执行失败，已重试{max_retries}次",
            "error_type": "RetryExhaustedError",
        }

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
