import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from bs4 import Comment

# 경로 상수
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEXT_FILE = os.path.join(BASE_DIR, "english_lines.txt")
INDEX_FILE = os.path.join(BASE_DIR, "index.html")
MENU_FILE = os.path.join(BASE_DIR, "menu.html")
POSTS_DIR = os.path.join(BASE_DIR, "posts")

# 오늘과 어제 날짜 계산 (기준: KST)
now = datetime.utcnow() + timedelta(hours=9)
yesterday = now - timedelta(days=1)

# 날짜 포맷
TODAY = now.strftime("%Y-%m-%d")
YESTERDAY = yesterday.strftime("%Y-%m-%d")
POST_YEAR = yesterday.strftime("%Y")
POST_MONTH = yesterday.strftime("%m")
POST_DAY = yesterday.strftime("%d")
POST_FOLDER = os.path.join(POSTS_DIR, POST_YEAR, POST_MONTH)
POST_PATH = os.path.join(POST_FOLDER, f"{YESTERDAY}.html")

# 문장 10세트(3줄 + 빈줄 × 10개) 추출 함수
def get_10_unique_entries():
    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        raw = f.read()

    raw_blocks = raw.strip().split("\n\n")
    blocks = []
    for block in raw_blocks:
        lines = block.splitlines()
        if len(lines) == 3:
            blocks.append(lines)

    if len(blocks) < 10:
        print(f"❌ 유효한 문장 블록이 10개 미만입니다. 현재 {len(blocks)}개입니다.")
        return []

    selected = blocks[:10]
    remaining = blocks[10:]

    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        for block in remaining:
            f.write("\n".join(block) + "\n\n")

    return selected

# menu.html 생성
# (이하 기존 코드와 동일 - 생략)
# ...

if __name__ == "__main__":
    entries = get_10_unique_entries()
    if len(entries) < 10:
        print("Not enough unique entries found.")
    else:
        backup_index()
        generate_new_index(entries)
        generate_menu_html()
