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
POST_FOLDER = os.path.join(POSTS_DIR, yesterday.strftime("%Y"), yesterday.strftime("%m"))
POST_PATH = os.path.join(POST_FOLDER, f"{YESTERDAY}.html")

# 문장 10세트(4줄 × 10개) 추출 함수
def get_10_unique_entries():
    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    entries = [lines[i:i+4] for i in range(0, len(lines), 4)]
    used_sentences = set()
    new_entries = []

    for entry in entries:
        if len(new_entries) >= 10:
            break
        if entry[0] not in used_sentences:
            new_entries.append(entry)
            used_sentences.add(entry[0])

    return new_entries

# index.html 백업 함수
def backup_index():
    if not os.path.exists(INDEX_FILE):
        print("index.html not found!")
        return
    os.makedirs(POST_FOLDER, exist_ok=True)
    shutil.copy(INDEX_FILE, POST_PATH)
    print(f"Backed up index.html to {POST_PATH}")

# 본문 <section>들만 찾아서 교체
def generate_new_index(entries):
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    # 기존 section 영역을 전부 찾아 제거
    new_body = ""
    pattern = re.compile(r'(\s*<section>.*?</section>)', re.DOTALL)
    all_sections = pattern.findall(html)

    if not all_sections:
        print("No <section> blocks found.")
        return

    first_section_start = html.find(all_sections[0])
    last_section_end = html.rfind(all_sections[-1]) + len(all_sections[-1])

    before = html[:first_section_start]
    after = html[last_section_end:]

    # 새 section들 생성
    new_sections = []
    for i, entry in enumerate(entries):
        new_sections.append(f'''
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

    new_html = before + ''.join(new_sections) + after

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(new_html)

    print("New index.html created with updated <section> blocks only.")

if __name__ == "__main__":
    entries = get_10_unique_entries()
    if len(entries) < 10:
        print("Not enough unique entries found.")
    else:
        backup_index()
        generate_new_index(entries)
