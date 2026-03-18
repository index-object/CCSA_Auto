"""分数控制策略模块"""

import logging
import random
from datetime import datetime
from typing import Dict, Tuple, Optional, Any

from ccsa_auto.core.system_config import SystemConfigService
from ccsa_auto.modules.task.score_tracker import ScoreTracker
from ccsa_auto.utils.timezone import get_current_time, SHANGHAI_TZ

logger = logging.getLogger(__name__)


class ScoreStrategy:
    """分数控制策略服务"""

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
    def calculate_strategy(
        user_id: int, task_type: str, total_questions: int, score_per_question: float
    ) -> Dict[str, Any]:
        """
        计算控分策略（简化版本）
        - 未接近目标分数：满分
        - 接近或超过目标分数：随机分数

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
        max_score = total_questions * score_per_question

        if task_type == "weekly":
            logger.info(f"[控分策略] 用户{user_id} 每周一课: 满分{max_score}分")
            return {
                "correct_questions": total_questions,
                "score": max_score,
                "max_score": max_score,
                "score_ratio": 1.0,
                "reason": "每周一课满分",
            }

        now = get_current_time()

        if task_type == "daily" and ScoreStrategy.is_weekend_or_holiday(now):
            logger.info(f"[控分策略] 用户{user_id} 周末/节假日不得分")
            return {
                "correct_questions": total_questions,
                "score": 0,
                "max_score": max_score,
                "score_ratio": 0.0,
                "reason": "周末或节假日每日一题不得分",
            }

        year, month = now.year, now.month
        current_scores = ScoreTracker.calculate_monthly_total(user_id, year, month)
        current_total = current_scores["total"]

        target = SystemConfigService.get_score_target()
        threshold = SystemConfigService.get_score_threshold()
        random_min, random_max = SystemConfigService.get_score_random_range()

        if current_total < target - threshold:
            correct_count = total_questions
            actual_score = max_score
            ratio = 1.0
            reason = f"当前{current_total:.0f}分 < 目标{target}分-{threshold}分，满分"
            logger.info(f"[控分策略] 用户{user_id} {reason}")
        else:
            random_ratio = random.uniform(random_min, random_max)
            correct_count = max(1, int(total_questions * random_ratio))
            actual_score = correct_count * score_per_question
            ratio = actual_score / max_score if max_score > 0 else 0.0
            reason = f"当前{current_total:.0f}分 >= 目标{target}分-{threshold}分，随机{ratio*100:.0f}%"
            logger.info(f"[控分策略] 用户{user_id} {reason}")

        return {
            "correct_questions": correct_count,
            "score": actual_score,
            "max_score": max_score,
            "score_ratio": ratio,
            "reason": reason,
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
