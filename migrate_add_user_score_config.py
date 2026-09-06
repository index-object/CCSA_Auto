"""数据库迁移脚本 - 为 users 表添加每用户控分配置列，并按旧全局配置回填
用法: 在项目根目录下运行 `python migrate_add_user_score_config.py`（幂等，可重复执行）
"""

import sys
import os

sys.path.insert(0, os.path.abspath("."))

from ccsa_auto.core.database import engine
from sqlalchemy import text

# 列 -> (SQLite 列定义, 默认值常量, 对应旧 system_configs 键)
COLUMNS = [
    ("score_strategy_enabled", "BOOLEAN DEFAULT 1", True, "score_strategy_enabled"),
    ("score_target", "INTEGER DEFAULT 650", 650, "score_target"),
    ("score_threshold", "INTEGER DEFAULT 20", 20, "score_threshold"),
    ("score_random_min", "FLOAT DEFAULT 0.30", 0.30, "score_random_min"),
    ("score_random_max", "FLOAT DEFAULT 1.00", 1.00, "score_random_max"),
    ("daily_deduction_enabled", "BOOLEAN DEFAULT 1", True, "daily_deduction_enabled"),
    ("daily_deduction_min", "INTEGER DEFAULT 1", 1, "daily_deduction_min"),
    ("daily_deduction_max", "INTEGER DEFAULT 2", 2, "daily_deduction_max"),
]


def _coerce(raw, default):
    s = str(raw)
    if isinstance(default, bool):
        return s.lower() in ("true", "1", "yes")
    if isinstance(default, int):
        try:
            return int(float(s))
        except ValueError:
            return default
    try:
        return float(s)
    except ValueError:
        return default


def migrate():
    print("开始迁移：为 users 表添加控分配置列...")
    with engine.connect() as conn:
        existing = [row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()]
        for col, col_def, default, _key in COLUMNS:
            if col in existing:
                print(f"  ✓ 列 {col} 已存在")
                continue
            conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_def}"))
            print(f"  ✓ 已添加列: {col}")

        # 按旧全局配置回填（有旧值则覆盖默认，否则保持默认）
        for col, col_def, default, key in COLUMNS:
            row = conn.execute(
                text("SELECT config_value FROM system_configs WHERE config_key = :k"),
                {"k": key},
            ).fetchone()
            if not row:
                continue
            value = _coerce(row[0], default)
            conn.execute(text(f"UPDATE users SET {col} = :v WHERE {col} IS NULL"), {"v": value})
            print(f"  ✓ 已按旧全局配置回填: {col}={value}")

        conn.commit()
    print("迁移完成!")


if __name__ == "__main__":
    migrate()
