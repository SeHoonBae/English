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

# 문장 10세트(3줄 + 빈줄 포함된 블록 × 10개) 추출 함수
def get_10_unique_entries():
    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    raw_blocks = content.strip().split("\n\n")
    blocks = []
    for block in raw_blocks:
        lines = block.strip().splitlines()
        if len(lines) >= 3:
            blocks.append(lines[:3])

    if len(blocks) < 10:
        print(f"❌ 유효한 문장 블록이 10개 미만입니다. 현재 {len(blocks)}개입니다.")
        return []

    selected = blocks[:10]
    remaining_blocks = raw_blocks[10:]

    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        for block in remaining_blocks:
            f.write(block.strip() + "\n\n")

    return selected

# index.html 백업

def backup_index():
    if not os.path.exists(INDEX_FILE):
        print("index.html not found!")
        return

    os.makedirs(POST_FOLDER, exist_ok=True)

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("href=\"assets/", "href=\"/assets/")
    html = html.replace("src=\"assets/", "src=\"/assets/")

    soup = BeautifulSoup(html, "html.parser")
    menu_include = soup.new_tag("div", id="sidebar")
    inner_div = soup.new_tag("div", **{"class": "inner"})
    comment = soup.new_string("#include virtual=\"/menu.html\" ", Comment)
    inner_div.append(comment)
    menu_include.append(inner_div)

    sidebar_div = soup.find("div", id="sidebar")
    if sidebar_div:
        sidebar_div.replace_with(menu_include)

    with open(POST_PATH, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f"✅ index.html 백업 완료: {POST_PATH}")

# index.html 갱신

def generate_new_index(entries):
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    main_inner = soup.select_one("div#main > div.inner")
    if not main_inner:
        print("Cannot find main > inner block")
        return

    banner = main_inner.find("section", id="banner")
    if banner:
        for sibling in list(banner.find_next_siblings("section")):
            sibling.decompose()

    for i, entry in enumerate(entries):
        block = BeautifulSoup(f'''
<section>
  <div class="features">
    <article>
      <div class="content">
        <h2>{i+1}. {entry[0]}</h2>
        <h2>{entry[1]}</h2>
        <h3>{entry[2]}</h3>
      </div>
    </article>
  </div>
</section>
''', "html.parser")
        main_inner.append(block)

    sidebar_div = soup.find("div", id="sidebar")
    if sidebar_div:
        new_sidebar = BeautifulSoup('<div id="sidebar"><div class="inner"><!--#include virtual="/menu.html" --></div></div>', "html.parser")
        sidebar_div.replace_with(new_sidebar)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(str(soup.prettify(formatter="html")))

    print("✅ index.html 업데이트 완료")

# menu.html 생성 (전체 자동 탐색 방식으로 교체)
def generate_menu_html():
    from bs4 import BeautifulSoup

    nav = BeautifulSoup(features="html.parser").new_tag("nav", id="menu")
    header = BeautifulSoup(features="html.parser").new_tag("header", **{"class": "major"})
    h2 = BeautifulSoup(features="html.parser").new_tag("h2")
    h2.string = "Menu"
    header.append(h2)
    nav.append(header)
    root_ul = BeautifulSoup(features="html.parser").new_tag("ul")

    home_li = BeautifulSoup(features="html.parser").new_tag("li")
    home_a = BeautifulSoup(features="html.parser").new_tag("a", href="/index.html")
    home_a.string = "Homepage"
    home_li.append(home_a)
    root_ul.append(home_li)

    if not os.path.exists(POSTS_DIR):
        print("No posts directory found.")
        return

    for year in sorted(os.listdir(POSTS_DIR)):
        year_path = os.path.join(POSTS_DIR, year)
        if not os.path.isdir(year_path):
            continue

        year_li = BeautifulSoup(features="html.parser").new_tag("li")
        year_span = BeautifulSoup(features="html.parser").new_tag("span", **{"class": "opener"})
        year_span.string = f"{year}년 모음"
        year_ul = BeautifulSoup(features="html.parser").new_tag("ul")

        for month in sorted(os.listdir(year_path)):
            month_path = os.path.join(year_path, month)
            if not os.path.isdir(month_path):
                continue

            month_li = BeautifulSoup(features="html.parser").new_tag("li")
            month_span = BeautifulSoup(features="html.parser").new_tag("span", **{"class": "opener"})
            month_span.string = f"{int(month):02d}월 모음"
            month_ul = BeautifulSoup(features="html.parser").new_tag("ul")

            for file in sorted(os.listdir(month_path)):
                if file.endswith(".html"):
                    day = file.split(".")[0].split("-")[-1]
                    file_li = BeautifulSoup(features="html.parser").new_tag("li")
                    file_a = BeautifulSoup(features="html.parser").new_tag("a", href=f"/posts/{year}/{month}/{file}")
                    file_a.string = f"{month}월 {day}일 영어문장 10개"
                    file_li.append(file_a)
                    month_ul.append(file_li)

            if month_ul.contents:
                month_li.append(month_span)
                month_li.append(month_ul)
                year_ul.append(month_li)

        if year_ul.contents:
            year_li.append(year_span)
            year_li.append(year_ul)
            root_ul.append(year_li)

    nav.append(root_ul)

    with open(MENU_FILE, "w", encoding="utf-8") as f:
        f.write(str(nav))

    print("✅ menu.html 갱신 완료")

if __name__ == "__main__":
    entries = get_10_unique_entries()
    if len(entries) < 10:
        print("Not enough unique entries found.")
    else:
        backup_index()
        generate_new_index(entries)
        generate_menu_html()
