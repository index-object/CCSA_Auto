# -*- coding: utf-8 -*-
"""控分策略验证脚本（per-user 配置）"""

import sys
import io
import logging
from datetime import datetime, timedelta
from ccsa_auto.modules.task import score_strategy
from ccsa_auto.modules.task import score_tracker
from ccsa_auto.utils.timezone import SHANGHAI_TZ

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
logging.basicConfig(level=logging.WARNING)

# ---- per-user config stubs ----
_USER_SCORE_CONFIGS = {
    1: {
        "score_strategy_enabled": True,
        "score_target": 680,
        "score_threshold": 10,
        "score_random_min": 0.30,
        "score_random_max": 1.00,
        "daily_deduction_enabled": True,
        "daily_deduction_min": 0,
        "daily_deduction_max": 1,
    },
    2: {
        "score_strategy_enabled": True,
        "score_target": 680,
        "score_threshold": 10,
        "score_random_min": 0.30,
        "score_random_max": 1.00,
        "daily_deduction_enabled": True,
        "daily_deduction_min": 0,
        "daily_deduction_max": 1,
    },
    3: {
        "score_strategy_enabled": True,
        "score_target": 680,
        "score_threshold": 10,
        "score_random_min": 0.30,
        "score_random_max": 1.00,
        "daily_deduction_enabled": True,
        "daily_deduction_min": 0,
        "daily_deduction_max": 1,
    },
}


def mock_get_user_score_config(user_id):
    return _USER_SCORE_CONFIGS.get(user_id, _USER_SCORE_CONFIGS[1].copy())


# ---- per-month mock (replaces DB calls) ----
_SCORE_CACHE = {}


def mock_calculate_monthly_total(user_id, year, month):
    return _SCORE_CACHE.get(
        user_id,
        {"total": 0, "daily": 0, "weekly": 0, "monthly": 0},
    )


def set_current_scores(user_id, scores):
    _SCORE_CACHE[user_id] = {k: v for k, v in scores.items() if k in ("total", "daily", "weekly", "monthly")}


def test_monthly_score_plan(user_id: int, year: int, month: int):
    first_day = datetime(year, month, 1, tzinfo=SHANGHAI_TZ)
    if month == 12:
        next_month = datetime(year + 1, 1, 1, tzinfo=SHANGHAI_TZ)
    else:
        next_month = datetime(year + 1, month + 1, 1, tzinfo=SHANGHAI_TZ)

    current = first_day
    total_daily_score = 0
    daily_count = 0
    results = []

    while current < next_month and current.month == month:
        score_strategy.get_current_time = lambda d=current: d
        is_workday = not score_strategy.ScoreStrategy.is_weekend_or_holiday(current)

        daily_result = {
            "date": current.strftime("%m-%d %a"),
            "is_workday": is_workday,
            "score": "-",
            "correct": "-",
            "running_total": 0,
        }

        if is_workday:
            result = score_strategy.ScoreStrategy.calculate_strategy(
                user_id, "daily", 10, 2.0
            )
            daily_result["score"] = f"{result['score']:.0f}"
            daily_result["correct"] = str(result["correct_questions"])
            daily_result["running_total"] = total_daily_score + result["score"]
            total_daily_score += result["score"]
            daily_count += 1

            set_current_scores(
                user_id,
                {
                    "total": total_daily_score,
                    "daily": total_daily_score,
                    "weekly": 0,
                    "monthly": 0,
                },
            )

        results.append(daily_result)
        current += timedelta(days=1)

    print(f"\n{'Date':<10} {'Work':<8} {'Score':<10} {'Correct':<6} {'Total':<10}")
    print("-" * 50)
    for r in results:
        status = "Y" if r["is_workday"] else "N"
        print(
            f"{r['date']:<10} {status:<8} {r['score']:<10} {r['correct']:<6} {r['running_total']:.0f}"
        )

    print("-" * 50)
    print(f"Work days: {daily_count}, Daily total: {total_daily_score:.0f}")


def test_monthly_exam(user_id: int, year: int, month: int, current_total_before: float):
    set_current_scores(
        user_id,
        {
            "total": current_total_before,
            "daily": current_total_before * 0.5,
            "weekly": current_total_before * 0.5,
            "monthly": 0,
        },
    )

    exam_date = datetime(year, month, 15, tzinfo=SHANGHAI_TZ)
    score_strategy.get_current_time = lambda: exam_date

    result = score_strategy.ScoreStrategy.calculate_strategy(
        user_id, "monthly", 50, 2.0
    )

    print(
        f"\nMonthly Exam (Day15): {result['score']:.0f} ({result['correct_questions']} correct)"
    )
    print(f"After exam total: {current_total_before + result['score']:.0f}")


def test_scenario(
    name: str, user_id: int, year: int, month: int, initial_score: float = 0
):
    print(f"\n{'=' * 60}")
    print(f"Scenario: {name}")
    print(f"{'=' * 60}")
    cfg = mock_get_user_score_config(user_id)
    print(f"Target: {cfg['score_target']}")
    print(f"Threshold: {cfg['score_threshold']}")

    _SCORE_CACHE.clear()

    test_monthly_score_plan(user_id, year, month)
    test_monthly_exam(user_id, year, month, initial_score)


if __name__ == "__main__":
    score_strategy.get_user_score_config = mock_get_user_score_config
    score_tracker.ScoreTracker.calculate_monthly_total = mock_calculate_monthly_total

    print("\n" + "=" * 60)
    print("Score Strategy Test - Per-User Config")
    print("=" * 60)

    test_scenario("Normal Progress (User1)", user_id=1, year=2026, month=2)

    print("\n")
    test_scenario(
        "Behind (200 at exam, User2)", user_id=2, year=2026, month=2, initial_score=200
    )

    print("\n")
    test_scenario(
        "Ahead (400 at exam, User3)", user_id=3, year=2026, month=2, initial_score=400
    )
