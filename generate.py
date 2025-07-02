import os
import shutil
import re
from datetime import datetime, timedelta

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
# 사용된 문장은 파일에서 제거
def get_10_unique_entries():
    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    entries = [lines[i:i+4] for i in range(0, len(lines), 4)]
    new_entries = entries[:10]

    if len(new_entries) < 10:
        return []

    # 사용된 문장은 제거하고 파일 덮어쓰기
    remaining = entries[10:]
    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        for entry in remaining:
            f.write('\n'.join(entry) + '\n\n')

    return new_entries

# index.html 백업 함수 (상대 경로 보존)
def backup_index():
    if not os.path.exists(INDEX_FILE):
        print("index.html not found!")
        return
    os.makedirs(POST_FOLDER, exist_ok=True)
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    # 상대 경로로 css, js 등 경로 수정
    html = html.replace("href=\"assets/", "href=\"../../../assets/")
    html = html.replace("src=\"assets/", "src=\"../../../assets/")

    with open(POST_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Backed up index.html to {POST_PATH}")

# 본문 <section>들만 찾아서 교체하고 사이드바 업데이트
def generate_new_index(entries):
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    # 본문 <section> 교체
    section_pattern = re.compile(r'(<section>\s*<div class=\"features\">.*?</section>)', re.DOTALL)
    all_sections = section_pattern.findall(html)
    if not all_sections:
        print("No <section> blocks found.")
        return
    first_section_start = html.find(all_sections[0])
    last_section_end = html.rfind(all_sections[-1]) + len(all_sections[-1])
    before = html[:first_section_start]
    after = html[last_section_end:]

    new_sections = []
    for i, entry in enumerate(entries):
        new_sections.append(f'''
<section>
	<div class=\"features\">
		<article>
			<div class=\"content\">
				<h2>{i+1}. {entry[0]}</h2>
				<h2>{entry[1]}</h2>
				<h3>{entry[2]}</h3>
			</div>
		</article>
	</div>
</section>''')

    html = before + ''.join(new_sections) + after

    # 사이드바 전체 유지하면서 새로운 날짜만 누적으로 추가
    menu_block = f'<li><a href="/English/posts/{POST_YEAR}/{POST_MONTH}/{YESTERDAY}.html">{POST_MONTH}월 {POST_DAY}일 영어문장 10개</a></li>'
    year_block = f'<span class=\"opener\">{POST_YEAR}년 모음</span>'
    month_block = f'<span class=\"opener\">{POST_MONTH}월 모음</span>'

    # 1. 연도 블럭 존재 확인
    if year_block not in html:
        year_html = f'''<li>
	{year_block}
	<ul>
		<li>
			{month_block}
			<ul>
				{menu_block}
			</ul>
		</li>
	</ul>
</li>'''
        html = html.replace('</ul>', year_html + '\n</ul>', 1)

    # 2. 월 블럭 존재 여부
    elif month_block not in html:
        pattern = re.compile(rf'({year_block}\s*<ul>)(.*?)</ul>', re.DOTALL)
        html = pattern.sub(lambda m: m.group(1) + f'\n<li>{month_block}<ul>{menu_block}</ul></li>' + '</ul>', html)

    # 3. 날짜 항목 추가
    else:
        pattern = re.compile(rf'({month_block}\s*<ul>)(.*?)(</ul>)', re.DOTALL)
        html = pattern.sub(lambda m: m.group(1) + f'\n{menu_block}' + m.group(2) + m.group(3), html)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print("New index.html created with updated <section> blocks and sidebar menu.")

if __name__ == "__main__":
    entries = get_10_unique_entries()
    if len(entries) < 10:
        print("Not enough unique entries found.")
    else:
        backup_index()
        generate_new_index(entries)
