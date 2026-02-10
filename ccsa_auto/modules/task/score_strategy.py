"""分数控制策略模块"""

import logging
import random
from datetime import datetime
from typing import Dict, Tuple, Optional, Any

from ccsa_auto.modules.task.score_tracker import ScoreTracker
from ccsa_auto.utils.timezone import get_current_time, SHANGHAI_TZ

logger = logging.getLogger(__name__)


class ScoreStrategy:
    """分数控制策略服务"""

    TARGET_MONTHLY_SCORE = 650
    MIN_SCORE_RATIO = 0.45
    MAX_SCORE_RATIO = 0.90
    USER_VARIATION_STD = 0.08
    DAILY_ALLOCATE_RATIO = 0.80
    MONTHLY_ALLOCATE_RATIO = 0.25
    MONTHLY_BASE_SCORE = 90

    @staticmethod
    def is_weekend_or_holiday(date: datetime) -> bool:
        """
        判断是否为周末或法定节假日

        Args:
            date: 日期时间（上海时区）

        Returns:
            bool: True表示周末或节假日
        """
        try:
            import chinese_calendar as calendar

            return calendar.is_holiday(date)
        except Exception:
            return date.weekday() >= 5

    @staticmethod
    def get_saturdays_in_month(year: int, month: int) -> list[datetime]:
        """
        获取指定月份中属于当月的周六列表

        Args:
            year: 年份
            month: 月份

        Returns:
            list[datetime]: 当月周六列表
        """
        if month == 12:
            next_month_year = year + 1
            next_month = 1
        else:
            next_month_year = year
            next_month = month + 1

        from datetime import timedelta

        first_day = datetime(year, month, 1).replace(tzinfo=SHANGHAI_TZ)
        last_day = datetime(next_month_year, next_month, 1).replace(
            tzinfo=SHANGHAI_TZ
        ) - timedelta(seconds=1)

        saturdays = []
        current = first_day
        while current <= last_day:
            if current.weekday() == 5:
                saturday = current.replace(hour=0, minute=0, second=0)
                saturdays.append(saturday)
            current += timedelta(days=1)

        if not saturdays:
            return []

        first_saturday = saturdays[0]
        if first_saturday.day <= 3 and first_saturday.weekday() == 5:
            is_first_belong_to_prev_month = (
                first_saturday.day == 1 or first_saturday.weekday() == 5
            )
            if is_first_belong_to_prev_month:
                saturdays = saturdays[1:]

        if len(saturdays) >= 2:
            last_saturday = saturdays[-1]
            next_day = last_saturday + timedelta(days=1)
            if next_day.month != month:
                saturdays = saturdays[:-1]

        return saturdays

    @staticmethod
    def get_working_days_in_month(year: int, month: int) -> int:
        """
        获取指定月份的工作日数量（周一到周五，排除节假日）

        Args:
            year: 年份
            month: 月份

        Returns:
            int: 工作日数量
        """
        if month == 12:
            next_month_year = year + 1
            next_month = 1
        else:
            next_month_year = year
            next_month = month + 1

        from datetime import timedelta

        first_day = datetime(year, month, 1).replace(tzinfo=SHANGHAI_TZ)
        last_day = datetime(next_month_year, next_month, 1).replace(
            tzinfo=SHANGHAI_TZ
        ) - timedelta(seconds=1)

        working_days = 0
        current = first_day
        while current <= last_day:
            if not ScoreStrategy.is_weekend_or_holiday(current):
                working_days += 1
            current += timedelta(days=1)

        return working_days

    @staticmethod
    def get_remaining_working_days_in_month(
        year: int, month: int, current_date: datetime
    ) -> int:
        """
        获取指定月份剩余的工作日数量（包括当前日期）

        Args:
            year: 年份
            month: 月份
            current_date: 当前日期（上海时区）

        Returns:
            int: 剩余工作日数量
        """
        if month == 12:
            next_month_year = year + 1
            next_month = 1
        else:
            next_month_year = year
            next_month = month + 1

        from datetime import timedelta

        first_day = datetime(year, month, 1).replace(tzinfo=SHANGHAI_TZ)
        last_day = datetime(next_month_year, next_month, 1).replace(
            tzinfo=SHANGHAI_TZ
        ) - timedelta(seconds=1)

        remaining_days = 0
        current = max(first_day, current_date.replace(hour=0, minute=0, second=0))
        while current <= last_day:
            if not ScoreStrategy.is_weekend_or_holiday(current):
                remaining_days += 1
            current += timedelta(days=1)

        return remaining_days

    @staticmethod
    def get_weekly_lessons_info(user_id: int, year: int, month: int) -> Dict[str, Any]:
        """
        获取本月每周一课信息

        Args:
            user_id: 用户ID
            year: 年份
            month: 月份

        Returns:
            Dict: {
                "total_sessions": 本月每周一课总次数,
                "full_score": 本月每周一课满分,
                "actual_score": 本月已完成得分,
                "remaining_sessions": 剩余次数,
                "remaining_score": 剩余可得分,
                "sessions_completed": 已完成次数
            }
        """
        saturdays = ScoreStrategy.get_saturdays_in_month(year, month)
        total_sessions = len(saturdays)
        full_score = total_sessions * 50

        actual_score = ScoreTracker.get_monthly_weekly_score(user_id, year, month)
        sessions_completed = actual_score // 50
        remaining_sessions = max(0, total_sessions - sessions_completed)
        remaining_score = remaining_sessions * 50

        return {
            "total_sessions": total_sessions,
            "full_score": full_score,
            "actual_score": actual_score,
            "remaining_sessions": remaining_sessions,
            "remaining_score": remaining_score,
            "sessions_completed": sessions_completed,
        }

    @staticmethod
    def apply_user_variation(user_id: int, date: datetime, base_ratio: float) -> float:
        """
        应用用户差异化随机波动

        Args:
            user_id: 用户ID
            date: 日期
            base_ratio: 基础得分率

        Returns:
            float: 差异化后的得分率
        """
        seed = user_id * 10000 + date.toordinal()
        random.seed(seed)

        variation = random.normalvariate(0, ScoreStrategy.USER_VARIATION_STD)
        ratio = base_ratio + variation

        ratio = max(ScoreStrategy.MIN_SCORE_RATIO, ratio)
        ratio = min(ScoreStrategy.MAX_SCORE_RATIO, ratio)

        return ratio

    @staticmethod
    def calculate_strategy(
        user_id: int, task_type: str, total_questions: int, score_per_question: float
    ) -> Dict[str, Any]:
        """
        计算控分策略（动态版本）
        - 保证月度目标 >= 570分
        - 同时尽量逼近570分，避免过高
        - 每周一课只能是50或0，无法控分

        Args:
            user_id: 用户ID
            task_type: 任务类型 (daily, weekly, monthly)
            total_questions: 总题数
            score_per_question: 每题分数

        Returns:
            Dict: {
                "correct_questions": 需要答对的题数,
                "score": 预期得分,
                "max_score": 满分,
                "score_ratio": 得分比例,
                "reason": 策略说明
            }
        """
        now = get_current_time()
        year, month = now.year, now.month

        max_score = total_questions * score_per_question

        if task_type == "weekly":
            logger.info(f"[控分策略] 用户{user_id} 每周一课: 必须满分{max_score}分")
            return {
                "correct_questions": total_questions,
                "score": max_score,
                "max_score": max_score,
                "score_ratio": 1.0,
                "reason": "每周一课无法控分，必须满分",
            }

        current_scores = ScoreTracker.get_current_month_scores(user_id)
        current_total = current_scores["total"]

        logger.info(f"[控分策略] 用户{user_id} 当前月度总分: {current_total}分")

        weekly_info = ScoreStrategy.get_weekly_lessons_info(user_id, year, month)
        weekly_actual = weekly_info["actual_score"]
        weekly_remaining = weekly_info["remaining_sessions"]
        weekly_remaining_score = weekly_remaining * 50

        remaining_days = ScoreStrategy.get_remaining_working_days_in_month(
            year, month, now
        )

        daily_available = remaining_days * 20
        monthly_min = ScoreStrategy.MONTHLY_BASE_SCORE

        target = ScoreStrategy.TARGET_MONTHLY_SCORE
        remaining_needed = max(0, target - current_total)

        logger.info(
            f"[控分策略] 用户{user_id} 剩余需达: {remaining_needed:.0f}分, 剩余工作日: {remaining_days}天, 剩余每周一课: {weekly_remaining}次({weekly_remaining_score}分)"
        )

        if task_type == "daily":
            if ScoreStrategy.is_weekend_or_holiday(now):
                logger.info(f"[控分策略] 用户{user_id} 周末/节假日不得分")
                return {
                    "correct_questions": total_questions,
                    "score": 0,
                    "max_score": max_score,
                    "score_ratio": 1.0,
                    "reason": "周末或节假日每日一题不得分",
                }

            if remaining_days <= 0:
                logger.info(f"[控分策略] 用户{user_id} 本月无剩余工作日")
                return {
                    "correct_questions": 1,
                    "score": score_per_question,
                    "max_score": max_score,
                    "score_ratio": 1.0 / total_questions,
                    "reason": "本月无剩余工作日",
                }

            if remaining_needed <= 0:
                base_ratio = ScoreStrategy.MIN_SCORE_RATIO
                reason = "已达标，得最低分"
                logger.info(
                    f"[控分策略] 用户{user_id} 已达标({current_total}分), 得最低分{base_ratio * 100:.1f}%"
                )
            else:
                weekly_monthly_reserve = weekly_remaining_score + monthly_min
                daily_target = max(0, remaining_needed - weekly_monthly_reserve)

                if daily_target <= daily_available * ScoreStrategy.MIN_SCORE_RATIO:
                    base_ratio = ScoreStrategy.MIN_SCORE_RATIO
                    reason = f"剩余需达{remaining_needed:.0f}分, 控最低分"
                    logger.info(
                        f"[控分策略] 用户{user_id} 只需控最低分, 得分率{base_ratio * 100:.1f}%"
                    )
                elif daily_target >= daily_available * ScoreStrategy.MAX_SCORE_RATIO:
                    base_ratio = ScoreStrategy.MAX_SCORE_RATIO
                    reason = f"剩余需达{remaining_needed:.0f}分, 需拿高分"
                    logger.info(
                        f"[控分策略] 用户{user_id} 需拿高分, 得分率{base_ratio * 100:.1f}%"
                    )
                else:
                    base_ratio = daily_target / daily_available
                    reason = f"剩余需达{remaining_needed:.0f}分, 日均目标{daily_target / remaining_days:.1f}分"
                    logger.info(
                        f"[控分策略] 用户{user_id} 日均目标{daily_target / remaining_days:.1f}分, 得分率{base_ratio * 100:.1f}%"
                    )

            ratio = ScoreStrategy.apply_user_variation(user_id, now, base_ratio)
            correct_count = max(1, min(total_questions, int(total_questions * ratio)))
            actual_score = correct_count * score_per_question

            logger.info(
                f"[控分策略] 用户{user_id} 每日一题: 得分{actual_score:.0f}分({correct_count}题), 得分率{ratio * 100:.1f}%"
            )

            return {
                "correct_questions": correct_count,
                "score": actual_score,
                "max_score": max_score,
                "score_ratio": actual_score / max_score if max_score > 0 else 0.0,
                "reason": f"{reason}, 得分率{ratio * 100:.1f}%",
            }

        elif task_type == "monthly":
            weekly_monthly_reserve = weekly_remaining_score
            monthly_target = max(
                0,
                remaining_needed
                - weekly_monthly_reserve
                - daily_available * ScoreStrategy.MIN_SCORE_RATIO,
            )

            if monthly_target <= ScoreStrategy.MONTHLY_BASE_SCORE:
                monthly_target = ScoreStrategy.MONTHLY_BASE_SCORE
                base_ratio = monthly_target / 100
                reason = "已达标或接近达标，得保底分"
                logger.info(
                    f"[控分策略] 用户{user_id} 每月一考得保底{monthly_target}分"
                )
            else:
                monthly_target = min(100, monthly_target)
                base_ratio = monthly_target / 100
                reason = f"剩余需达{remaining_needed:.0f}分, 承担{monthly_target:.0f}分"
                logger.info(
                    f"[控分策略] 用户{user_id} 每月一考分配{monthly_target:.0f}分, 得分率{base_ratio * 100:.1f}%"
                )

            ratio = ScoreStrategy.apply_user_variation(user_id, now, base_ratio)
            correct_count = max(1, min(total_questions, int(total_questions * ratio)))
            actual_score = correct_count * score_per_question

            logger.info(
                f"[控分策略] 用户{user_id} 每月一考: 得分{actual_score:.0f}分({correct_count}题), 得分率{ratio * 100:.1f}%"
            )

            return {
                "correct_questions": correct_count,
                "score": actual_score,
                "max_score": max_score,
                "score_ratio": actual_score / max_score if max_score > 0 else 0.0,
                "reason": f"{reason}, 得分率{ratio * 100:.1f}%",
            }

        return {
            "correct_questions": total_questions,
            "score": max_score,
            "max_score": max_score,
            "score_ratio": 1.0,
            "reason": "未知任务类型",
        }

    @staticmethod
    def get_wrong_answer_for_single_choice(correct_answer: str) -> str:
        """
        为单选题生成错误答案（相邻互换）

        Args:
            correct_answer: 正确答案（如 A, B, C, D）

        Returns:
            str: 错误答案
        """
        option_map = {
            "A": "B",
            "B": "A",
            "C": "D",
            "D": "C",
            "E": "D",
            "F": "E",
        }

        correct_option = correct_answer.strip('"')
        wrong_option = option_map.get(correct_option, "B")
        return f'"{wrong_option}"'

    @staticmethod
    def get_wrong_answer_for_multiple_choice(correct_answer: str) -> str:
        """
        为多选题生成错误答案（替换其中一个选项）

        Args:
            correct_answer: 正确答案（如 "A,B,C"）

        Returns:
            str: 错误答案
        """
        correct_options_str = correct_answer.strip('"')
        correct_options = [opt.strip() for opt in correct_options_str.split(",")]

        if len(correct_options) <= 1:
            return correct_answer

        option_pool = ["A", "B", "C", "D", "E"]
        wrong_options = correct_options.copy()

        random.shuffle(option_pool)

        for opt in option_pool:
            if opt not in correct_options:
                if len(wrong_options) > 1:
                    wrong_options[-1] = opt
                else:
                    wrong_options.append(opt)
                break

        wrong_options.sort()
        return f'"{",".join(wrong_options)}"'

    @staticmethod
    def select_incorrect_questions_by_type(
        questions: list[Dict[str, Any]],
        incorrect_count: int,
        prefer_single: bool = True,
    ) -> list[int]:
        """
        选择需要答错的题号（优先选择单选题）

        Args:
            questions: 题目列表
            incorrect_count: 需要答错的题数
            prefer_single: 是否优先选择单选题

        Returns:
            list[int]: 需要答错的题号列表
        """
        if incorrect_count <= 0:
            return []

        single_indices = []
        multiple_indices = []

        for idx, question in enumerate(questions):
            question_type = question.get("questionType", 1)
            if question_type == 1:
                single_indices.append(idx)
            elif question_type == 2:
                multiple_indices.append(idx)

        selected_indices = []

        if prefer_single:
            selected_indices = random.sample(
                single_indices, min(incorrect_count, len(single_indices))
            )
            remaining = incorrect_count - len(selected_indices)
            if remaining > 0:
                selected_indices.extend(
                    random.sample(
                        multiple_indices, min(remaining, len(multiple_indices))
                    )
                )
        else:
            all_indices = list(range(len(questions)))
            selected_indices = random.sample(
                all_indices, min(incorrect_count, len(all_indices))
            )
        selected_indices.sort()
        return selected_indices

    @staticmethod
    def modify_answers_for_score_control(
        questions: list[Dict[str, Any]], task_type: str, user_id: int
    ) -> Tuple[list[Dict[str, Any]], Dict[str, Any]]:
        """
        根据控分策略修改答案

        Args:
            questions: 原始题目列表
            task_type: 任务类型
            user_id: 用户ID

        Returns:
            Tuple: (修改后的题目列表, 策略信息)
        """
        total_questions = len(questions)
        if total_questions == 0:
            return questions, {
                "correct_questions": 0,
                "score": 0,
                "max_score": 0,
                "score_ratio": 0.0,
                "reason": "没有题目",
            }

        score_per_question = 2.0

        strategy = ScoreStrategy.calculate_strategy(
            user_id, task_type, total_questions, score_per_question
        )

        if task_type == "daily" and "weekend" in strategy.get("reason", ""):
            return questions, strategy

        correct_count = strategy["correct_questions"]
        incorrect_count = total_questions - correct_count

        if incorrect_count > 0:
            incorrect_indices = ScoreStrategy.select_incorrect_questions_by_type(
                questions, incorrect_count, prefer_single=True
            )

            for idx in incorrect_indices:
                question = questions[idx]
                original_answer = question.get("questionAnswer", "")
                question_type = question.get("questionType", 1)

                if original_answer:
                    if question_type == 1:
                        wrong_answer = ScoreStrategy.get_wrong_answer_for_single_choice(
                            original_answer
                        )
                        questions[idx]["questionAnswer"] = wrong_answer
                    elif question_type == 2:
                        wrong_answer = (
                            ScoreStrategy.get_wrong_answer_for_multiple_choice(
                                original_answer
                            )
                        )
                        questions[idx]["questionAnswer"] = wrong_answer

        return questions, strategy
