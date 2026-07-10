"""
采集答题记录中的正确答案到 question_bank 表。

流程：
  1. 从数据库读取最多 ACCOUNT_LIMIT 个有外部账号的用户
  2. 逐个登录外部平台，分页查询 examType={1|2} 的答题记录
  3. 逐个获取答题详情，提取每道题的正确答案
  4. 存入本地 question_bank 表（自动去重）

用法：
  uv run python -m scripts.seed_question_bank       # 采集每日一题 (examType=1)
  uv run python -m scripts.seed_question_bank 2     # 采集每月一考 (examType=2)
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from sqlalchemy import func

from ccsa_auto.core.config import Config
from ccsa_auto.core.database import SessionLocal, engine, Base
from ccsa_auto.core.models import QuestionBank, User
from ccsa_auto.modules.auth.service import AuthService

# 多账号采集（只读查询，不消耗每日答题）
ACCOUNT_LIMIT = 10


def get_accounts_from_db():
    db = SessionLocal()
    try:
        users = (
            db.query(User)
            .filter(
                User.external_username != None,
                User.external_password != None,
                User.external_username != "",
                User.external_password != "",
            )
            .limit(ACCOUNT_LIMIT)
            .all()
        )
        return [{"username": u.external_username, "password": u.external_password} for u in users]
    finally:
        db.close()

EXAM_TYPE = int(sys.argv[1]) if len(sys.argv) > 1 else 1  # 1=每日一题, 2=每月一考
EXAM_LABEL = {1: "每日一题", 2: "每月一考"}.get(EXAM_TYPE, f"examType={EXAM_TYPE}")
TOTAL_PAGES = {1: 5, 2: 5}.get(EXAM_TYPE, 5)  # 各取5页
PAGE_SIZE = 10


def ensure_table():
    Base.metadata.create_all(bind=engine)
    print("[OK] 表已就绪")


def login(account):
    result = AuthService.authenticate_external(account["username"], account["password"])
    if not result[0]:
        print(f"[WARN] 登录失败 {account['username']}: {result[1]}")
        return None
    token = result[2]
    print(f"[OK] {account['username']} 登录成功")
    return token


def fetch_record_ids(token):
    ids = []
    headers = {"Authorization": f"Bearer {token}", **Config.EXTERNAL_PLATFORM["HEADERS"]}
    list_url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"]["GET_EXAM_RECORDS"]

    for page in range(1, TOTAL_PAGES + 1):
        resp = requests.get(
            list_url,
            params={"examType": EXAM_TYPE, "pageNum": page, "pageSize": PAGE_SIZE},
            headers=headers,
        )
        data = resp.json()
        rows = data.get("rows", [])
        for r in rows:
            ids.append((r["id"], r.get("answerPoint", 0)))
        print(f"  第{page}页: {len(rows)}条 (累计{len(ids)}条)")
        time.sleep(0.5)

    print(f"[OK] 共获取 {len(ids)} 条记录 ID")
    return ids


def fetch_and_save_questions(token, record_id, api_headers):
    """获取单条记录的题目详情并入库"""
    detail_url = Config.EXTERNAL_PLATFORM["API_ENDPOINTS"]["GET_EXAM_DETAIL"]
    url = f"{detail_url}/{record_id}/1"

    resp = requests.get(url, headers=api_headers)
    data = resp.json()
    if data.get("code") != 200:
        print(f"    [SKIP] 记录 {record_id} 查询失败: {data.get('msg')}")
        return 0

    vo_list = data.get("data", {}).get("answerDetailVoList", {})
    questions = vo_list.get("appResourcesQuestions", [])
    if not questions:
        print(f"    [SKIP] 记录 {record_id} 无题目详情")
        return 0

    db = SessionLocal()
    try:
        saved = 0
        for q in questions:
            qid = q.get("id")
            qtype = q.get("questionType")
            answer = q.get("questionAnswera")
            point = q.get("questionPoint", 2)
            title = q.get("questionTitle", "")
            options = q.get("questionOptions", "")

            if not qid or not answer:
                continue

            existing = db.query(QuestionBank).filter_by(question_id=qid).first()
            if existing:
                continue

            row = QuestionBank(
                question_id=qid,
                question_type=qtype,
                question_point=point,
                question_answer=answer,
                question_title=title,
                question_options=options,
                source_record_id=record_id,
                source_exam_type=EXAM_TYPE,
            )
            db.add(row)
            saved += 1

        db.commit()
        print(f"    [OK] 记录 {record_id} 新增 {saved} 题")
        return saved
    except Exception as e:
        db.rollback()
        print(f"    [ERR] 记录 {record_id} 入库失败: {e}")
        return 0
    finally:
        db.close()


def main():
    ensure_table()

    accounts = get_accounts_from_db()
    print(f"[OK] 从数据库读取 {len(accounts)} 个账号\n")

    total_saved = 0
    total_records = 0

    for account in accounts:
        token = login(account)
        if not token:
            continue

        api_headers = {"Authorization": f"Bearer {token}", **Config.EXTERNAL_PLATFORM["HEADERS"]}
        records = fetch_record_ids(token)
        if not records:
            print(f"  [SKIP] {account['username']} 无记录")
            continue

        for i, (rid, score) in enumerate(records, 1):
            n = fetch_and_save_questions(token, rid, api_headers)
            total_saved += n
            print(f"  进度: {i}/{len(records)}  {account['username']}")
            time.sleep(0.3)

        total_records += len(records)
        print(f"  [DONE] {account['username']} 完成\n")

    db = SessionLocal()
    try:
        by_type = db.query(QuestionBank.question_type, func.count(QuestionBank.id)).group_by(QuestionBank.question_type).all()
    finally:
        db.close()

    print(f"\n=== 采集完成 ===")
    print(f"  处理账号: {len(accounts)} 个")
    print(f"  处理记录: {total_records} 条")
    print(f"  新增题目: {total_saved} 题")
    print(f"  按类型分布:")
    for t, cnt in sorted(by_type):
        label = {1: "单选", 2: "多选", 3: "判断"}.get(t, f"未知({t})")
        print(f"    类型 {t}({label}): {cnt} 题")


if __name__ == "__main__":
    main()
