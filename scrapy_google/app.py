from google_play_scraper import Sort, reviews
import pandas as pd
import time

APP_ID = "com.larus.wolf"  # ← 换成你要的应用包名

all_reviews = []
token = None

for i in range(5):  # 先抓 5 批（最多 ~1000 条）
    batch, token = reviews(
        APP_ID,
        lang="zh",
        country="tw",
        sort=Sort.NEWEST,
        count=200,
        continuation_token=token
    )

    if not batch:
        break

    all_reviews.extend(batch)
    print(f"batch {i+1}: got {len(batch)}, total {len(all_reviews)}")

    if token is None:
        break

    time.sleep(1.5)  # 限速，防封

df = pd.DataFrame(all_reviews)

cols = [
    "reviewId",
    "userName",
    "score",
    "at",
    "content",
    "thumbsUpCount",
    "replyContent",
    "repliedAt",
    "appVersion"
]

for c in cols:
    if c not in df.columns:
        df[c] = None

out_file = f"{APP_ID}_reviews.csv"
df[cols].to_csv(out_file, index=False, encoding="utf-8-sig")

print("✅ 保存成功：", out_file)
