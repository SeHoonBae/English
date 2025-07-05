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

# 날짜 처리
now = datetime.utcnow() + timedelta(hours=9)
yesterday = now - timedelta(days=1)

TODAY = now.strftime("%Y-%m-%d")
YESTERDAY = yesterday.strftime("%Y-%m-%d")
POST_YEAR = yesterday.strftime("%Y")
POST_MONTH = yesterday.strftime("%m")
POST_DAY = yesterday.strftime("%d")
POST_FOLDER = os.path.join(POSTS_DIR, POST_YEAR, POST_MONTH)
POST_PATH = os.path.join(POST_FOLDER, f"{YESTERDAY}.html")

# 문장 10세트(4줄) 추출
def get_10_unique_entries():
    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        blocks = [b.strip().splitlines() for b in f.read().strip().split("\n\n")]

    entries = [b for b in blocks if len(b) == 4]
    if len(entries) < 10:
        return []

    selected = entries[:10]
    remaining = entries[10:]

    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        for entry in remaining:
            f.write("\n".join(entry) + "\n\n")

    return selected

# menu.html 생성
def generate_menu_html():
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()
    nav_pattern = re.compile(r'(<nav id="menu">.*?</nav>)', re.DOTALL)
    nav_match = nav_pattern.search(html)
    if nav_match:
        updated_nav = update_sidebar(nav_match.group(1))
        with open(MENU_FILE, "w", encoding="utf-8") as f:
            f.write(updated_nav)
        print("✅ menu.html 생성 완료")

# 백업 index → posts/YYYY/MM/YYYY-MM-DD.html
def backup_index():
    if not os.path.exists(INDEX_FILE):
        print("⚠️ index.html 없음")
        return

    os.makedirs(POST_FOLDER, exist_ok=True)

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("href=\"assets/", "href=\"/assets/")
    html = html.replace("src=\"assets/", "src=\"/assets/")

    soup = BeautifulSoup(html, "html.parser")

    # 메뉴 include로 교체
    sidebar_div = soup.find("div", id="sidebar")
    if sidebar_div:
        new_sidebar = BeautifulSoup(
            '<div id="sidebar"><div class="inner"><!--#include virtual="/menu.html" --></div></div>',
            "html.parser"
        )
        sidebar_div.replace_with(new_sidebar)

    with open(POST_PATH, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f"✅ index 백업 생성: {POST_PATH}")

# section 생성
def build_sections(entries):
    blocks = []
    for i, entry in enumerate(entries):
        blocks.append(f'''
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
</section>''')
    return '\n'.join(blocks)

# sidebar nav 갱신
def update_sidebar(nav_html):
    soup = BeautifulSoup(nav_html, "html.parser")
    root_ul = soup.find("ul")
    if not root_ul:
        return nav_html

    year_str = f"{POST_YEAR}년 모음"
    month_str = f"{POST_MONTH}월 모음"
    link_text = f"{POST_MONTH}월 {POST_DAY}일 영어문장 10개"
    href_val = f"/posts/{POST_YEAR}/{POST_MONTH}/{YESTERDAY}.html"

    def find_li(ul, text):
        for li in ul.find_all("li", recursive=False):
            span = li.find("span", class_="opener")
            if span and span.text.strip() == text:
                return li
        return None

    year_li = find_li(root_ul, year_str)
    if not year_li:
        year_li = soup.new_tag("li")
        span = soup.new_tag("span", **{"class": "opener"})
        span.string = year_str
        sub_ul = soup.new_tag("ul")
        year_li.append(span)
        year_li.append(sub_ul)
        root_ul.append(year_li)
    else:
        sub_ul = year_li.find("ul")

    month_li = find_li(sub_ul, month_str)
    if not month_li:
        month_li = soup.new_tag("li")
        span = soup.new_tag("span", **{"class": "opener"})
        span.string = month_str
        month_ul = soup.new_tag("ul")
        month_li.append(span)
        month_li.append(month_ul)
        sub_ul.append(month_li)
    else:
        month_ul = month_li.find("ul")

    if not any(a.get("href") == href_val for a in month_ul.find_all("a")):
        new_li = soup.new_tag("li")
        new_a = soup.new_tag("a", href=href_val)
        new_a.string = link_text
        new_li.append(new_a)
        month_ul.append(new_li)

    return str(soup.find("nav", id="menu"))

# index.html 갱신
def generate_new_index(entries):
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    nav_match = re.search(r'(<nav id="menu">.*?</nav>)', html, re.DOTALL)
    if nav_match:
        updated_nav = update_sidebar(nav_match.group(1))
        html = html.replace(nav_match.group(1), updated_nav)

    soup = BeautifulSoup(html, "html.parser")
    main_inner = soup.select_one("div#main > div.inner")
    if not main_inner:
        print("❌ main.inner 찾기 실패")
        return

    banner = main_inner.find("section", id="banner")
    if banner:
        for sibling in list(banner.find_next_siblings("section")):
            sibling.decompose()

    new_html = build_sections(entries)
    new_soup = BeautifulSoup(new_html, "html.parser")
    for section in new_soup.find_all("section"):
        main_inner.append(section)

    sidebar_div = soup.find("div", id="sidebar")
    if sidebar_div:
        new_sidebar = BeautifulSoup(
            '<div id="sidebar"><div class="inner"><!--#include virtual="/menu.html" --></div></div>',
            "html.parser"
        )
        sidebar_div.replace_with(new_sidebar)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(str(soup.prettify(formatter="html")))

    print("✅ index.html 갱신 완료")

# 실행
if __name__ == "__main__":
    entries = get_10_unique_entries()
    if len(entries) < 10:
        print("⚠️ 문장이 10세트 미만입니다.")
    else:
        generate_new_index(entries)   # 먼저 index 갱신
        backup_index()               # 이후 백업 파일 생성
        generate_menu_html()        # 마지막에 메뉴 따로 생성
