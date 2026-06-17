# 管理员后台批量任务执行功能设计

## 概述

在 admin_v2 的任务管理页面中，新增批量执行任务功能。管理员可勾选多条任务后一键执行，通过后端线程池并行执行所有选中任务，执行完成后刷新表格并通过通知展示结果。

## 需求

1. 表格每行增加 checkbox，支持勾选多条任务
2. 表头增加全选 checkbox（控制当前页）
3. 工具栏新增「批量执行」按钮，选中任务后启用
4. 并行执行所有选中任务
5. 执行完成后刷新表格 + 通知显示成功/失败汇总

## 后端设计

### TaskManagementService.batch_execute_tasks

文件: `ccsa_auto/admin_v2/services/task_service.py`

新增静态方法:

```python
@staticmethod
def batch_execute_tasks(task_ids: List[int]) -> Dict[str, Any]:
```

**参数**: 任务 ID 列表
**返回**: `{success_count, failed_count, total, results: [{task_id, success, message}]}`

**执行流程:**
1. 遍历 task_ids，从 DB 查询每个 Task 和对应的 User，过滤无效的
2. 使 `concurrent.futures.ThreadPoolExecutor(max_workers=5)` 并行提交
3. 每个任务线程内:
   - 获取独立的 DB session
   - 将任务状态更新为 `running`
   - 调用 `TaskService.execute_task(task, user)`
   - 根据结果更新状态为 `completed` / `failed`
   - 记录操作日志
   - 关闭 session
4. 等待所有任务完成，汇总结果
5. 返回汇总数据

**并发控制：**
- ThreadPoolExecutor max_workers=5，避免过多并发冲击外部平台
- 每个线程使用独立 DB session，避免 session 冲突

## 前端设计

### 文件: `ccsa_auto/admin_v2/pages/tasks.py`

**新增状态变量:**
```python
selected_ids: set = set()  # 勾选的任务 ID 集合
is_executing: bool = False  # 批量执行中标志
```

**UI 变更：**
1. 表格列数由 9 列变为 10 列，第 1 列为 checkbox
2. 表头第一列为全选 checkbox
3. 工具栏新增「批量执行」按钮，图标 `playlist_play`
4. 按钮文字 `批量执行 (N)` 随选中数量动态变化
5. 未选中或执行中时按钮 disabled
6. 切换页面时清空 `selected_ids`

**交互流程:**
1. 管理员勾选任务 → selected_ids 更新
2. 点击「批量执行」→ 按钮进入 loading 状态
3. 调用 `TaskManagementService.batch_execute_tasks(list(selected_ids))`
4. 完成后:
   - 刷新任务列表
   - `ui.notify` 显示汇总结果（成功/失败数量）
   - 清空 selected_ids
   - 按钮恢复

## 错误处理

- 无效 task_id: 跳过并计入失败
- 任务执行异常: 捕获异常，计入失败，不影响其他任务
- 网络超时: 由 TaskService.execute_task 内部的重试机制处理
- 总体超时: 暂不设整体超时（任务数量由管理员控制）

## 未涉及的范围

- 跨页全选（仅当前页全选，翻页后清空）
- 批量启用/禁用（可后续扩展）
- 批量删除（可后续扩展）
- 执行进度实时反馈（对管理后台场景过度设计）
