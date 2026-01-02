import time
import requests
import pandas as pd

API_URL = "https://web-drcn.hispace.dbankcloud.com/edge/index/commentlist3"

APP_ID = "C112973233"     # Deepseek
SLEEP = 0.5              # 请求间隔，别太快

MAX_COMMENTS = 1000      # 最多抓多少条评论（人为上限）
MAX_PAGES = 300          # 最多请求多少次接口（兜底）

# 这是你抓到的真实参数：maxResults + reqPageNum
MAX_RESULTS = 25         # 每页多少条（你抓到的是 25；有些场景可试 50，但先按抓到的来）

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://appgallery.huawei.com",
    "Referer": "https://appgallery.huawei.com/",
}

def fetch_all_comments():
    all_rows = []
    page_count = 0
    reqPageNum = 1  # ✅ 翻页：从第 1 页开始

    totalPages = None  # 从接口返回里读取（例如 40）

    # ✅ 去重：避免接口偶尔重复返回
    seen = set()

    while True:
        page_count += 1

        if page_count > MAX_PAGES:
            print("达到最大请求次数，停止")
            break

        payload = {
            # ✅ 你抓到的真实 Form Data
            "method": "internal.user.commenList3",
            "serviceType": 20,
            "reqPageNum": reqPageNum,
            "maxResults": MAX_RESULTS,
            "appid": APP_ID,
            "locale": "zh",       # 你抓到的是 zh（不是 zh_CN）
            "version": "10.0.0",
            "zone": ""
        }

        print(f"REQ page={reqPageNum} maxResults={MAX_RESULTS}")

        resp = requests.post(
            API_URL,
            headers=HEADERS,
            data=payload,
            timeout=10
        )

        print("HTTP status:", resp.status_code)
        resp.raise_for_status()
        data = resp.json()

        # 从返回里取总页数/总数（如果有）
        if totalPages is None:
            totalPages = data.get("totalPages")
            count = data.get("count")
            print("totalPages:", totalPages, "count:", count)

        comments = data.get("list")
        if not comments:
            print("没有更多评论，停止")
            break

        added_this_page = 0
        for c in comments:
            comment_id = c.get("id") or c.get("commentId")
            user = c.get("accountName") or c.get("nickName")
            rating = int(c.get("rating")) if c.get("rating") is not None else None
            content = c.get("commentInfo")
            oper_time = c.get("operTime")

            # 去重 key（更稳）
            key = (comment_id or "", oper_time or "", content or "")
            if key in seen:
                continue
            seen.add(key)

            all_rows.append({
                "id": comment_id,
                "user": user,
                "rating": rating,
                "content": content,
                "time": oper_time,
                "phone": c.get("phone"),
                "versionName": c.get("versionName"),
                "approveCounts": c.get("approveCounts"),
            })
            added_this_page += 1

            if len(all_rows) >= MAX_COMMENTS:
                print(f"达到最大评论数 {MAX_COMMENTS}，停止")
                return all_rows

        print(f"本页新增 {added_this_page} 条，累计 {len(all_rows)} 条")

        # ✅ 如果接口告诉你总页数，到最后一页就停（更稳）
        if totalPages is not None and reqPageNum >= int(totalPages):
            print("到达最后一页，停止")
            break

        # 下一页
        reqPageNum += 1
        time.sleep(SLEEP)

    return all_rows


if __name__ == "__main__":
    rows = fetch_all_comments()
    df = pd.DataFrame(rows)
    df.to_csv("huawei_comments_api.csv", index=False, encoding="utf-8-sig")
    print("✅ 完成，总评论数：", len(df))
