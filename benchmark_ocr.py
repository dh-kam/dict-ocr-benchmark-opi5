#!/usr/bin/env python3
"""
OCR/Vision 모델 벤치마크
단어장 이미지에서 단어 추출 정확도 및 속도 비교
"""

import os
import sys
import json
import time
import re
import subprocess
from pathlib import Path
from PIL import Image
import pytesseract

# 설정
IMAGES_DIR = Path("images")
OUTPUT_DIR = Path("benchmark_results")
OUTPUT_DIR.mkdir(exist_ok=True)

# 정답 데이터 (실제 이미지에서 확인)
# 이미지 1: photo_2026-03-15_16-39-42.jpg
GROUND_TRUTH = [
    {"image": "photo_2026-03-15_16-39-42.jpg", "words": ["affect", "influence", "impact", "tremendous"]},  # 4개
    # 이미지 2: photo_2026-03-28_13-04-45.jpg
    {"image": "photo_2026-03-28_13-04-45.jpg", "words": ["respond", "response"]},  # 2개
    # 이미지 3: photo_2026-03-28_13-04-49.jpg
    {"image": "photo_2026-03-28_13-04-49.jpg", "words": ["view", "viewpoint", "benefit"]},  # 3개
    # 이미지 4: photo_2026-03-28_13-04-54.jpg
    {"image": "photo_2026-03-28_13-04-54.jpg", "words": ["participant", "participation"]},  # 2개
    # 이미지 5: photo_2026-03-28_13-04-57.jpg
    {"image": "photo_2026-03-28_13-04-57.jpg", "words": ["outgoing"]},  # 1개
    # 이미지 6: photo_2026-03-28_13-05-01.jpg
    {"image": "photo_2026-03-28_13-05-01.jpg", "words": ["traffic"]},  # 1개
]

# 모든 정답 단어 (중복 제거)
ALL_TRUE_WORDS = set()
for item in GROUND_TRUTH:
    for word in item["words"]:
        ALL_TRUE_WORDS.add(word)

print(f"정답 단어 수: {len(ALL_TRUE_WORDS)}개 -> {sorted(ALL_TRUE_WORDS)}")


def calculate_metrics(extracted_words, true_words):
    """정확도, 재현율, F1 계산"""
    extracted_set = set(extracted_words)
    true_set = set(true_words)

    tp = len(extracted_set & true_set)  # True Positive
    fp = len(extracted_set - true_set)  # False Positive
    fn = len(true_set - extracted_set)   # False Negative

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


# ============================================
# 방법 1: Tesseract OCR (다양한 설정)
# ============================================

def benchmark_tesseract():
    """Tesseract OCR 벤치마크"""
    results = []

    configs = [
        ("Tesseract 기본", ""),
        ("Tesseract PSM 3", "--psm 3"),
        ("Tesseract PSM 4", "--psm 4"),
        ("Tesseract PSM 6", "--psm 6"),
        ("Tesseract PSM 11", "--psm 11"),
    ]

    for config_name, config in configs:
        print(f"  [{config_name}] 테스트 중...", flush=True)

        all_extracted = []
        all_times = []

        for item in GROUND_TRUTH:
            img_path = IMAGES_DIR / item["image"]

            start = time.time()
            try:
                img = Image.open(img_path)
                text = pytesseract.image_to_string(img, lang='eng', config=config)
                words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
                elapsed = time.time() - start

                all_extracted.extend(words)
                all_times.append(elapsed)
            except Exception as e:
                print(f"    오류: {e}")
                continue

        metrics = calculate_metrics(all_extracted, list(ALL_TRUE_WORDS))

        results.append({
            "method": config_name,
            "total_time": sum(all_times),
            "avg_time": sum(all_times) / len(all_times) if all_times else 0,
            **metrics
        })

    return results


# ============================================
# 방법 2: Tesseract + 전처리
# ============================================

def preprocess_image(img):
    """이미지 전처리"""
    # 그레이스케일
    img = img.convert('L')
    # 대비 향상
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    # 리사이즈
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    return img


def benchmark_tesseract_preprocessed():
    """Tesseract + 전처리"""
    results = []

    print(f"  [Tesseract + 전처리] 테스트 중...", flush=True)

    all_extracted = []
    all_times = []

    for item in GROUND_TRUTH:
        img_path = IMAGES_DIR / item["image"]

        start = time.time()
        try:
            img = Image.open(img_path)
            processed = preprocess_image(img)
            text = pytesseract.image_to_string(processed, lang='eng', config='--psm 6')
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
            elapsed = time.time() - start

            all_extracted.extend(words)
            all_times.append(elapsed)
        except Exception as e:
            print(f"    오류: {e}")
            continue

    metrics = calculate_metrics(all_extracted, list(ALL_TRUE_WORDS))

    results.append({
        "method": "Tesseract + 전처리",
        "total_time": sum(all_times),
        "avg_time": sum(all_times) / len(all_times) if all_times else 0,
        **metrics
    })

    return results


# ============================================
# 방법 3: PaddleOCR
# ============================================

def benchmark_paddleocr():
    """PaddleOCR 벤치마크"""
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
    except Exception as e:
        print(f"  [PaddleOCR] 설치되지 않음: {e}")
        return []

    results = []
    print(f"  [PaddleOCR] 테스트 중...", flush=True)

    all_extracted = []
    all_times = []

    for item in GROUND_TRUTH:
        img_path = IMAGES_DIR / item["image"]

        start = time.time()
        try:
            result = ocr.ocr(str(img_path))
            if result and result[0]:
                for line in result[0]:
                    text_info = line[1]
                    text = text_info[0] if isinstance(text_info, (list, tuple)) else text
                    if isinstance(text, str):
                        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
                        all_extracted.extend(words)
            elapsed = time.time() - start
            all_times.append(elapsed)
        except Exception as e:
            print(f"    오류: {e}")
            continue

    metrics = calculate_metrics(all_extracted, list(ALL_TRUE_WORDS))

    results.append({
        "method": "PaddleOCR",
        "total_time": sum(all_times),
        "avg_time": sum(all_times) / len(all_times) if all_times else 0,
        **metrics
    })

    return results


# ============================================
# 방법 4: llama.cpp + Qwen2.5-VL (시도)
# ============================================

def benchmark_llama_qwen():
    """llama.cpp + Qwen2.5-VL 벤치마크"""
    results = []

    model_configs = {
        "Qwen2.5-VL-3B-Q8_0": "/workspace/opi5-llama/models/Qwen2.5-VL-3B-Instruct-Q8_0.gguf",
    }

    for model_name, model_path in model_configs.items():
        if not Path(model_path).exists():
            continue

        print(f"  [{model_name}] 테스트 중...", flush=True)

        all_extracted = []
        all_times = []

        for item in GROUND_TRUTH:
            img_path = IMAGES_DIR / item["image"]

            prompt = '''이미지에서 영어 단어들을 추출하세요. 단어 목록만 출력:
word1, word2, word3, ...'''

            start = time.time()
            try:
                # 타임아웃 설정으로 안전하게 실행
                result = subprocess.run(
                    ["timeout", "60", "taskset", "-c", "4-7",
                     "/workspace/opi5-llama/llama.cpp/build/bin/llama-cli",
                     "-m", model_path,
                     "--mmproj", "/workspace/opi5-llama/models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf",
                     "--image", str(img_path),
                     "-p", prompt,
                     "-n", "256",
                     "-t", "4"],
                    capture_output=True,
                    text=True,
                    timeout=70
                )
                elapsed = time.time() - start

                if result.returncode == 0:
                    output = result.stdout.decode('utf-8', errors='ignore')
                    words = re.findall(r'\b[a-zA-Z]{4,}\b', output.lower())
                    all_extracted.extend(words)
                    all_times.append(elapsed)
                else:
                    print(f"    실패 (exit code: {result.returncode})")
            except Exception as e:
                print(f"    오류: {e}")
                continue

        if all_times:
            metrics = calculate_metrics(all_extracted, list(ALL_TRUE_WORDS))

            results.append({
                "method": model_name,
                "total_time": sum(all_times),
                "avg_time": sum(all_times) / len(all_times),
                **metrics
            })

    return results


# ============================================
# 메인 실행
# ============================================

def main():
    print("=" * 60)
    print("OCR/Vision 모델 벤치마크")
    print("=" * 60)
    print(f"이미지 디렉토리: {IMAGES_DIR}")
    print(f"출력 디렉토리: {OUTPUT_DIR}")
    print(f"정답 단어: {len(ALL_TRUE_WORDS)}개")
    print()

    all_results = []

    # Tesseract OCR
    print("[1/4] Tesseract OCR 설정별 비교")
    all_results.extend(benchmark_tesseract())
    print()

    # Tesseract + 전처리
    print("[2/4] Tesseract + 전처리")
    all_results.extend(benchmark_tesseract_preprocessed())
    print()

    # PaddleOCR (skip - crashes on ARM64)
    print("[3/4] PaddleOCR - 건너뜀 (ARM64 충돌)")
    print()
    # all_results.extend(benchmark_paddleocr())
    print()

    # llama.cpp + Qwen (skip - crashes on vision)
    print("[4/4] llama.cpp + Qwen2.5-VL - 건너뜀 (vision 충돌)")
    print()
    # all_results.extend(benchmark_llama_qwen())
    print()

    # 결과 저장
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    result_file = OUTPUT_DIR / f"benchmark_{timestamp}.json"

    output = {
        "timestamp": timestamp,
        "ground_truth_count": len(ALL_TRUE_WORDS),
        "ground_truth_words": sorted(ALL_TRUE_WORDS),
        "results": all_results
    }

    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print("벤치마크 완료")
    print("=" * 60)
    print()

    # 테이블 출력
    print(f"{'방법':<25} {'정확도':<8} {'재현율':<8} {'F1':<8} {'추출':<6} {'정답':<6} {'시간':<10}")
    print("-" * 80)

    for r in all_results:
        print(f"{r['method']:<25} {r['precision']*100:>6.1f}%   {r['recall']*100:>6.1f}%   {r['f1']*100:>6.1f}%   {r['extracted_count']:>4}/{r['true_count']:<4} {r['total_time']:>6.1f}s")

    print()
    print(f"상세 결과: {result_file}")


if __name__ == "__main__":
    main()
