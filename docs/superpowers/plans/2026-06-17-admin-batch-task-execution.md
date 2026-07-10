# 管理员后台批量任务执行功能 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans

**Goal:** 在 admin_v2 任务管理页面添加批量执行任务功能

**Architecture:** 后端新增 `batch_execute_tasks` 用 `ThreadPoolExecutor` 并行执行；前端新增 checkbox 列 + 全选 + 批量执行按钮

**Tech Stack:** Python 3, NiceGUI, SQLAlchemy, concurrent.futures

**Files:**
- Modify: `ccsa_auto/admin_v2/services/task_service.py`
- Modify: `ccsa_auto/admin_v2/pages/tasks.py`

---

### Task 1: 后端 — 新增 `batch_execute_tasks` 方法

**Files:**
- Modify: `ccsa_auto/admin_v2/services/task_service.py`

- [ ] **Step 1: 添加 ThreadPoolExecutor 导入**

在 `ccsa_auto/admin_v2/services/task_service.py` 顶部找到 `from typing import Dict, Any, List, Optional`，修改为：

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
```

- [ ] **Step 2: 添加 `batch_execute_tasks` 方法**

在 `trigger_task` 方法（第 185-195 行）之后，`delete_task` 方法之前插入：

```python
    @staticmethod
    def batch_execute_tasks(task_ids: List[int]) -> Dict[str, Any]:
        """
        批量执行任务（并行）

        Args:
            task_ids: 任务ID列表

        Returns:
            dict: {success, message, success_count, failed_count, total, results}
        """
        if not task_ids:
            return {
                "success": False,
                "message": "未选择任务",
                "success_count": 0,
                "failed_count": 0,
                "total": 0,
                "results": [],
            }

        from ccsa_auto.core.database import SessionLocal
        from ccsa_auto.core.models import Task, User
        from ccsa_auto.modules.task.service import TaskService
        from ccsa_auto.modules.logging.service import LoggingService
        from datetime import datetime

        results = []
        success_count = 0
        failed_count = 0

        def _execute_single(tid: int) -> dict:
            db = SessionLocal()
            try:
                task = db.query(Task).filter_by(id=tid).first()
                if not task:
                    return {"task_id": tid, "success": False, "message": "任务不存在"}

                user = db.query(User).filter_by(id=task.user_id).first()
                if not user:
                    return {"task_id": tid, "success": False, "message": "用户不存在"}

                if not task.is_active:
                    return {"task_id": tid, "success": False, "message": "任务未激活"}

                task.execution_status = "running"
                task.updated_at = datetime.utcnow()
                db.commit()

                exec_result = TaskService.execute_task(task, user)

                task.execution_status = "completed" if exec_result.get("success") else "failed"
                task.external_status = "success" if exec_result.get("success") else "failed"
                task.result = str(exec_result)
                task.executed_at = datetime.utcnow()
                task.updated_at = datetime.utcnow()
                db.commit()

                LoggingService.log_task_execution(
                    task_id=tid,
                    user_id=task.user_id,
                    task_type=task.task_type,
                    status="success" if exec_result.get("success") else "failed",
                    message=exec_result.get("message", str(exec_result)),
                )

                return {
                    "task_id": tid,
                    "success": exec_result.get("success", False),
                    "message": exec_result.get("message", ""),
                }
            except Exception as e:
                try:
                    db.rollback()
                    task = db.query(Task).filter_by(id=tid).first()
                    if task:
                        task.execution_status = "failed"
                        task.external_status = "failed"
                        task.result = f"批量执行异常: {str(e)}"
                        task.updated_at = datetime.utcnow()
                        db.commit()
                except Exception:
                    pass
                return {"task_id": tid, "success": False, "message": str(e)}
            finally:
                db.close()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(_execute_single, tid): tid for tid in task_ids}
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    if result.get("success"):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    tid = futures[future]
                    results.append({"task_id": tid, "success": False, "message": str(e)})
                    failed_count += 1

        return {
            "success": failed_count == 0,
            "message": f"批量执行完成：成功 {success_count} 条，失败 {failed_count} 条",
            "success_count": success_count,
            "failed_count": failed_count,
            "total": len(task_ids),
            "results": results,
        }
```

- [ ] **Step 3: 验证语法**

```bash
cd G:\work\python\CCSA_Auto && uv run python -c "from ccsa_auto.admin_v2.services.task_service import TaskManagementService; print('OK')"
```

- [ ] **Step 4: 提交**

```bash
git add ccsa_auto/admin_v2/services/task_service.py
git commit -m "feat(admin): 新增 batch_execute_tasks 批量并行执行任务方法"
```

---

### Task 2: 前端 — 新增 checkbox 勾选 + 批量执行按钮

**Files:**
- Modify: `ccsa_auto/admin_v2/pages/tasks.py`

- [ ] **Step 1: 添加选中状态和批量执行函数**

在 `create_tasks_page` 的 state 区域（第 10-16 行后）添加：

```python
    selected_ids = {"value": []}
    is_executing = {"value": False}
```

在 `delete_task` 函数（第 72-79 行）之后添加选中相关函数（`on_batch_execute` 稍后在 Step 2 中定义，因为需要引用 `batch_btn` 变量）：

```python
    def on_select_all(checked: bool):
        """全选/取消全选当前页"""
        if checked:
            for task in tasks_data["data"]:
                tid = task["id"]
                if tid not in selected_ids["value"]:
                    selected_ids["value"] = selected_ids["value"] + [tid]
        else:
            page_ids = {task["id"] for task in tasks_data["data"]}
            selected_ids["value"] = [tid for tid in selected_ids["value"] if tid not in page_ids]

    def on_select_task(task_id: int, checked: bool):
        """勾选/取消勾选单个任务"""
        if checked:
            if task_id not in selected_ids["value"]:
                selected_ids["value"] = selected_ids["value"] + [task_id]
        else:
            selected_ids["value"] = [tid for tid in selected_ids["value"] if tid != task_id]
```

- [ ] **Step 2: 工具栏添加批量执行按钮**

在状态过滤器之后（第 165 行 `</ui.card>` 之前），添加批量执行按钮行：

```python
            # Batch execute
            with ui.row().classes("items-center gap-2 ml-auto"):
                batch_btn = ui.button(
                    "批量执行",
                    icon="playlist_play",
                    on_click=on_batch_execute,
                ).props("color=primary")
```

在 `on_select_all` 函数之后添加 `on_batch_execute`：

```python
    def on_batch_execute():
        """批量执行选中任务"""
        ids = list(selected_ids["value"])
        if not ids:
            return
        batch_btn.props("disabled")
        is_executing["value"] = True
        try:
            result = TaskManagementService.batch_execute_tasks(ids)
            selected_ids["value"] = []
            load_tasks()
            if result.get("success"):
                ui.notify(result.get("message", "批量执行完成"), type="positive")
            else:
                failed = result.get("failed_count", 0)
                if failed > 0:
                    ui.notify(result.get("message", "批量执行完成"), type="warning")
                else:
                    ui.notify(result.get("message", "批量执行完成"), type="positive")
        except Exception as e:
            ui.notify(f"批量执行失败: {str(e)}", type="negative")
        finally:
            batch_btn.props(remove="disabled")
            is_executing["value"] = False
```

- [ ] **Step 3: 表格列数从 9 列改为 10 列**

修改表头（第 168-169 行）的 grid 列数：

```python
    "grid grid-cols-10 gap-4 pb-4 border-b border-gray-100 mb-4 shrink-0"
```

在表头第一列（第 171 行 `ui.label("ID")` 之前）插入全选 checkbox：

```python
            with ui.element("div").classes("flex items-center"):
                all_check = ui.checkbox(on_change=lambda e: on_select_all(e.value))
```

- [ ] **Step 4: 修改表格数据行，添加单行 checkbox 并调整列宽**

修改第 189-320 行的数据行循环。将 grid 列数改为 10，在每行第一列插入 checkbox：

将第 193 行的：
```python
    f"grid grid-cols-9 gap-4 py-4 {row_bg} items-center"
```
改为：
```python
    f"grid grid-cols-10 gap-4 py-4 {row_bg} items-center"
```

在第 195 行（ID 列）之前插入 checkbox 列：

```python
                    with ui.element("div").classes("flex items-center"):
                        ui.checkbox(
                            value=task.get("id") in selected_ids["value"],
                            on_change=lambda e, tid=task.get("id"): on_select_task(tid, e.value),
                        )
```

- [ ] **Step 5: 验证语法**

```bash
cd G:\work\python\CCSA_Auto && uv run python -c "from ccsa_auto.admin_v2.pages import *; print('OK')"
```

- [ ] **Step 6: 启动并手动测试**

```bash
cd G:\work\python\CCSA_Auto && uv run python app.py
```

访问 `http://localhost:8082/admin_v2/tasks`，验证：
1. 表格首列出现 checkbox
2. 表头有全选 checkbox
3. 勾选若干任务后「批量执行」按钮显示选中数量并变为可用
4. 点击批量执行后按钮 loading，完成后刷新表格 + 通知

- [ ] **Step 7: 提交**

```bash
git add ccsa_auto/admin_v2/pages/tasks.py
git commit -m "feat(admin): 任务管理新增批量执行功能（checkbox 勾选 + 批量执行按钮）"
```
