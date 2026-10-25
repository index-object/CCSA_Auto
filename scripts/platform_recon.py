"""第三方平台浏览器侦察：登录后注入 token，用真实浏览器录全部接口流量。

平台（https://edu.axdxa.cn）是 Vite SPA，接口契约会随前端发版变化。
排查「本地执行成功但平台没记录」时，用真实浏览器跑一遍、对比请求体最可靠。

依赖 Playwright（不进项目依赖，按需安装）：
    uv pip install playwright

用法（在仓库根目录执行）：
    uv run python -m scripts.platform_recon <账号> <密码>
    uv run python -m scripts.platform_recon <账号> <密码> --play          # 打开本周周课并播放
    uv run python -m scripts.platform_recon <账号> <密码> --url <URL> --seconds 60 --headless
    uv run python -m scripts.platform_recon <账号> <密码> --play --out events.json
"""

import argparse
import json
import time

import requests

from ccsa_auto.core.config import Config
from ccsa_auto.utils.crypto import encrypt_payload

EP = Config.EXTERNAL_PLATFORM
BASE = "https://edu.axdxa.cn"
IDENTITY_KEYS = ("getRegularStudyWeek", "regularCourseWeek", "progressReporter", "PlayAuth")


def api_login(username, password):
    payload = {
        "username": username,
        "password": password,
        "clientId": EP["LOGIN_CLIENT_ID"],
        "grantType": EP["LOGIN_GRANT_TYPE"],
    }
    body, encrypt_key = encrypt_payload(payload)
    headers = dict(EP["HEADERS"])
    headers["encrypt-key"] = encrypt_key
    headers["isencrypt"] = "true"
    resp = requests.post(EP["LOGIN_URL"], data=json.dumps(body), headers=headers, timeout=20).json()
    token = (resp.get("data") or {}).get("access_token")
    if not token:
        raise SystemExit(f"登录失败: {resp.get('msg')}")
    return token


def current_week_id(token):
    headers = dict(EP["HEADERS"])
    headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(EP["API_ENDPOINTS"]["GET_REGULAR_STUDY_WEEK"], headers=headers, timeout=20).json()
    week = resp.get("data") or {}
    if not week.get("id"):
        raise SystemExit(f"未取到本周周课: {resp.get('msg')}")
    print(f"本周周课 id={week['id']} 时长={week.get('resourceDuration')} "
          f"状态={week.get('studyStatus')} 进度={week.get('studySchedule')}")
    return week["id"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("username")
    ap.add_argument("password")
    ap.add_argument("--url", default=f"{BASE}/user/learnCenter")
    ap.add_argument("--play", action="store_true", help="打开本周周课页并播放视频")
    ap.add_argument("--seconds", type=int, default=30)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--out", default="", help="把完整流量写入 JSON")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    token = api_login(args.username, args.password)
    url = f"{BASE}/weekClass/home?id={current_week_id(token)}" if args.play else args.url

    events = []
    t0 = time.time()

    def stamp():
        return round(time.time() - t0, 2)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=args.headless,
            args=["--autoplay-policy=no-user-gesture-required", "--mute-audio"],
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        context.add_init_script(
            "try{localStorage.setItem('Admin-Token', %s);}catch(e){}" % json.dumps(token)
        )
        page = context.new_page()

        page.on("request", lambda req: events.append({
            "t": stamp(), "kind": "req", "type": req.resource_type,
            "method": req.method, "url": req.url, "body": req.post_data,
        }) if req.resource_type in ("xhr", "fetch", "media") else None)

        def on_response(resp):
            if resp.request.resource_type not in ("xhr", "fetch"):
                return
            try:
                body = resp.text()
            except Exception as exc:
                body = f"<unreadable: {exc}>"
            events.append({"t": stamp(), "kind": "resp", "status": resp.status,
                           "url": resp.url, "body": body[:2000]})

        page.on("response", on_response)
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)

        if args.play:
            for selector in (".prism-big-play-btn", "video"):
                try:
                    page.locator(selector).first.click(timeout=2000)
                    break
                except Exception:
                    continue
            page.evaluate("() => { const v=document.querySelector('video'); if(v){v.muted=true;v.play().catch(()=>{});} }")

        page.wait_for_timeout(max(args.seconds - 6, 1) * 1000)
        video = page.evaluate(
            "() => { const v=document.querySelector('video');"
            " return v ? {time: Math.round(v.currentTime), duration: Math.round(v.duration), paused: v.paused} : null; }"
        )
        page.close()
        context.close()
        browser.close()

    print(f"页面: {url}")
    if video:
        print(f"视频: {video}")
    print("=== 流量 ===")
    for event in events:
        if event["kind"] == "resp":
            continue
        print(f'[{event["t"]:>6.2f}] {event["method"]} {event["url"]}')
        if event.get("body"):
            print(f'         {event["body"][:500]}')
        for resp in events:
            if resp["kind"] == "resp" and resp["url"] == event["url"]:
                print(f'    <- {resp["status"]} {resp["body"][:500]}')
                break

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=1)
        print(f"已写入 {args.out}")


if __name__ == "__main__":
    main()
