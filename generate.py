import os
import shutil
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 경로 상수
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEXT_FILE = os.path.join(BASE_DIR, "english_lines.txt")
INDEX_FILE = os.path.join(BASE_DIR, "index.html")
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

# 문장 10세트(4줄 × 10개) 추출 함수
def get_10_unique_entries():
    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    entries = [lines[i:i+4] for i in range(0, len(lines), 4)]
    new_entries = []
    used_set = set()

    for entry in entries:
        key = tuple(entry)
        if key not in used_set:
            new_entries.append(entry)
            used_set.add(key)
        if len(new_entries) == 10:
            break

    if len(new_entries) < 10:
        return []

    # 남은 문장만 다시 파일에 기록
    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        for entry in entries[len(new_entries):]:
            f.write('\n'.join(entry) + '\n\n')

    return new_entries

# index.html 백업 함수
def backup_index():
    if not os.path.exists(INDEX_FILE):
        print("index.html not found!")
        return
    os.makedirs(POST_FOLDER, exist_ok=True)
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("href=\"assets/", "href=\"../../../../assets/")
    html = html.replace("src=\"assets/", "src=\"../../../../assets/")

    with open(POST_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Backed up index.html to {POST_PATH}")

# 새로운 섹션 블록 HTML 생성
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

# nav 메뉴 업데이트
def update_sidebar(nav_html):
    soup = BeautifulSoup(nav_html, "html.parser")
    root_ul = soup.find("ul")
    if not root_ul:
        return nav_html

    year_str = f"{POST_YEAR}년 모음"
    month_str = f"{POST_MONTH}월 모음"
    link_text = f"{POST_MONTH}월 {POST_DAY}일 영어문장 10개"
    href_val = f"/English/posts/{POST_YEAR}/{POST_MONTH}/{YESTERDAY}.html"

    year_li = None
    for li in root_ul.find_all("li", recursive=False):
        if li.find("span", string=year_str):
            year_li = li
            break

    if not year_li:
        year_li = soup.new_tag("li")
        year_span = soup.new_tag("span", **{"class": "opener"})
        year_span.string = year_str
        year_ul = soup.new_tag("ul")
        year_li.append(year_span)
        year_li.append(year_ul)
        root_ul.append(year_li)
    else:
        year_ul = year_li.find("ul")

    month_li = None
    for li in year_ul.find_all("li", recursive=False):
        if li.find("span", string=month_str):
            month_li = li
            break

    if not month_li:
        month_li = soup.new_tag("li")
        month_span = soup.new_tag("span", **{"class": "opener"})
        month_span.string = month_str
        month_ul = soup.new_tag("ul")
        month_li.append(month_span)
        month_li.append(month_ul)
        year_ul.append(month_li)
    else:
        month_ul = month_li.find("ul")

    if not any(a for a in month_ul.find_all("a") if a.get("href") == href_val):
        new_li = soup.new_tag("li")
        new_a = soup.new_tag("a", href=href_val)
        new_a.string = link_text
        new_li.append(new_a)
        month_ul.append(new_li)

    return str(soup.find("nav", id="menu"))

# index.html 생성
def generate_new_index(entries):
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    # nav 메뉴 먼저 추출 및 교체
    nav_pattern = re.compile(r'(<nav id="menu">.*?</nav>)', re.DOTALL)
    nav_match = nav_pattern.search(html)
    updated_nav = nav_match.group(1)
    if nav_match:
        updated_nav = update_sidebar(nav_match.group(1))
        html = html.replace(nav_match.group(1), updated_nav)

    # section 삽입 (main > inner 내에서만)
    inner_start = html.find('<div id="main">')
    sidebar_start = html.find('<div id="sidebar">')
    if inner_start == -1 or sidebar_start == -1:
        print("Could not locate main/sidebar blocks.")
        return

    main_html = html[inner_start:sidebar_start]
    main_clean = re.sub(r'<section>.*?</section>', '', main_html, flags=re.DOTALL)
    new_sections = build_sections(entries)
    updated_main = main_clean + new_sections

    updated_html = html[:inner_start] + updated_main + html[sidebar_start:]

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(updated_html)

    print("New index.html created with updated <section> blocks and sidebar menu.")

if __name__ == "__main__":
    entries = get_10_unique_entries()
    if len(entries) < 10:
        print("Not enough unique entries found.")
    else:
        backup_index()
        generate_new_index(entries)
