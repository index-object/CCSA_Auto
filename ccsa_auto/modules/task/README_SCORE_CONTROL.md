# 控分策略使用说明

## 概述

控分策略模块用于自动控制每月的得分，确保总得分不低于530分，同时避免超过太多。

## 文件说明

- `score_tracker.py` - 分数追踪服务，用于记录和查询得分
- `score_strategy.py` - 控分策略服务，用于计算和控制得分
- `score_control.py` - 模块导出文件

## 依赖

本模块依赖 `chinese-calendar` 库来精确识别中国法定节假日，已通过 uv 安装：

```bash
uv pip install chinese-calendar
```

## 功能特性

### 1. 任务得分规则

| 任务类型 | 满分 | 得分规则 |
|---------|------|---------|
| 每日一题 | 20分/次 | 10道题，每题2分 |
| 每周一课 | 50分/次 | 每周一次，固定50分，无法控分 |
| 每月一考 | 100分/次 | 50道题，每题2分 |

### 2. 控分策略核心规则

- **最低得分比例**: 每次任务最少得满分的50%
- **目标月度得分**: 530分
- **周末/节假日**: 每日一题在周六日和法定节假日不得分（使用 chinese-calendar 库精确判断）
- **动态调整**: 根据当前得分和剩余潜力动态调整策略
- **优先单选**: 优先选择单选题进行控分，避免多选题答错失分过多

### 3. 节假日识别

使用 `chinese-calendar` 库精确识别以下节假日：
- 元旦（1月1日）
- 春节（农历正月初一及其前后调休）
- 清明节
- 劳动节（5月1日及其前后调休）
- 端午节
- 中秋节
- 国庆节（10月1日及其前后调休）
- 所有周末（周六、周日）

**注意**：工作日的每日一题可获得满分或按策略控分；周末和法定节假日的每日一题不得分。

### 4. 策略计算逻辑

1. 如果当前月度得分 >= 530分，使用最低得分比例（50%）
2. 如果当前月度得分 < 530分，根据剩余潜力计算得分比例
3. 每次任务最少得满分的50%
4. 如果已经超过530分，允许继续超过（不能通过不完成任务来减少）

### 5. 答案修改逻辑

控分策略通过修改部分题目的答案来实现得分控制：

#### 单选题答案修改

使用**相邻互换**的方式生成错误答案：

| 正确答案 | 错误答案 | 说明 |
|---------|---------|------|
| A | B | A和B互换 |
| B | A | B和A互换 |
| C | D | C和D互换 |
| D | C | D和C互换 |

这种方式可以确保错误答案看起来仍然是一个合法的选项，而不是明显错误的值。

#### 多选题答案修改

采用**替换其中一个选项**的方式生成错误答案：

1. 保留至少一个正确选项（确保最少得50%）
2. 从选项池中随机选择一个不在正确答案中的选项
3. 替换掉正确答案中的一个选项

示例：
- 正确答案：`A,B` → 错误答案：`A,D`
- 正确答案：`A,B,C` → 错误答案：`A,B,E`
- 正确答案：`A,B,C,D` → 错误答案：`A,B,C,E`

#### 题目选择策略

- **优先选择单选题**：单选题每题2分，答错失分较少
- **单选题不足时选择多选题**：多选题通常分值更高（如5分），但只有在单选题数量不足时才会被选中

#### 答案格式

根据接口信息，答案格式为带引号的选项字母：

- 单选题：`"A"`, `"B"`, `"C"`, `"D"`
- 多选题：`"A,B"`, `"A,B,C"`, `"A,B,C,D"`

## 使用方法

### 初始化数据库

运行数据库迁移脚本创建得分记录表：

```bash
.venv\Scripts\python.exe migrate_score_records.py
```

### 测试控分策略

运行测试脚本验证策略逻辑：

```bash
.venv\Scripts\python.exe test_score_strategy.py
```

### 测试节假日计算

运行节假日测试脚本验证节假日识别功能：

```bash
.venv\Scripts\python.exe test_holiday_calculation.py
```

### 测试答案修改

运行答案修改测试验证答案修改逻辑：

```bash
.venv\Scripts\python.exe test_answer_modification.py
```

### 在任务中使用

控分策略已经集成到 `TaskService` 中，无需额外配置。执行任务时会自动：

1. 计算当前月度得分
2. 计算本次任务的控分策略
3. 优先选择单选题进行控分
4. 使用相邻互换方式修改单选题答案
5. 使用替换选项方式修改多选题答案
6. 记录得分到数据库

### API使用示例

#### 计算控分策略

```python
from ccsa_auto.modules.task.score_strategy import ScoreStrategy

# 计算每日一题策略
strategy = ScoreStrategy.calculate_strategy(
    user_id=1,
    task_type="daily",
    total_questions=10,
    score_per_question=2.0
)

print(f"需要答对: {strategy['correct_questions']}/10 题")
print(f"预期得分: {strategy['score']}/{strategy['max_score']}")
```

#### 修改答案以控分

```python
from ccsa_auto.modules.task.score_strategy import ScoreStrategy

# 模拟题目列表
questions = [
    {
        "id": i,
        "questionType": 1,  # 1=单选题，2=多选题
        "questionPoint": 2,
        "questionAnswer": '"A"'
    }
    for i in range(10)
]

# 应用控分策略（优先选择单选题）
modified_questions, strategy = ScoreStrategy.modify_answers_for_score_control(
    questions, "daily", user_id=1
)
```

#### 单选题答案修改

```python
from ccsa_auto.modules.task.score_strategy import ScoreStrategy

# 生成单选题的错误答案
wrong_answer = ScoreStrategy.get_wrong_answer_for_single_choice('"A"')
print(f"正确答案: \"A\" -> 错误答案: {wrong_answer}")
# 输出: 正确答案: "A" -> 错误答案: "B"
```

#### 多选题答案修改

```python
from ccsa_auto.modules.task.score_strategy import ScoreStrategy

# 生成多选题的错误答案
wrong_answer = ScoreStrategy.get_wrong_answer_for_multiple_choice('"A,B"')
print(f"正确答案: \"A,B\" -> 错误答案: {wrong_answer}")
# 输出类似: 正确答案: "A,B" -> 错误答案: "A,D"
```

#### 查询月度得分

```python
from ccsa_auto.modules.task.score_tracker import ScoreTracker

# 获取当前月度得分
current_scores = ScoreTracker.get_current_month_scores(user_id=1)
print(f"总分: {current_scores['total']}")
print(f"每日一题: {current_scores['daily']}")
print(f"每周一课: {current_scores['weekly']}")
print(f"每月一考: {current_scores['monthly']}")
```

#### 记录得分

```python
from ccsa_auto.modules.task.score_tracker import ScoreTracker

ScoreTracker.record_score(
    user_id=1,
    task_id=123,
    task_type="daily",
    total_questions=10,
    correct_questions=8,
    score=16.0,
    max_score=20.0
)
```

#### 判断是否为节假日

```python
from ccsa_auto.modules.task.score_strategy import ScoreStrategy
from datetime import datetime

from ccsa_auto.utils.timezone import SHANGHAI_TZ

# 判断某个日期是否为节假日
date = datetime(2026, 1, 1).replace(tzinfo=SHANGHAI_TZ)
is_holiday = ScoreStrategy.is_weekend_or_holiday(date)
print(f"2026年1月1日 {'是' if is_holiday else '不是'}节假日")
```

## 注意事项

1. **周末和节假日**: 每日一题在周六日和法定节假日不得分（使用 chinese-calendar 库精确识别）
2. **最低得分**: 每次任务最少得满分的50%，不能设置为0分
3. **动态调整**: 策略会根据当前得分动态调整，如果月中开始策略会自动适应
4. **每月一课**: 无法控分，必须完成，固定50分
5. **数据库迁移**: 首次使用前必须运行 `migrate_score_records.py` 创建得分记录表
6. **节假日数据**: chinese-calendar 库包含从 2004 年到未来的节假日数据
7. **优先单选**: 控分策略优先选择单选题进行修改，因为单选题分值较低，风险较小
8. **答案格式**: 答案必须带引号，如 `"A"`、`"A,B"`

## 配置参数

可以在 `ScoreStrategy` 类中修改以下参数：

```python
MIN_SCORE_RATIO = 0.5  # 最低得分比例
TARGET_MONTHLY_SCORE = 530  # 目标月度得分
```

## 日志输出

执行任务时会输出控分策略信息：

```
控分策略: 当前得分: 480, 目标: 530, 需要答对: 8/10 题, 预期得分: 16.0/20.0
```

## 故障排除

### 节假日库错误

如果 chinese-calendar 库不可用，系统会自动回退到简单的周末判断（仅判断周六日）。

### 工作日数量变化

使用节假日库后，工作日数量会比简单周末判断更准确，因为排除了调休的工作日和添加了调休的周末。

### 答案格式错误

如果答案格式不正确（如缺少引号），可能会导致答题失败。确保答案格式为：
- 单选题：`"A"`
- 多选题：`"A,B"`

### 多选题控分

多选题由于分值较高（通常5分），答错失分较多。因此策略优先选择单选题进行控分，只有在单选题数量不足时才会选择多选题。
