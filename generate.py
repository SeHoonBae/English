import os
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

    # 경로 정리 (/assets 기준으로)
    html = html.replace("href=\"assets/", "href=\"/assets/")
    html = html.replace("src=\"assets/", "src=\"/assets/")

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
    href_val = f"/posts/{POST_YEAR}/{POST_MONTH}/{YESTERDAY}.html"

    # 중복 제거 위해 텍스트 기준으로 찾기
    def find_existing_li(ul_tag, target_text):
        for li in ul_tag.find_all("li", recursive=False):
            span = li.find("span", class_="opener")
            if span and span.text.strip() == target_text:
                return li
        return None

    # 연도 li
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

    # 월 li
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

    # 링크 중복 방지 후 삽입
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

    # nav 메뉴 먼저 추출 및 교체
    nav_pattern = re.compile(r'(<nav id="menu">.*?</nav>)', re.DOTALL)
    nav_match = nav_pattern.search(html)
    if nav_match:
        updated_nav = update_sidebar(nav_match.group(1))
        html = html.replace(nav_match.group(1), updated_nav)

    # 기존 section 제거 후 새 section 삽입
    soup = BeautifulSoup(html, "html.parser")
    main_inner = soup.select_one("div#main > div.inner")
    if not main_inner:
        print("Cannot find main > inner block")
        return

    # 기존 섹션 중 "오늘의 영어 10문장" 제목 이후만 제거
    banner = main_inner.find("section", id="banner")
    if banner:
        for sibling in list(banner.find_next_siblings("section")):
            sibling.decompose()

    new_html = build_sections(entries)
    new_soup = BeautifulSoup(new_html, "html.parser")
    for section in new_soup.find_all("section"):
        main_inner.append(section)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(str(soup.prettify(formatter="html")))

    print("New index.html created with updated <section> blocks and sidebar menu.")

if __name__ == "__main__":
    entries = get_10_unique_entries()
    if len(entries) < 10:
        print("Not enough unique entries found.")
    else:
        backup_index()
        generate_new_index(entries)
