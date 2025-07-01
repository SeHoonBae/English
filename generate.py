import os
import shutil
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

# 기존 index.html을 로드하고 본문만 새로 채워 넣기
def generate_new_index(entries):
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    start_marker = '<!-- Section -->'
    split_point = html.find(start_marker)
    if split_point == -1:
        print("Section marker not found in index.html")
        return

    new_sections = [start_marker]
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

    before = html[:split_point]
    after = html[split_point:]

    # 기존 섹션 이후 내용 제거하고 새 섹션만 추가
    new_html = before + '\n'.join(new_sections) + '\n\t\t\t\t\t\n\t\t\t\t</div>\n\t\t\t</div>' + after.split('</div>\n\t\t\t</div>')[-1]

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(new_html)

    print("New index.html created with original layout preserved")

if __name__ == "__main__":
    entries = get_10_unique_entries()
    if len(entries) < 10:
        print("Not enough unique entries found.")
    else:
        backup_index()
        generate_new_index(entries)
