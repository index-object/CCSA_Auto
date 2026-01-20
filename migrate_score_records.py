"""创建得分记录表"""

import sys
import os

sys.path.insert(0, os.path.abspath("."))

from ccsa_auto.core.database import engine, Base
from ccsa_auto.modules.task.score_tracker import ScoreRecord


def create_score_records_table():
    """创建得分记录表"""
    try:
        ScoreRecord.__table__.create(engine, checkfirst=True)
        print("得分记录表创建成功")
    except Exception as e:
        print(f"创建得分记录表失败: {e}")


if __name__ == "__main__":
    create_score_records_table()
