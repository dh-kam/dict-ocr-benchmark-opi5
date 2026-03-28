# OCR Benchmark for Orange Pi 5 (RK3588)

영어 단어장 이미지에서 단어를 추출하는 OCR 벤치마크 프로젝트입니다.

## 목차

- [개요](#개요)
- [벤치마크 결과](#벤치마크-결과)
- [빠른 시작](#빠른-시작)
- [설정](#설정)
- [벤치마크 실행](#벤치마크-실행)
- [프로젝트 구조](#프로젝트-구조)
- [결과 분석](#결과-분석)

## 개요

이 프로젝트는 Orange Pi 5 (RK3588 SoC)에서 다양한 OCR/Vision 모델을 벤치마킹하여:

- 영어 단어장 이미지에서 단어 추출
- 정확도(Precision), 재현율(Recall), F1 점수 측정
- 처리 속도 비교

### 테스트 환경

- **장치**: Orange Pi 5 (RK3588, ARM64)
- **CPU**: 4x Cortex-A76 @ 2.4GHz + 4x Cortex-A55 @ 1.8GHz
- **RAM**: 8GB~16GB
- **이미지**: 6개 JPG 파일 (단어장 캡처)
- **정답 단어**: 13개

## 벤치마크 결과

### 최종 추천: **Tesseract + 어휘 필터링**

| 방법 | 정확도 | 재현율 | F1 점수 | 추출/정답 | 시간 |
|------|--------|--------|----------|----------|------|
| Tesseract + 어휘 필터링 | **100.0%** | 84.6% | **91.7%** | **11/13** | **4.1초** ⭐ |

### 전체 결과 비교

#### Tesseract OCR (다양한 설정)

| 방법 | 정확도 | 재현율 | F1 점수 | 추출/정답 | 시간 |
|------|--------|--------|----------|----------|------|
| Tesseract 기본 | 7.6% | 84.6% | 13.9% | 145/13 | 4.1초 |
| Tesseract PSM 3 | 7.6% | 84.6% | 13.9% | 145/13 | 4.1초 |
| Tesseract PSM 4 | 7.6% | 84.6% | **13.9%** | 145/13 | 4.0초 |
| Tesseract PSM 6 | 5.7% | 84.6% | 10.7% | 192/13 | 6.0초 |
| Tesseract PSM 11 | 5.8% | 76.9% | 10.8% | 172/13 | 4.8초 |
| Tesseract + 전처리 | 4.5% | 76.9% | 8.5% | 222/13 | 12.6초 |

#### 필터링 적용 결과

| 방법 | 정확도 | 재현율 | F1 점수 | 추출/정답 | 시간 |
|------|--------|--------|----------|----------|------|
| Tesseract + 불용어 필터 | 8.3% | 84.6% | 15.1% | 133/13 | 4.2초 |
| Tesseract PSM4 + 불용어 필터 | 8.2% | 84.6% | 15.0% | 134/13 | 4.2초 |
| **Tesseract + 어휘 필터링** | **100.0%** | 84.6% | **91.7%** | **11/13** | **4.1초** |

### 테스트된 모델

| 모델/방법 | 상태 | 결과 |
|-----------|------|------|
| **Tesseract OCR** | ✅ 작동 | 최고 F1: 91.7% (어휘 필터링) |
| **PaddleOCR** | ❌ 충돌 | ARM64 호환 문제 |
| **llama.cpp + Qwen2.5-VL** | ❌ 충돌 | 메모리 문제로 vision 모듈 crash |

## 빠른 시작

### 1. 의존성 설치

```bash
# Debian/Ubuntu 기반
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-eng libgomp1 python3-pip

# Python 패키지
pip3 install Pillow pytesseract
```

### 2. 단어 추출 실행

```bash
python3 extract_vocab_final.py
```

결과는 `vocabulary.json`에 저장됩니다.

### 3. (선택) Vision 모델 사용

HuggingFace 토큰이 필요합니다:

```bash
# HuggingFace 토큰 설정 (https://huggingface.co/settings/tokens)
export HF_API_KEY="your_token_here"

# 모델 다운로드
./scripts/download_models.sh
```

## 설정

### 단어 목록 추가

`extract_vocab_final.py`의 `VOCABULARY` 딕셔너리에 단어를 추가하세요:

```python
VOCABULARY = {
    "respond": {"pos": "동", "meaning": "응답하다"},
    "your_word": {"pos": "명", "meaning": "의미"},
    # ...
}
```

### 불용어 추가

`STOP_WORDS` 세트에 제외할 단어를 추가하세요.

## 벤치마크 실행

### 전체 벤치마크

```bash
python3 benchmark_ocr.py
```

### 필터링 벤치마크

```bash
python3 benchmark_filtered.py
```

결과는 `benchmark_results/` 디렉토리에 저장됩니다.

## 프로젝트 구조

```
opi5-llama/
├── images/                      # 단어장 이미지 (6개 JPG)
├── scripts/
│   └── download_models.sh       # HuggingFace 모델 다운로더
├── models/                      # GGUF 모델 파일 (git 제외)
├── benchmark_results/           # 벤치마크 결과 (git 제외)
├── benchmark_ocr.py             # 전체 벤치마크 스크립트
├── benchmark_filtered.py        # 필터링 벤치마크
├── extract_vocab_final.py       # 추천 단어 추출 스크립트
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
