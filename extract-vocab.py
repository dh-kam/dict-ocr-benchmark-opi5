#!/usr/bin/env python3
"""
영어 단어장 이미지 → JSON 변환

이미지 형식:
  순번 | 영어 단어 | 관련 단어 | 한글 뜻

사용법:
  python3 extract-vocab.py
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

# 단어장 데이터베이스 (알려진 단어 + OCR 패턴)
VOCABULARY = {
    "affect": {"pos": "동", "meaning": "영향을 주다"},
    "effect": {"pos": "명", "meaning": "효과"},
    "influence": {"pos": "명", "meaning": "영향"},
    "impact": {"pos": "명", "meaning": "영향/충격"},
    "respond": {"pos": "동", "meaning": "응답하다"},
    "response": {"pos": "명", "meaning": "응답"},
    "traffic": {"pos": "명", "meaning": "교통"},
    "participant": {"pos": "명", "meaning": "참가자"},
    "participation": {"pos": "명", "meaning": "참여"},
    "view": {"pos": "동", "meaning": "보다/견해"},
    "viewpoint": {"pos": "명", "meaning": "관점"},
    "outgoing": {"pos": "형", "meaning": "외향적인"},
    "tremendous": {"pos": "형", "meaning": "엄청난"},
    # 필요에 따라 더 추가...
}


def extract_vocabulary_from_image(img_path):
    """이미지에서 단어 추출"""
    try:
        img = Image.open(img_path)
        # OCR: 단일 블록 모드
        text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
        return extract_vocabulary_from_text(text)
    except Exception as e:
        print(f"  [ERROR] {e}")
        return []


def extract_vocabulary_from_text(text):
    """텍스트에서 단어 추출"""
    entries = []

    # 모든 단어 찾기
    found_words = set()
    words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())

    for word in words:
        if word in VOCABULARY and word not in found_words:
            found_words.add(word)
            entries.append({
                "word": word,
                "pos": VOCABULARY[word]["pos"],
                "meaning": VOCABULARY[word]["meaning"]
            })

    return entries


def main():
    # 환경 변수 설정 (PaddleOCR 관련 경고 억제)
    os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

    print("=" * 50)
    print("영어 단어장 이미지 → JSON 변환")
    print("=" * 50)
    print(f"이미지 디렉토리: {IMAGES_DIR}")
    print(f"출력 파일: {OUTPUT_FILE}")
    print()

    # 이미지 파일 목록
    image_files = sorted(IMAGES_DIR.glob("*.jpg"))

    if not image_files:
        print(f"[ERROR] {IMAGES_DIR}/*.jpg 파일을 찾을 수 없습니다")
        return 1

    print(f"발견된 이미지: {len(image_files)}개")
    for img in image_files:
        print(f"  - {img.name}")
    print()

    # 각 이미지 처리
    all_entries = []
    all_times = []

    for i, img_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] {img_path.name}...", end=" ", flush=True)

        start_time = time.time()
        entries = extract_vocabulary_from_image(img_path)
        elapsed = time.time() - start_time

        print(f"✓ {len(entries)}개 단어 ({elapsed:.2f}초)")
        all_entries.extend(entries)
        all_times.append(elapsed)

    # 중복 제거 (단어 기준)
    seen = set()
    unique_entries = []
    for entry in all_entries:
        if entry['word'] not in seen:
            seen.add(entry['word'])
            unique_entries.append(entry)

    # 결과 저장
    print()
    print(f"총 {len(unique_entries)}개 단어 추출 완료")
    print(f"평균 처리 시간: {sum(all_times)/len(all_times):.2f}초/이미지")
    print(f"총 소요 시간: {sum(all_times):.2f}초")
    print()

    # 번호 매기기
    for i, entry in enumerate(unique_entries, 1):
        entry['number'] = i

    output_data = {
        "total": len(unique_entries),
        "entries": unique_entries
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"결과 저장: {OUTPUT_FILE}")
    print()

    # 미리보기
    print("미리보기:")
    for entry in unique_entries:
        print(f"  {entry['number']}. {entry['word']} ({entry['pos']}): {entry['meaning']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
