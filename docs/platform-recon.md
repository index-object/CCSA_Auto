# 平台侦察工具（platform_recon）

平台（https://edu.axdxa.cn）是 Vite SPA，接口契约会随前端发版变化。出现「本地任务成功、平台却没记录」时，用真实浏览器跑一遍、对比实际请求体，比猜字段可靠。

## 依赖

Playwright 不进项目依赖，按需安装：

```bash
uv pip install playwright
```

使用系统已安装的 Microsoft Edge，无需下载 Chromium。

## 用法

在仓库根目录执行：

```bash
# 1. 打开学习中心，录制所有接口请求/响应
uv run python -m scripts.platform_recon <账号> <密码>

# 2. 打开本周周课页并真实播放（自动查询本周课程 id、点击播放）
uv run python -m scripts.platform_recon <账号> <密码> --play --seconds 600

# 3. 打开任意页面
uv run python -m scripts.platform_recon <账号> <密码> --url https://edu.axdxa.cn/weekClass/history

# 4. 把完整流量写入 JSON
uv run python -m scripts.platform_recon <账号> <密码> --play --out events.json
```

### 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `username` / `password` | 平台账号（数据库 `users.external_username` / `external_password`） | 必填 |
| `--url` | 要打开的页面 | `https://edu.axdxa.cn/user/learnCenter` |
| `--play` | 打开本周周课页并播放视频 | 关 |
| `--seconds` | 页面停留/播放观察时长 | 30 |
| `--headless` | 无头模式（不弹窗） | 关 |
| `--out` | 完整流量写入 JSON 文件 | 不写 |

## 输出

- 终端：按时间顺序列出 `XHR/fetch` 请求（含 POST body）及对应响应（截断到 2000 字符），最后打印视频播放状态。
- `--out`：同内容写入 JSON，便于对比两次发版之间的接口差异。

## 登录方式

不走登录页（避开验证码）：先调用 `auth-v2/pwdLogin` 取 token，再注入 `localStorage['Admin-Token']` 打开 SPA。

## 已知平台规则（2026-10 实测）

每周一课的 `progressReporter` 按「本次观看增量」记账：

- 请求体字段：`studyProgressTime`（播放位置）、`studyDuration`（本次实际观看秒数）、`studyAssociationId`、`weeklyCourseId`、`studyType=4`、`studySchedule`、`version`
- 真实客户端每 `vodReportingFrequency=120` 秒上报一次，`studyDuration` 约为 120
- 单次 `studyDuration` 超过 120 秒的部分会被静默丢弃（接口仍返回 `200 操作成功`），一次报满 100% 平台不登记
- 正确做法：按 120 秒步长累加上报，见 `TaskService.execute_weekly_lesson`

每日一题 / 每月一考的交卷耗时（2026-09-28 起）：

- 前端提交体仍带 `useTime`，但平台改为按服务端记录的「取题到交卷」真实耗时记账，客户端上报值不再生效
- 取题后立即交卷会记 `useTime=0` 或 `-1`（2026-09-27 及以前为 181/245/279 等正常值）
- 正确做法：取题后真实等待到目标时长再交卷；`examDuration` 取自
  `regularStudyDayRuleSetting` / `regularExamMonthRuleSetting` 的 `answeringTime`，
  `examDetailId` 取 `id ?? examDetailId`，见 `TaskService._execute_regular_exam`

## 注意

- 脚本会在本机启动 Edge 窗口，加 `--headless` 可避免。
- 抓到的响应可能含 token / 个人信息，`--out` 生成的文件不要提交到仓库。
