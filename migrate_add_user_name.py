"""
数据库迁移脚本 - 为 users 表添加 name 字段
用法: 在项目根目录下运行 `python migrate_add_user_name.py`
"""

import sys
import os

sys.path.insert(0, os.path.abspath("."))

from ccsa_auto.core.database import engine
from sqlalchemy import text


def migrate():
    print("开始迁移：为 users 表添加 name 列（如果不存在）...")

    with engine.connect() as conn:
        # 获取现有列信息（SQLite 使用 PRAGMA table_info）
        try:
            result = conn.execute(text("PRAGMA table_info(users)"))
            existing_columns = [row[1] for row in result.fetchall()]
        except Exception as e:
            print(f"无法读取 users 表信息: {e}")
            return

        print(f"users 表已有列: {existing_columns}")

        if "name" in existing_columns:
            print("✓ 列 'name' 已存在，跳过添加。")
        else:
            try:
                # SQLite 支持简单的 ALTER TABLE ADD COLUMN
                conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR(100)"))
                conn.commit()
                print("✓ 已添加列: name")
            except Exception as e:
                print(f"✗ 添加列 name 失败: {e}")

    print("迁移完成。请根据需要备份数据库并验证数据。")


if __name__ == "__main__":
    migrate()
