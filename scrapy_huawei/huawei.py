import time
import requests
import pandas as pd

API_URL = "https://web-drcn.hispace.dbankcloud.com/edge/index/commentlist3"

APP_ID = "C112973233"     # Deepseek
LIMIT = 50              # 每次请求条数
SLEEP = 0.5             # 请求间隔，别太快

MAX_COMMENTS = 1000    # ⭐ 新增：最多抓多少条评论（人为上限）
MAX_PAGES = 300         # ⭐ 新增：最多请求多少次接口（兜底）

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
    offset = 0
    page_count = 0        # ⭐ 新增：请求计数

    while True:
        page_count += 1   # ⭐ 新增

        # ⭐ 新增：请求次数上限
        if page_count > MAX_PAGES:
            print("达到最大请求次数，停止")
            break

        payload = {
            "appid": APP_ID,
            "offset": offset,
            "limit": LIMIT,
            "orderType": 0,      # 0 = 最新
            "locale": "zh_CN"
        }

        resp = requests.post(
            API_URL,
            headers=HEADERS,
            data=payload,
            timeout=10
        )

        print("HTTP status:", resp.status_code)
        resp.raise_for_status()
        data = resp.json()

        comments = data.get("list")
        if comments is None:
            comments = data.get("data", {}).get("list")

        
        # ⭐⭐ 就加在这里
        #print("DEBUG sample comment:", comments[0])

        # 原有结束条件：接口没数据
        if not comments:
            print("没有更多评论，停止")
            break
        
        for c in comments:
            all_rows.append({
                "user": c.get("accountName") or c.get("nickName"),
                "rating": int(c.get("rating")) if c.get("rating") is not None else None,
                "content": c.get("commentInfo"),
                "time": c.get("operTime")
            })


            # ⭐ 新增：评论数上限
            if len(all_rows) >= MAX_COMMENTS:
                print(f"达到最大评论数 {MAX_COMMENTS}，停止")
                return all_rows

        offset += len(comments)
        print(f"已抓取 {len(all_rows)} 条评论")

        time.sleep(SLEEP)

    return all_rows


if __name__ == "__main__":
    rows = fetch_all_comments()
    df = pd.DataFrame(rows)
    df.to_csv("huawei_comments_api.csv", index=False, encoding="utf-8-sig")
    print("✅ 完成，总评论数：", len(df))
