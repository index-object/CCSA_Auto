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

    MIN_SCORE_RATIO = 0.5
    TARGET_MONTHLY_SCORE = 530

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
    def get_working_days_in_month(year: int, month: int) -> int:
        """
        获取指定月份的工作日数量（周一到周五）

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
    def get_weeks_in_month(year: int, month: int) -> int:
        """
        获取指定月份的周数（按周一为一周开始）

        Args:
            year: 年份
            month: 月份

        Returns:
            int: 周数
        """
        from calendar import monthcalendar

        weeks = monthcalendar(year, month)
        return len([w for w in weeks if any(w)])

    @staticmethod
    def calculate_max_potential_score(year: int, month: int) -> Dict[str, int]:
        """
        计算指定月份的理论最大得分

        Args:
            year: 年份
            month: 月份

        Returns:
            Dict: {"total": 总分, "daily": 每日一题, "weekly": 每周一课, "monthly": 每月一考}
        """
        working_days = ScoreStrategy.get_working_days_in_month(year, month)
        weeks = ScoreStrategy.get_weeks_in_month(year, month)

        daily_max = working_days * 20  # 每工作日20分
        weekly_max = weeks * 50  # 每周50分
        monthly_max = 100  # 每月100分

        return {
            "total": daily_max + weekly_max + monthly_max,
            "daily": daily_max,
            "weekly": weekly_max,
            "monthly": monthly_max,
        }

    @staticmethod
    def calculate_strategy(
        user_id: int, task_type: str, total_questions: int, score_per_question: float
    ) -> Dict[str, Any]:
        """
        计算控分策略

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
        score_ratio = 1.0

        if task_type == "weekly":
            return {
                "correct_questions": total_questions,
                "score": max_score,
                "max_score": max_score,
                "score_ratio": 1.0,
                "reason": "每周一课无法控分，必须满分",
            }

        current_scores = ScoreTracker.get_current_month_scores(user_id)
        current_total = current_scores["total"]

        max_potential = ScoreStrategy.calculate_max_potential_score(year, month)
        remaining_potential = ScoreStrategy.calculate_remaining_potential(
            user_id, year, month, now
        )

        if task_type == "daily":
            if ScoreStrategy.is_weekend_or_holiday(now):
                return {
                    "correct_questions": total_questions,
                    "score": 0,
                    "max_score": max_score,
                    "score_ratio": 1.0,
                    "reason": "周末或节假日每日一题不得分",
                }

            if current_total >= ScoreStrategy.TARGET_MONTHLY_SCORE:
                score_ratio = ScoreStrategy.MIN_SCORE_RATIO
            else:
                needed = ScoreStrategy.TARGET_MONTHLY_SCORE - current_total
                if remaining_potential["total"] <= 0:
                    score_ratio = 1.0
                else:
                    score_ratio = min(1.0, needed / remaining_potential["total"])

        elif task_type == "monthly":
            if current_total >= ScoreStrategy.TARGET_MONTHLY_SCORE:
                score_ratio = ScoreStrategy.MIN_SCORE_RATIO
            else:
                needed = ScoreStrategy.TARGET_MONTHLY_SCORE - current_total
                if remaining_potential["total"] <= 0:
                    score_ratio = 1.0
                else:
                    score_ratio = min(1.0, needed / remaining_potential["total"])

        score_ratio = max(ScoreStrategy.MIN_SCORE_RATIO, min(1.0, score_ratio))

        correct_questions = int(total_questions * score_ratio)
        correct_questions = max(
            int(total_questions * ScoreStrategy.MIN_SCORE_RATIO), correct_questions
        )
        correct_questions = min(total_questions, correct_questions)

        actual_score = correct_questions * score_per_question

        return {
            "correct_questions": correct_questions,
            "score": actual_score,
            "max_score": max_score,
            "score_ratio": actual_score / max_score if max_score > 0 else 0.0,
            "reason": f"当前得分: {current_total}, 目标: {ScoreStrategy.TARGET_MONTHLY_SCORE}, 需要答对: {correct_questions}/{total_questions} 题",
        }

    @staticmethod
    def calculate_remaining_potential(
        user_id: int, year: int, month: int, current_date: datetime
    ) -> Dict[str, int]:
        """
        计算剩余可能获得的最大得分

        Args:
            user_id: 用户ID
            year: 年份
            month: 月份
            current_date: 当前日期（上海时区）

        Returns:
            Dict: {"total": 总分, "daily": 每日一题, "weekly": 每周一课, "monthly": 每月一考}
        """
        remaining_working_days = ScoreStrategy.get_remaining_working_days_in_month(
            year, month, current_date
        )

        from datetime import timedelta

        remaining_weeks = 0
        last_day = current_date.replace(day=1)
        if month == 12:
            next_month_year = year + 1
            next_month = 1
        else:
            next_month_year = year
            next_month = month + 1

        last_day = datetime(next_month_year, next_month, 1).replace(
            tzinfo=SHANGHAI_TZ
        ) - timedelta(seconds=1)

        temp = current_date.replace(hour=0, minute=0, second=0)
        while temp <= last_day:
            if temp.weekday() == 0:
                remaining_weeks += 1
                temp += timedelta(days=7)
            else:
                temp += timedelta(days=1)

        remaining_monthly = 1

        return {
            "total": remaining_working_days * 20
            + remaining_weeks * 50
            + remaining_monthly * 100,
            "daily": remaining_working_days * 20,
            "weekly": remaining_weeks * 50,
            "monthly": remaining_monthly * 100,
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
