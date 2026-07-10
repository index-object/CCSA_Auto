# 完全动态控分策略设计方案

> 生成日期：2026-01-31
> 版本：v2.0

---

## 1. 概述

### 1.1 背景
原控分策略存在以下问题：
- 每月一题每次都拿满分，导致月底远超预期目标530分
- 每周一课缺失时没有补救措施
- 所有用户同一天分数相同，缺乏差异化
- 未考虑剩余天数，导致极端场景失控

### 1.2 目标
- 保证月底总分略高于530分（535-560范围）
- 每周一课缺失时，通过每日一题和每月一考进行补救
- 用户差异化：同一天不同用户分数不同
- 完全动态计算：每次执行任务都重新计算目标
- 极端场景处理：剩余天数不足时无法达标，但不会得0分

---

## 2. 分数来源与目标分解

### 2.1 每月任务分值

| 任务类型 | 单次分值 | 月度理论满分 | 执行时间 | 控分策略 |
|---------|---------|-------------|---------|---------|
| 每日一题 | 20分/工作日 | 约400-440分 | 每日工作日 | **完全动态** |
| 每周一课 | 50分/周 | 200-250分 | 每周六 | **必须满分/0分** |
| 每月一考 | 100分/月 | 100分 | 每月15号 | **完全动态** |

### 2.2 目标分解（530分）

| 任务类型 | 目标分数 | 说明 |
|---------|---------|-----|
| 每周一课 | 实际完成 | 不可控，预计100%完成（200分） |
| 每日一题 | 80% | 承担剩余需达分数的80% |
| 每月一考 | 25% + 保底90 | 承担剩余需达分数的25%，最少90分 |

---

## 3. 每周一课规则

### 3.1 周次计算规则

根据当前月份中的周六数量计算周次：

| 场景 | 计入规则 |
|-----|---------|
| 周六在月中 | 正常计入当月 |
| 周六在月初第1天 | 该周末属于上月，不计入当月 |
| 周六在月末最后几天 | 判断下一个周六是否在下月，是则不计入当月 |

### 3.2 每月每周一课次数

- 正常月份：4次（4个周六）
- 5周月份：5次（5个周六）
- 满分：次数 × 50分

---

## 4. 完全动态控分策略

### 4.1 核心公式

```python
# 每次执行任务时动态计算

# 1. 获取基本信息
current_total = ScoreTracker.get_current_month_scores(user_id)["total"]

# 2. 每周一课信息
weekly_info = get_weekly_lessons_info(user_id, year, month)
weekly_actual = weekly_info["actual_score"]
weekly_remaining = weekly_info["remaining_sessions"]
weekly_expected = weekly_actual + weekly_remaining * 50  # 100%预期

# 3. 剩余工作日
remaining_days = get_remaining_working_days_in_month(year, month, now)

# 4. 剩余需达分数
remaining_needed = max(0, 530 - current_total - weekly_expected)
```

### 4.2 每日一题得分计算

```python
if task_type == "daily":
    if ScoreStrategy.is_weekend_or_holiday(now):
        return {"score": 0, ...}  # 周末/节假日不得分
    
    if remaining_needed <= 0:
        ratio = 0.45  # 已达标，最低分
    else:
        # 每日一题承担80%
        daily_needed = remaining_needed * 0.80
        daily_target = daily_needed / remaining_days
        base_ratio = min(daily_target / 20, 1.0)  # 封顶20分
        ratio = max(0.45, min(0.75, base_ratio + variation))
    
    correct_count = min(10, max(1, int(10 * ratio)))
    score = correct_count * 2
```

### 4.3 每月一考得分计算（15号执行）

```python
if task_type == "monthly":
    if remaining_needed <= 0:
        monthly_target = 90  # 保底90分
    else:
        # 每月一考承担25%
        monthly_target = min(100, remaining_needed * 0.25)
        monthly_target = max(90, monthly_target)  # 保底90分
    
    ratio = monthly_target / 100
    correct_count = min(50, max(25, int(50 * ratio)))
    score = correct_count * 2
```

### 4.4 每周一课得分计算

```python
if task_type == "weekly":
    return {"score": 50, "correct_count": 1, ...}  # 必须满分
```

---

## 5. 用户差异化方案

### 5.1 差异化算法

使用用户ID + 日期作为随机种子，保证：
- 同一天同一用户分数固定
- 不同用户同一天分数不同

```python
def apply_user_variation(user_id: int, date: datetime, base_ratio: float) -> float:
    seed = user_id * 10000 + date.toordinal()
    random.seed(seed)
    
    # 正态分布随机波动（均值0，标准差0.08）
    variation = random.normalvariate(0, USER_VARIATION_STD)
    
    # 限制范围
    ratio = max(MIN_SCORE_RATIO, min(MAX_SCORE_RATIO, base_ratio + variation))
    return ratio
```

### 5.2 差异化效果示例

同一天10题满分20分：

| 用户ID | 得分 | 正确题数 |
|-------|-----|---------|
| 1 | 12.3分 | 6题 |
| 2 | 11.7分 | 6题 |
| 3 | 13.1分 | 7题 |
| 4 | 10.9分 | 5题 |
| 5 | 14.2分 | 7题 |

---

## 6. 场景示例

### 6.1 场景1：极端落后（只剩5天，100分）

| 项目 | 数值 |
|-----|-----|
| 当前得分 | 100分 |
| 剩余工作日 | 5天 |
| 每周一课预期 | 200分 |
| 剩余需达 | 230分 |
| 每日一题目标 | 230 × 80% / 5 = 37分/天 → 封顶20分 |
| 每月一考目标 | min(100, 230 × 25%) = 58分 → 保底90分 |
| **月底总分** | **320分** |

> ⚠️ 无法达标，用户严重落后

### 6.2 场景2：正常进度（10天剩余，200分）

| 项目 | 数值 |
|-----|-----|
| 当前得分 | 200分 |
| 剩余工作日 | 10天 |
| 每周一课预期 | 220分 |
| 剩余需达 | 110分 |
| 每日一题目标 | 110 × 80% / 10 = 9分 → 9分/天 |
| 每月一考目标 | min(100, 110 × 25%) = 28分 → 保底90分 |
| **月底总分** | **~420分** |

### 6.3 场景3：良好进度（10天剩余，300分）

| 项目 | 数值 |
|-----|-----|
| 当前得分 | 300分 |
| 剩余工作日 | 10天 |
| 每周一课预期 | 220分 |
| 剩余需达 | 10分 → ≤0 |
| 每日一题得分率 | 45%（最低） |
| 每月一考目标 | 90分（保底） |
| **月底总分** | **~535分** |

### 6.4 场景4：已超标（5天剩余，400分）

| 项目 | 数值 |
|-----|-----|
| 当前得分 | 400分 |
| 剩余工作日 | 5天 |
| 每周一课预期 | 220分 |
| 剩余需达 | -90分 → 0 |
| 每日一题得分率 | 45% |
| 每月一考目标 | 90分（保底） |
| **月底总分** | **~545分** |

---

## 7. 效果汇总

| 场景 | 当前得分 | 剩余天数 | 每日得分 | 每月一考 | 月底总分 |
|-----|---------|---------|---------|---------|---------|
| 极端落后 | 100分 | 5天 | 20分×5 | 90分 | **320分** |
| 正常1 | 200分 | 10天 | 9分×10 | 90分 | **420分** |
| 正常2 | 300分 | 10天 | 9分×10 | 90分 | **~535分** |
| 良好 | 400分 | 10天 | 9分×10 | 90分 | **~545分** |
| 超标 | 500分 | 5天 | 9分×5 | 90分 | **~545分** |

---

## 8. 常量定义

```python
class ScoreStrategy:
    TARGET_MONTHLY_SCORE = 530
    MIN_SCORE_RATIO = 0.45
    MAX_SCORE_RATIO = 0.75
    USER_VARIATION_STD = 0.08
    DAILY_ALLOCATE_RATIO = 0.80  # 每日一题分配80%
    MONTHLY_ALLOCATE_RATIO = 0.25  # 每月一考分配25%
    MONTHLY_BASE_SCORE = 90  # 每月一考保底90分
```

---

## 9. 代码变更清单

### 9.1 score_strategy.py

| 方法 | 变更类型 | 说明 |
|-----|---------|-----|
| `calculate_strategy()` | 重写 | 完全动态核心逻辑 |
| `calculate_daily_target_with_compensation()` | 删除 | 旧方案不再使用 |
| `calculate_daily_score()` | 删除 | 逻辑合并到calculate_strategy |
| `get_saturdays_in_month()` | 保留 | 计算当月周六 |
| `get_weekly_lessons_info()` | 保留 | 获取每周一课信息 |
| `get_working_days_in_month()` | 保留 | 计算工作日 |
| `get_remaining_working_days_in_month()` | 保留 | 计算剩余工作日 |

### 9.2 score_tracker.py

| 方法 | 变更类型 | 说明 |
|-----|---------|-----|
| `weekly_score()` |get_monthly_ 保留 | 获取本月每周一课得分 |

---

## 10. 验收标准

1. [ ] 正常进度月底总分在535-560之间
2. [ ] 每周一课缺失时，通过补救机制仍能达标
3. [ ] 同一天不同用户分数不同
4. [ ] 每日一题得分率平滑，控制在45%-75%之间
5. [ ] 周末和节假日不答题不得分
6. [ ] 每月一考15号执行，根据当前进度动态计算

---

## 11. 风险与注意事项

1. **chinese_calendar 库**：需确认节假日数据准确性
2. **数据库查询**：确保查询性能，避免每月查询过慢
3. **边界场景**：月初、月末的特殊日期处理
4. **15号每月一考**：需确保当天有任务执行

---

> 文档版本：v2.0
> 最后更新：2026-01-31
> 状态：已完成实现
