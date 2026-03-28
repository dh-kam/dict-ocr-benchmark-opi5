#!/bin/bash
# 영어 단어장 이미지를 JSON으로 변환하는 스크립트
# Qwen2.5-VL 모델 사용

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LLAMA_CLI="${SCRIPT_DIR}/llama.cpp/build/bin/llama-cli"
MODEL="${SCRIPT_DIR}/models/Qwen2.5-VL-3B-Instruct-Q8_0.gguf"
MMPROJ="${SCRIPT_DIR}/models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf"
IMAGES_DIR="${SCRIPT_DIR}/images"
OUTPUT="${SCRIPT_DIR}/vocabulary.json"

THREADS=4
CTX=4096

# JSON 문법 (llama.cpp의 grammar 형식)
GRAMMAR='
root "[" item "]"
item "{" ws "\"number\"" ws ":" ws number ws "," ws "\"word\"" ws ":" ws string ws "," ws "\"pos\"" ws ":" ws string ws "," ws "\"meaning\"" ws ":" ws string ws "}"
ws ::= " "*
string ::= "\"" [^"\\] "\"" | "\\" escape
escape ::= ["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F]
number ::= [0-9]+
'

# 프롬프트
PROMPT='이 이미지는 영어 단어장 사진입니다. 이미지에서 다음 정보를 추출하여 JSON 배열 형식으로 반환하세요:

[
  {"number": 단어 순번(숫자만), "word": "영어 단어", "pos": "품사(명/형/부 중 하나)", "meaning": "한글 뜻"},
  ...
]

규칙:
- 순번은 숫자만 (예: 1, 2, 3)
- 품사는 한글자로: 명(명사), 형(형용사), 부(부사)
- 한글 뜻은 정확히 표기
- 유효한 JSON만 출력 (다른 설명 없이)
'

echo "=== 영어 단어장 이미지 → JSON 변환 ==="
echo "이미지 디렉토리: $IMAGES_DIR"
echo "출력 파일: $OUTPUT"
echo ""

# 이미지 파일 목록
IMAGE_FILES=($(ls "$IMAGES_DIR"/*.jpg 2>/dev/null))

if [ ${#IMAGE_FILES[@]} -eq 0 ]; then
    echo "오류: $IMAGES_DIR/*.jpg 파일을 찾을 수 없습니다"
    exit 1
fi

echo "발견된 이미지: ${#IMAGE_FILES[@]}개"
ls -1 "$IMAGES_DIR"/*.jpg
echo ""

# 각 이미지 처리
ALL_RESULTS="["

for i in "${!IMAGE_FILES[@]}"; do
    IMG="${IMAGE_FILES[$i]}"
    IMG_NAME=$(basename "$IMG")
    echo "[$((i+1))/${#IMAGE_FILES[@]}] 처리 중: $IMG_NAME"

    RESULT=$(taskset -c 4-7 $LLAMA_CLI \
        -m "$MODEL" \
        --mmproj "$MMPROJ" \
        --image "$IMG" \
        -p "$PROMPT" \
        -n 2048 \
        -t $THREADS \
        -c $CTX \
        --temp 0.1 \
        2>/dev/null | grep -A 999 '\[' | grep -B 999 '\]' | head -n -1 | tail -n +2)

    if [ -n "$RESULT" ]; then
        if [ "$i" -gt 0 ]; then
            ALL_RESULTS="$ALL_RESULTS,"
        fi
        ALL_RESULTS="$ALL_RESULTS
$RESULT"
    fi
done

ALL_RESULTS="$ALL_RESULTS
]"

# 결과 저장
echo "$ALL_RESULTS" > "$OUTPUT"

echo ""
echo "=== 완료 ==="
echo "결과가 $OUTPUT 에 저장되었습니다"
echo ""
head -c 500 "$OUTPUT"
echo "..."
