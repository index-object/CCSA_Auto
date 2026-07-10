"""
数据库迁移脚本 - 为 auth_sessions 表添加用户状态字段
运行此脚本将添加必要的列来存储用户状态数据
"""

import sys
import os

sys.path.insert(0, os.path.abspath("."))

from ccsa_auto.core.database import engine
from sqlalchemy import text


def migrate():
    """执行数据库迁移"""
    print("开始数据库迁移...")

    # 检查并添加新列
    new_columns = [
        ("is_authenticated", "BOOLEAN DEFAULT 0"),
        ("is_admin", "BOOLEAN DEFAULT 0"),
        ("user_info_json", "TEXT"),
        ("access_token", "VARCHAR(500)"),
        ("external_token", "TEXT"),
        ("referrer_path", "VARCHAR(500)"),
    ]

    with engine.connect() as conn:
        # 获取现有列
        result = conn.execute(text("PRAGMA table_info(auth_sessions)"))
        existing_columns = [row[1] for row in result.fetchall()]
        print(f"现有列: {existing_columns}")

        for col_name, col_def in new_columns:
            if col_name not in existing_columns:
                try:
                    conn.execute(
                        text(
                            f"ALTER TABLE auth_sessions ADD COLUMN {col_name} {col_def}"
                        )
                    )
                    print(f"✓ 已添加列: {col_name}")
                except Exception as e:
                    print(f"✗ 添加列 {col_name} 失败: {e}")
            else:
                print(f"✓ 列 {col_name} 已存在")

        conn.commit()

    print("数据库迁移完成!")


if __name__ == "__main__":
    migrate()
