# OCR Benchmark for Orange Pi 5 (RK3588)

영어 단어장 이미지에서 단어를 추출하는 OCR 벤치마크 프로젝트입니다.

## 실행 순서

파일 이름의 숫자 접두사는 실행 순서를 나타냅니다:

```
1_setup.sh                 # 설치 스크립트
scripts/2_download_models.sh  # HF 모델 다운로드
3_benchmark_ocr.py         # 전체 벤치마크
4_benchmark_filtered.py    # 필터링 벤치마크
5_extract_vocab_final.py  # 단어 추출 (추천)
```

## 빠른 시작

```bash
# 1. 설치
./1_setup.sh

# 2. 단어 추출 (Tesseract OCR만 사용 - 모델 불필요)
python3 5_extract_vocab_final.py

# 결과: vocabulary.json
```

## (선택) Vision 모델 사용

```bash
# 1. HuggingFace 토큰 설정
export HF_API_KEY="your_token_here"

# 2. 모델 다운로드
./scripts/2_download_models.sh
```

## 벤치마크 실행

```bash
# 전체 벤치마크
python3 3_benchmark_ocr.py

# 필터링 벤치마크
python3 4_benchmark_filtered.py
```

## 벤치마크 결과

### 최종 추천: **Tesseract + 어휘 필터링**

| 방법 | 정확도 | 재현율 | F1 점수 | 추출/정답 | 시간 |
|------|--------|--------|----------|----------|------|
| Tesseract + 어휘 필터링 | **100.0%** | 84.6% | **91.7%** | **11/13** | **4.1초** ⭐ |

### 테스트된 모델

| 모델/방법 | 상태 | 결과 |
|-----------|------|------|
| **Tesseract OCR** | ✅ 작동 | 최고 F1: 91.7% (어휘 필터링) |
| **PaddleOCR** | ❌ 충돌 | ARM64 호환 문제 |
| **llama.cpp + Qwen2.5-VL** | ❌ 충돌 | 메모리 문제로 vision 모듈 crash |

## 설정

### 단어 목록 추가

`5_extract_vocab_final.py`의 `VOCABULARY` 딕셔너리에 단어를 추가하세요:

```python
VOCABULARY = {
    "respond": {"pos": "동", "meaning": "응답하다"},
    "your_word": {"pos": "명", "meaning": "의미"},
    # ...
}
```

### 불용어 추가

`STOP_WORDS` 세트에 제외할 단어를 추가하세요.

## 프로젝트 구조

```
dict-ocr-benchmark-opi5/
├── 1_setup.sh                   # 설치 스크립트
├── scripts/
│   └── 2_download_models.sh     # HF 모델 다운로더
├── 3_benchmark_ocr.py           # 전체 벤치마크
├── 4_benchmark_filtered.py      # 필터링 벤치마크
├── 5_extract_vocab_final.py     # 추천 단어 추출 스크립트
├── images/                      # 단어장 이미지 (6개 JPG)
├── models/                      # GGUF 모델 파일 (git 제외)
├── benchmark_results/           # 벤치마크 결과 (git 제외)
├── BENCHMARK_SUMMARY.md         # 벤치마크 요약
└── README.md                    # 이 파일
```

## 결과 분석

### 놓친 단어

- `benefit` - OCR이 "electronic"으로 잘못 인식
- `viewpoint` - OCR에서 누락됨

이 단어들은 단어장 카드의 예문에 있는 다른 단어들로 인해 OCR 오류가 발생합니다.

### 개선 제안

1. **어휘 사전 확장**: 놓친 단어들을 VOCABULARY에 추가
2. **이미지 전처리**: 카드 영역만 크롭하거나 예문 제외
3. **하이브리드 접근**: Tesseract + Vision 모델 결합

## 라이선스

MIT License

## 참고

- Tesseract OCR: https://github.com/tesseract-ocr/tesseract
- Qwen2.5-VL: https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct-GGUF
- Orange Pi 5: https://www.orangepi.org/html/hardwareKaoman/compAndAppliance/OrangePi5.html
