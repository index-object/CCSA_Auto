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
    print("\n" + "=" * 60)
    print(f"全部通过：{_passed} 项检查")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print(exc)
        sys.exit(1)
