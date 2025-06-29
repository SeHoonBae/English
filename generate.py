
import os
import hashlib
import json
from datetime import datetime

TXT_FILE = 'english_lines.txt'
USED_FILE = 'used_sentences.json'
TODAY = datetime.now().strftime('%Y-%m-%d')
POSTS_DIR = 'posts'
INDEX_FILE = 'index.html'
TODAY_FILE = f'{POSTS_DIR}/{TODAY}.html'

def get_hash(text):
    return hashlib.md5(text.strip().lower().encode()).hexdigest()

def load_used_hashes():
    if os.path.exists(USED_FILE):
        with open(USED_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_used_hashes(hashes):
    with open(USED_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(hashes), f, ensure_ascii=False, indent=2)

def load_sentences():
    with open(TXT_FILE, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    sentences = [lines[i:i+3] for i in range(0, len(lines), 3)]
    return sentences

def select_new_sentences(sentences, used_hashes):
    new = []
    for s in sentences:
        h = get_hash(s[0])
        if h not in used_hashes:
            new.append((s[0], s[1], s[2], h))
        if len(new) >= 10:
            break
    return new

def build_html(sentences):
    html = "<section>\n  <header class=\"major\"><h2>오늘의 영어 문장</h2></header>\n  <div class=\"post\">\n"
    for eng, kor, pron, _ in sentences:
        html += f"    <p><strong>{eng}</strong></p>\n    <p>{kor}</p>\n    <p>{pron}</p>\n    <br />\n"
    html += "  </div>\n</section>"
    return html

def inject_html(body):
    if not os.path.exists(INDEX_FILE):
        return body
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        html = f.read()
    insert_point = html.find("<!-- 여기 아래에 자동 삽입됨 -->")
    return html[:insert_point] + body + html[insert_point:]

def main():
    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)

    used_hashes = load_used_hashes()
    sentences = load_sentences()
    new_sentences = select_new_sentences(sentences, used_hashes)
    if not new_sentences:
        print("❗ 새 문장이 없습니다.")
        return

    html_body = build_html(new_sentences)
    full_html = inject_html(html_body)

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(full_html)
    with open(TODAY_FILE, 'w', encoding='utf-8') as f:
        f.write(full_html)

    used_hashes.update([s[3] for s in new_sentences])
    save_used_hashes(used_hashes)
    print(f"✅ index.html 및 {TODAY_FILE} 생성 완료")

if __name__ == '__main__':
    main()
