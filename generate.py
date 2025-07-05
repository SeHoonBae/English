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

# 문장 10세트(4줄 × 10개) 추출 함수
def get_10_unique_entries():
    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        raw_text = f.read()

    blocks = [block.strip().splitlines() for block in raw_text.strip().split("\n\n")]
    entries = [block for block in blocks if len(block) == 4]
    new_entries = entries[:10]

    if len(new_entries) < 10:
        return []

    remaining_entries = entries[10:]

    # 다시 파일에 저장
    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        for entry in remaining_entries:
            f.write("\n".join(entry) + "\n\n")

    return new_entries


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
        print("Generated separate menu.html file.")

# 백업 파일 생성
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

    print(f"Backed up index.html to {POST_PATH}")

# 새 섹션 블록 생성
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

# 메뉴 업데이트
def update_sidebar(nav_html):
    soup = BeautifulSoup(nav_html, "html.parser")
    root_ul = soup.find("ul")
    if not root_ul:
        return nav_html

    year_str = f"{POST_YEAR}년 모음"
    month_str = f"{POST_MONTH}월 모음"
    link_text = f"{POST_MONTH}월 {POST_DAY}일 영어문장 10개"
    href_val = f"/posts/{POST_YEAR}/{POST_MONTH}/{YESTERDAY}.html"

    def find_existing_li(ul_tag, target_text):
        for li in ul_tag.find_all("li", recursive=False):
            span = li.find("span", class_="opener")
            if span and span.text.strip() == target_text:
                return li
        return None

    year_li = find_existing_li(root_ul, year_str)
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

    month_li = find_existing_li(year_ul, month_str)
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

    if not any(a.get("href") == href_val for a in month_ul.find_all("a")):
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

    nav_pattern = re.compile(r'(<nav id="menu">.*?</nav>)', re.DOTALL)
    nav_match = nav_pattern.search(html)
    if nav_match:
        updated_nav = update_sidebar(nav_match.group(1))
        html = html.replace(nav_match.group(1), updated_nav)

    soup = BeautifulSoup(html, "html.parser")
    main_inner = soup.select_one("div#main > div.inner")
    if not main_inner:
        print("Cannot find main > inner block")
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
        new_sidebar = BeautifulSoup('<div id="sidebar"><div class="inner"><!--#include virtual="/menu.html" --></div></div>', "html.parser")
        sidebar_div.replace_with(new_sidebar)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(str(soup.prettify(formatter="html")))

    print("New index.html created with updated <section> blocks and sidebar include.")

if __name__ == "__main__":
    entries = get_10_unique_entries()
    if len(entries) < 10:
        print("Not enough unique entries found.")
    else:
        generate_menu_html()
        backup_index()
        generate_new_index(entries)
