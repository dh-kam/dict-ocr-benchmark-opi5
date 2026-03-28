#!/usr/bin/env python3
"""
최종 추천 스크립트: 필터링 적용 OCR
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from PIL import Image
import pytesseract

# 설정
IMAGES_DIR = Path("images")
OUTPUT_FILE = Path("vocabulary.json")

# 알려진 단어장 어휘 (확장된 목록)
VOCABULARY = {
    # 동사
    "respond": {"pos": "동", "meaning": "응답하다"},
    "affect": {"pos": "동", "meaning": "영향을 주다"},
    "benefit": {"pos": "명", "meaning": "이익/혜택"},
    "view": {"pos": "동", "meaning": "보다/견해"},
    "impact": {"pos": "명", "meaning": "영향/충격"},
    # 명사
    "response": {"pos": "명", "meaning": "응답"},
    "influence": {"pos": "명", "meaning": "영향"},
    "traffic": {"pos": "명", "meaning": "교통"},
    "participant": {"pos": "명", "meaning": "참가자"},
    "participation": {"pos": "명", "meaning": "참여"},
    "viewpoint": {"pos": "명", "meaning": "관점/견해"},
    # 형용사
    "tremendous": {"pos": "형", "meaning": "엄청난"},
    "outgoing": {"pos": "형", "meaning": "외향적인"},
}

# 불용어 목록 (예문에서 많이 나오는 단어들)
STOP_WORDS = {
    "this", "that", "have", "from", "with", "they", "were", "would", "there",
    "their", "what", "when", "which", "your", "after", "before", "about",
    "just", "been", "into", "over", "also", "other", "could", "some",
    "time", "very", "more", "will", "than", "then", "them", "these",
    "such", "like", "make", "take", "know", "year", "good", "well",
    "said", "because", "even", "back", "through", "each", "where",
    "much", "must", "does", "want", "still", "give", "being", "here",
    "electronic", "electricity", "devices", "devices", "contest", "prize",
    "first", "youngest", "won", "asked", "turn", "off", "all"
}


def extract_vocabulary():
    """어휘 추출 메인 함수"""
    all_entries = []
    seen_words = set()

    image_files = sorted(IMAGES_DIR.glob("*.jpg"))

    print("=" * 50)
    print("영어 단어장 이미지 → JSON 변환 (필터링 버전)")
    print("=" * 50)
    print(f"이미지: {len(image_files)}개")
    print()

    for i, img_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] {img_path.name}...", end=" ", flush=True)

        start = time.time()
        try:
            # OCR
            img = Image.open(img_path)
            text = pytesseract.image_to_string(img, lang='eng', config='--psm 4')

            # 단어 추출 및 필터링
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
            filtered = [w for w in words if w in VOCABULARY and w not in seen_words and w not in STOP_WORDS]

            for word in filtered:
                seen_words.add(word)
                all_entries.append({
                    "word": word,
                    "pos": VOCABULARY[word]["pos"],
                    "meaning": VOCABULARY[word]["meaning"]
                })

            elapsed = time.time() - start
            print(f"✓ {len(filtered)}개 단어 ({elapsed:.2f}초)")

        except Exception as e:
            print(f"✗ 오류: {e}")

    # 중복 제거 (단어 기준)
    seen = {}
    unique_entries = []
    for entry in all_entries:
        word = entry['word']
        if word not in seen:
            seen[word] = entry
            unique_entries.append(entry)

    # 정렬 및 번호 부여
    unique_entries = sorted(unique_entries, key=lambda x: x['word'])
    for i, entry in enumerate(unique_entries, 1):
        entry['number'] = i

    return unique_entries


def main():
    entries = extract_vocabulary()

    print()
    print(f"총 {len(entries)}개 단어 추출 완료")
    print()

    # 결과 저장
    output_data = {
        "total": len(entries),
        "entries": entries
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"결과 저장: {OUTPUT_FILE}")
    print()

    # 미리보기
    print("미리보기:")
    for entry in entries:
        print(f"  {entry['number']}. {entry['word']} ({entry['pos']}): {entry['meaning']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
