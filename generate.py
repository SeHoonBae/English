import pandas as pd
from datetime import datetime
import os
import hashlib
import json

# 파일 경로
CSV_FILE = 'english_lines.csv'
USED_FILE = 'used_sentences.json'
TODAY = datetime.now().strftime('%Y-%m-%d')
POSTS_DIR = 'posts'
INDEX_FILE = 'index.html'
TODAY_FILE = f'{POSTS_DIR}/{TODAY}.html'

# 해시 함수
def get_hash(text):
    return hashlib.md5(text.strip().lower().encode()).hexdigest()

# 사용된 해시 불러오기
def load_used_hashes():
    if os.path.exists(USED_FILE):
        with open(USED_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

# 해시 저장
def save_used_hashes(hashes):
    with open(USED_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(hashes), f, ensure_ascii=False, indent=2)

# 문장 5개 선택 (중복 제거)
def select_new_sentences():
    df = pd.read_csv(CSV_FILE)
    used_hashes = load_used_hashes()

    new_rows = []
    for _, row in df.iterrows():
        h = get_hash(row['english'])
        if h not in used_hashes:
            new_rows.append((row['english'], row['korean'], row['pronunciation'], h))
        if len(new_rows) >= 5:
            break

    # 해시 업데이트
    used_hashes.update([row[3] for row in new_rows])
    save_used_hashes(used_hashes)

    return new_rows

# HTML 콘텐츠 생성
def build_html(sentences):
    html = "<section>\n  <header class=\"major\">\n    <h2>오늘의 영어 문장</h2>\n  </header>\n  <div class=\"post\">\n"
    for eng, kor, pron, _ in sentences:
        html += f"""    <p><strong>{eng}</strong></p>
    <p>{kor}</p>
    <p>{pron}</p>
    <br />\n"""
    html += "  </div>\n</section>"
    return html

# 기존 템플릿 앞부분 유지
def inject_html(body):
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        html = f.read()
    start = html.find("<section")
    if start != -1:
        html = html[:start]
    return html + body

# 실행
def main():
    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)

    new_sentences = select_new_sentences()
    if not new_sentences:
        print("❗ 새 문장이 없습니다 (모두 등록됨)")
        return

    html_body = build_html(new_sentences)
    full_html = inject_html(html_body)

    # 저장
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(full_html)

    with open(TODAY_FILE, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"✅ index.html 및 {TODAY_FILE} 생성 완료")

if __name__ == '__main__':
    main()
