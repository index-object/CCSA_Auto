# -*- coding: utf-8 -*-
"""新版（v2）第三方平台接口适配验证脚本。

覆盖：
  1. 登录加密（AES-256-ECB/PKCS7 + RSA PKCS#1 v1.5）
  2. 登录请求构造（isencrypt / encrypt-key）
  3. 试题标准答案归一化
  4. v2 接口清单校验（无遗留旧路径）
  5. 三个一状态解析

用法：
  uv run python test_platform_api_v2.py
"""

import base64
import json
import sys

from ccsa_auto.core.config import Config
from ccsa_auto.modules.auth import service as auth_service
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.modules.task.service import TaskService
from ccsa_auto.utils import crypto
from refactored_code.auth_module import AuthModule
from refactored_code.config import Config as RefactoredConfig

_passed = 0


def check(name, condition, detail=""):
    global _passed
    if condition:
        _passed += 1
        print(f"  [PASS] {name}")
    else:
        raise AssertionError(f"[FAIL] {name} {detail}")


def test_aes_roundtrip():
    print("\n[1] AES-256-ECB/PKCS7 往返")
    key = crypto.generate_aes_key()
    check("AES 密钥为 32 字节", len(key) == 32, len(key))

    payload = json.dumps({"username": "13800000000", "password": "p@ss"}, ensure_ascii=False)
    body = crypto.aes_encrypt(payload, key)
    check("密文为合法 base64", base64.b64decode(body) is not None)
    check("密文长度为块大小整数倍", len(base64.b64decode(body)) % 16 == 0)
    check("解密还原明文", crypto.aes_decrypt(body, key) == payload)

    # 中文/长文本
    long_text = "每日一题" * 100
    check(
        "中文长文本往返",
        crypto.aes_decrypt(crypto.aes_encrypt(long_text, key), key) == long_text,
    )


def test_rsa_and_payload():
    print("\n[2] RSA 加密与登录载荷")
    pub = crypto._get_public_key()
    check("公钥为 512 bit", pub.key_size == 512, pub.key_size)

    cipher = base64.b64decode(crypto.rsa_encrypt(b"hello"))
    check("RSA 密文为 64 字节", len(cipher) == 64, len(cipher))

    payload = {"username": "u", "password": "p", "clientId": RefactoredConfig.CLIENT_ID}
    body, encrypt_key = crypto.encrypt_payload(payload)
    check("body 为字符串", isinstance(body, str))
    check("encrypt-key 为 64 字节 RSA 密文", len(base64.b64decode(encrypt_key)) == 64)
    check("body 可 base64 解码", len(base64.b64decode(body)) % 16 == 0)


def test_login_request():
    print("\n[3] 登录请求构造")
    module = AuthModule()
    body, headers = module._build_login_request()

    check("包含 isencrypt=true", headers.get("isencrypt") == "true")
    check("包含 encrypt-key", bool(headers.get("encrypt-key")))
    check("clientid 为新值", headers.get("ClientId") == RefactoredConfig.CLIENT_ID)

    # 与前端一致：base64 密文以 JSON 字符串形式发送（带引号）
    decoded = json.loads(body)
    check("请求体是 JSON 字符串", isinstance(decoded, str))
    base64.b64decode(decoded)
    check("登录地址为 auth-v2", RefactoredConfig.LOGIN_URL.endswith("auth-v2/pwdLogin"))
    check("登录数据 clientId 已更新", RefactoredConfig.LOGIN_DATA["clientId"] == RefactoredConfig.CLIENT_ID)


def test_answer_normalization():
    print("\n[4] 试题答案归一化")
    cases = [
        ('"D"', "D"),
        ('"A,B,C"', "A,B,C"),
        ("ABD", "A,B,D"),
        ("A,B,C,D,E", "A,B,C,D,E"),
        (["A", "C"], "A,C"),
        ("a", "A"),
        ("", None),
        (None, None),
    ]
    for raw, expected in cases:
        got = TaskService._normalize_question_answer(raw)
        check(f"{raw!r} -> {expected!r}", got == expected, f"got {got!r}")


def test_build_questions():
    print("\n[5] 由平台题目构造提交项")
    from ccsa_auto.core.database import Base, SessionLocal, engine
    from ccsa_auto.core.models import QuestionBank

    # 本地题库回退需要 question_bank 中有同类型题目；测试自备一条，避免依赖已有数据
    Base.metadata.create_all(engine)
    db = SessionLocal()
    seed_id = "test-fallback-q1"
    try:
        if not db.query(QuestionBank).filter_by(question_id=seed_id).first():
            db.add(
                QuestionBank(
                    question_id=seed_id,
                    question_type=1,
                    question_point=5,
                    question_answer="A",
                    source_exam_type=2,
                )
            )
            db.commit()

        question_list = [
            {
                "id": "q1",
                "questionType": 1,
                "questionPoint": 5,
                "questionAnswera": '"B"',
                "bankId": "bank-1",
            },
            {
                "id": "q2",
                "questionType": 2,
                "questionPoint": 5,
                "questionAnswera": '"A,C"',
                "bankId": "bank-1",
            },
            {
                "id": "q3",
                "questionType": 1,
                "questionPoint": 5,
                "questionAnswera": None,
                "bankId": "bank-1",
            },
        ]
        questions = TaskService._build_questions_from_api(question_list, 2)
    finally:
        db.query(QuestionBank).filter_by(question_id=seed_id).delete()
        db.commit()
        db.close()

    check("返回题目数量", len(questions) == 3, len(questions))
    check("包含 bankId", questions[0].get("bankId") == "bank-1")
    check("单选答案归一化", questions[0]["questionAnswer"] == "B")
    check("多选答案归一化", questions[1]["questionAnswer"] == "A,C")
    check("缺失API答案时回退本地题库", bool(questions[2]["questionAnswer"]))
    check("回退题目不再沿用原 bankId", "bankId" not in questions[2])


def test_endpoint_map():
    print("\n[6] v2 接口清单")
    endpoints = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"]
    legacy = {
        "GET_STUDY_LIST",
        "getNewRegularStudyList",
        "studyScheduleEscalation",
        "selectUrlByVodId",
        "system/app/userExtend",
    }

    for key, url in endpoints.items():
        check(f"{key} 使用 v2 命名空间", "-v2/" in url, url)
        for token in legacy:
            check(f"{key} 不含遗留路径 {token}", token not in url, url)

    expected = {
        "GET_REGULAR_STUDY_DAY": "progress-v2/app/regularStudy/getRegularStudyDay",
        "GET_REGULAR_STUDY_WEEK": "progress-v2/app/regularStudy/getRegularStudyWeek",
        "GET_REGULAR_STUDY_MONTH": "progress-v2/app/regularStudy/getRegularStudyMonth",
        "SUBMIT_EXAM": "progress-v2/app/regularExamRecord",
        "SUBMIT_STUDY_SCHEDULE": "platform-resource-v2/app/weeklyCourse/progressReporter",
        "GET_WEEKLY_LESSON": "progress-v2/app/regularCourseWeek/{lesson_id}",
        "GET_VIDEO_URL": "progress-v2/app/regularCourseWeek/courseWeekPlayAuth/{lesson_id}",
        "GET_SCORES": "progress-v2/app/regularStudyRecord/getRegularFractionInfo",
        "GET_DAILY_RULE_SETTING": "progress-v2/app/regularStudyDayRuleSetting/{practice_id}",
        "GET_MONTHLY_RULE_SETTING": "progress-v2/app/regularExamMonthRuleSetting/{practice_id}",
    }
    for key, suffix in expected.items():
        check(f"{key} 路径正确", endpoints[key].endswith(suffix), endpoints[key])

    check(
        "登录地址为 auth-v2/pwdLogin",
        Config.EXTERNAL_PLATFORM["LOGIN_URL"].endswith("auth-v2/pwdLogin"),
    )
    check(
        "登录 clientId 已更新",
        Config.EXTERNAL_PLATFORM["LOGIN_CLIENT_ID"] == "e5cd7e4891bf95d1d19206ce24a7b32e",
    )


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


def test_task_status_parsing():
    print("\n[7] 三个一状态解析")

    def fake_get(url, headers=None, params=None, **kwargs):
        if url.endswith("getRegularStudyDay"):
            return _FakeResponse(
                {
                    "code": 200,
                    "data": {
                        "id": "d1",
                        "studyName": "每日一学",
                        "studyStatus": 1,
                        "availableScore": 20,
                        "obtainedScore": None,
                    },
                }
            )
        if url.endswith("getRegularStudyWeek"):
            return _FakeResponse(
                {
                    "code": 200,
                    "data": {
                        "id": "w1",
                        "courseName": "每周一课",
                        "studyStatus": 2,
                        "availableScore": 50,
                        "obtainedScore": 50,
                    },
                }
            )
        if url.endswith("getRegularStudyMonth"):
            return _FakeResponse(
                {
                    "code": 200,
                    "data": {
                        "id": "m1",
                        "examName": "每月一考",
                        "studyStatus": 2,
                        "availableScore": 100,
                        "obtainedScore": 100,
                    },
                }
            )
        raise AssertionError(f"unexpected url {url}")

    original_get = auth_service.requests.get
    auth_service.requests.get = fake_get
    try:
        status, error, is_auth_error = AuthService._fetch_task_status("token")
    finally:
        auth_service.requests.get = original_get

    check("解析成功", error is None and status is not None, error)
    check("每日未完成", status["daily"]["status"] == "未完成", status["daily"])
    check("每日名称", status["daily"]["name"] == "每日一学")
    check("每周已完成", status["weekly"]["status"] == "已完成")
    check("每月得分", status["monthly"]["obtained_score"] == 100)
    check("无认证错误", is_auth_error is False)


def test_weekly_submit_payload():
    print("\n[8] 每周一课提交 payload")
    from ccsa_auto.modules.task import service as task_service
    from ccsa_auto.modules.task.score_tracker import ScoreTracker

    captured = {}

    def fake_get(url, headers=None, params=None, **kwargs):
        if url.endswith("getRegularStudyWeek"):
            return _FakeResponse({"code": 200, "data": {"id": "w1"}})
        if url.endswith("/regularCourseWeek/w1"):
            return _FakeResponse(
                {
                    "code": 200,
                    "data": {
                        "id": "w1",
                        "resourceId": "r1",
                        "resourceUrl": "v1",
                        "resourceDuration": 606,
                    },
                }
            )
        if url.endswith("courseWeekPlayAuth/w1"):
            return _FakeResponse({"code": 200, "data": {"playAuth": "x"}})
        raise AssertionError(f"unexpected url {url}")

    def fake_post(url, headers=None, json=None, **kwargs):
        captured["url"] = url
        captured.setdefault("payloads", []).append(json)
        return _FakeResponse({"code": 200, "msg": "操作成功", "data": None})

    original_get = task_service.requests.get
    original_post = task_service.requests.post
    original_record = ScoreTracker.record_score
    task_service.requests.get = fake_get
    task_service.requests.post = fake_post
    ScoreTracker.record_score = staticmethod(lambda **kwargs: None)
    try:
        result = TaskService.execute_weekly_lesson("token", 5, "测试用户")
    finally:
        task_service.requests.get = original_get
        task_service.requests.post = original_post
        ScoreTracker.record_score = original_record

    check("执行成功", result.get("success") is True, result)
    check(
        "提交到 progressReporter",
        captured.get("url", "").endswith("weeklyCourse/progressReporter"),
        captured.get("url"),
    )
    payloads = captured.get("payloads") or []
    # 平台按「本次观看增量」记账：单次 studyDuration 超过 120 秒的部分会被
    # 静默丢弃，必须按 120 秒步长累加上报（2026-10 平台新增校验）
    check("分步上报", len(payloads) == 6, [p.get("studyProgressTime") for p in payloads])
    check(
        "每步 studyDuration=120",
        all(p.get("studyDuration") == 120 for p in payloads),
        [p.get("studyDuration") for p in payloads],
    )
    check(
        "进度递增至总时长",
        [p.get("studyProgressTime") for p in payloads] == [120, 240, 360, 480, 600, 606],
        [p.get("studyProgressTime") for p in payloads],
    )
    last = payloads[-1] if payloads else {}
    # weeklyCourseId 缺失时平台返回 200 但不登记完成（2026-10 平台前端新增字段）
    check("含 weeklyCourseId", last.get("weeklyCourseId") == "w1", last)
    check("含 studyAssociationId", last.get("studyAssociationId") == "w1", last)
    check("含 version", last.get("version") == "pc-V2.0.1", last)
    check("studySchedule=100", last.get("studySchedule") == 100, last)


def test_daily_exam_submit_payload():
    print("\n[9] 每日一题交卷 payload（真实耗时）")
    from ccsa_auto.modules.task import service as task_service
    from ccsa_auto.modules.task.score_strategy import ScoreStrategy
    from ccsa_auto.modules.task.score_tracker import ScoreTracker

    captured = {"sleeps": []}

    def fake_get(url, headers=None, params=None, **kwargs):
        if url.endswith("getRegularStudyDay"):
            return _FakeResponse(
                {"code": 200, "data": {"id": "d1", "studyStatus": 1}}
            )
        if "regularStudyDayRuleSetting" in url:
            return _FakeResponse({"code": 200, "data": {"answeringTime": 30}})
        if url.endswith("getRegularStudyQuestionInfo"):
            return _FakeResponse(
                {
                    "code": 200,
                    "data": {
                        "id": "detail-1",
                        "questionTotalPoint": 20,
                        "examLimitTime": 30,
                        "questionList": [
                            {
                                "id": "q1",
                                "questionType": 1,
                                "questionPoint": 20,
                                "questionAnswera": '"B"',
                                "bankId": "b1",
                            }
                        ],
                    },
                }
            )
        raise AssertionError(f"unexpected url {url}")

    def fake_post(url, headers=None, data=None, **kwargs):
        captured["url"] = url
        captured["payload"] = json.loads(data)
        return _FakeResponse({"code": 200, "msg": "操作成功", "data": None})

    def fake_sleep(seconds):
        captured["sleeps"].append(seconds)

    original_get = task_service.requests.get
    original_post = task_service.requests.post
    original_sleep = task_service.time.sleep
    original_record = ScoreTracker.record_score
    original_enabled = ScoreStrategy.is_enabled_for
    task_service.requests.get = fake_get
    task_service.requests.post = fake_post
    task_service.time.sleep = fake_sleep
    ScoreTracker.record_score = staticmethod(lambda **kwargs: None)
    ScoreStrategy.is_enabled_for = staticmethod(lambda user_id: False)
    try:
        result = TaskService.execute_daily_question("token", 1, "测试用户")
    finally:
        task_service.requests.get = original_get
        task_service.requests.post = original_post
        task_service.time.sleep = original_sleep
        ScoreTracker.record_score = original_record
        ScoreStrategy.is_enabled_for = original_enabled

    check("执行成功", result.get("success") is True, result)
    payload = captured.get("payload") or {}
    # 2026-09-28 起平台按服务端真实耗时记账，必须等够时间再交卷
    check(
        "交卷前存在真实等待",
        len(captured["sleeps"]) == 1 and captured["sleeps"][0] > 0,
        captured["sleeps"],
    )
    # examDuration 与前端一致，取自规则接口 answeringTime
    check("examDuration=30", payload.get("examDuration") == 30, payload)
    # 前端为 examDetailId = id ?? examDetailId，这里验证回退
    check("examDetailId 回退到 id", payload.get("examDetailId") == "detail-1", payload)
    # useTime 反映真实耗时，不再出现 0 / -1
    check(
        "useTime 在 120-300 秒",
        120 <= payload.get("useTime", 0) <= 300,
        payload.get("useTime"),
    )


def main():
    print("=" * 60)
    print("第三方平台 v2 接口适配验证")
    print("=" * 60)
    test_aes_roundtrip()
    test_rsa_and_payload()
    test_login_request()
    test_answer_normalization()
    test_build_questions()
    test_endpoint_map()
    test_task_status_parsing()
    test_weekly_submit_payload()
    test_daily_exam_submit_payload()
    print("\n" + "=" * 60)
    print(f"全部通过：{_passed} 项检查")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print(exc)
        sys.exit(1)
