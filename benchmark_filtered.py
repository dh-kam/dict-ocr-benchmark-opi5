#!/usr/bin/env python3
"""
필터링 적용 OCR 벤치마크
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
OUTPUT_FILE = Path("benchmark_results/filtered_results.json")

# 정답 데이터
GROUND_TRUTH = [
    {"image": "photo_2026-03-15_16-39-42.jpg", "words": ["affect", "influence", "impact", "tremendous"]},
    {"image": "photo_2026-03-28_13-04-45.jpg", "words": ["respond", "response"]},
    {"image": "photo_2026-03-28_13-04-49.jpg", "words": ["view", "viewpoint", "benefit"]},
    {"image": "photo_2026-03-28_13-04-54.jpg", "words": ["participant", "participation"]},
    {"image": "photo_2026-03-28_13-04-57.jpg", "words": ["outgoing"]},
    {"image": "photo_2026-03-28_13-05-01.jpg", "words": ["traffic"]},
]

ALL_TRUE_WORDS = set()
for item in GROUND_TRUTH:
    for word in item["words"]:
        ALL_TRUE_WORDS.add(word)

# 알려진 어휘별 (품사 접미사 제외 + 일반 명사/동사/형용사/부사)
# 단어장에 나오는 단어들로 필터링
VOCAB_FILTER_WORDS = {
    # 동사
    "respond", "affect", "benefit", "view", "impact",
    # 명사
    "response", "influence", "traffic", "participant", "participation",
    "viewpoint", "tremendous",
    # 형용사
    "outgoing",
    # 부사
    # 추가...
}

def extract_with_tesseract(img_path, config=""):
    """Tesseract OCR"""
    img = Image.open(img_path)
    text = pytesseract.image_to_string(img, lang='eng', config=config)
    # 영어 단어 추출 (4글자 이상)
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    return words

def filter_extracted_words(words, vocab_set=None):
    """추출된 단어 필터링"""
    if vocab_set:
        # 알려진 어휘 리스트로만 필터
        return [w for w in words if w in vocab_set]
    else:
        # 불용어 목록 제거
        stop_words = {
            "this", "that", "have", "from", "with", "they", "were", "would", "there",
            "their", "what", "when", "which", "your", "after", "before", "about",
            "just", "been", "into", "over", "also", "other", "could", "some",
            "time", "very", "more", "will", "than", "then", "them", "these",
            "such", "like", "make", "take", "know", "year", "good", "well",
            "said", "because", "even", "back", "through", "each", "where",
            "much", "must", "does", "want", "still", "give", "being", "here",
            "does", "llm", "vel", "seq", "num", "cnt", "text", "image"
        }
        return [w for w in words if w not in stop_words and len(w) >= 4]
    return words

def calculate_metrics(extracted_words, true_words):
    """정확도, 재현율, F1 계산"""
    extracted_set = set(extracted_words)
    true_set = set(true_words)

    tp = len(extracted_set & true_set)
    fp = len(extracted_set - true_set)
    fn = len(true_set - extracted_set)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "extracted_count": len(extracted_set),
        "true_count": len(true_set)
    }

def benchmark_filtered_approaches():
    """필터링 방법들 벤치마크"""
    results = []

    approaches = [
        ("Tesseract + 불용어 필터", ""),
        ("Tesseract PSM4 + 불용어 필터", "--psm 4"),
        ("Tesseract + 어휘 필터링 (VOCAB_FILTER_WORDS)", ""),
    ]

    for approach_name, config in approaches:
        use_vocab_filter = "어휘 필터링" in approach_name

        print(f"  [{approach_name}] 테스트 중...", flush=True)

        all_extracted = []
        all_times = []

        for item in GROUND_TRUTH:
            img_path = IMAGES_DIR / item["image"]

            start = time.time()
            try:
                words = extract_with_tesseract(img_path, config)
                if use_vocab_filter:
                    words = [w for w in words if w in VOCAB_FILTER_WORDS]
                else:
                    words = filter_extracted_words(words, None)
                elapsed = time.time() - start

                all_extracted.extend(words)
                all_times.append(elapsed)
            except Exception as e:
                print(f"    오류: {e}")
                continue

        metrics = calculate_metrics(all_extracted, list(ALL_TRUE_WORDS))

        results.append({
            "method": approach_name,
            "total_time": sum(all_times),
            "avg_time": sum(all_times) / len(all_times) if all_times else 0,
            **metrics
        })

    return results

def main():
    print("=" * 50)
    print("필터링 OCR 벤치마크")
    print("=" * 50)
    print(f"정답 단어: {len(ALL_TRUE_WORDS)}개")
    print()

    results = benchmark_filtered_approaches()

    # 결과 저장
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "ground_truth_count": len(ALL_TRUE_WORDS),
            "ground_truth_words": sorted(ALL_TRUE_WORDS),
            "results": results
        }, f, ensure_ascii=False, indent=2)

    # 테이블 출력
    print()
    print(f"{'방법':<30} {'정확도':<8} {'재현율':<8} {'F1':<8} {'추출':<6} {'정답':<6} {'시간':<10}")
    print("-" * 80)

    for r in results:
        print(f"{r['method']:<30} {r['precision']*100:>6.1f}%   {r['recall']*100:>6.1f}%   {r['f1']*100:>6.1f}%   {r['extracted_count']:>4}/{r['true_count']:<4} {r['total_time']:>6.1f}s")

    print()
    print(f"상세 결과: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
