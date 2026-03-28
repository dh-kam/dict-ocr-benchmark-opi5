#!/bin/bash
#
# HuggingFace에서 Qwen2.5-VL 모델 다운로드 스크립트
# 사용법: export HF_API_KEY="your_token_here" && ./scripts/2_download_models.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="${PROJECT_DIR}/models"

# 모델 정보
MODEL_REPO="Qwen/Qwen2.5-VL-3B-Instruct-GGUF"
MODEL_FILE="Qwen2.5-VL-3B-Instruct-Q8_0.gguf"
MMPROJ_FILE="Qwen2.5-VL-3B-Instruct-f16.gguf"

# 색상 출력
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Qwen2.5-VL 모델 다운로더"
echo "=========================================="
echo

# API 키 확인
if [ -z "$HF_API_KEY" ] && [ -z "$HF_TOKEN" ]; then
    echo -e "${RED}오류: HF_API_KEY 또는 HF_TOKEN 환경변수가 설정되지 않았습니다.${NC}"
    echo
    echo "사용법:"
    echo "  export HF_API_KEY='your_huggingface_token_here'"
    echo "  ./scripts/download_models.sh"
    echo
    echo "HuggingFace 토큰 발급: https://huggingface.co/settings/tokens"
    exit 1
fi

# HF_TOKEN 설정 (우선순위: HF_TOKEN > HF_API_KEY)
if [ -n "$HF_API_KEY" ] && [ -z "$HF_TOKEN" ]; then
    export HF_TOKEN="$HF_API_KEY"
fi

# 디렉토리 생성
mkdir -p "$MODELS_DIR"

# huggingface-cli 확인
if ! command -v huggingface-cli &> /dev/null; then
    echo -e "${YELLOW}huggingface-cli가 설치되지 않았습니다. 설치합니다...${NC}"
    pip3 install -U "huggingface_hub[cli]"
fi

# 로그인 상태 확인
echo "HuggingFace 인증 확인..."
huggingface-cli whoami > /dev/null 2>&1 || {
    echo -e "${YELLOW}HuggingFace에 로그인합니다...${NC}"
    echo "token=$HF_TOKEN" | huggingface-cli login --token -
}

# 다운로드 함수
download_file() {
    local repo=$1
    local file=$2
    local output=$3

    if [ -f "$output" ]; then
        echo -e "${GREEN}✓ 이미 존재함: $file${NC}"
        return 0
    fi

    echo "다운로드 중: $file"
    echo "  저장소: $repo"
    echo "  대상: $output"

    start_time=$(date +%s)

    if huggingface-cli download "$repo" "$file" --local-dir "$MODELS_DIR" --local-dir-use-symlinks False; then
        end_time=$(date +%s)
        elapsed=$((end_time - start_time))

        # 파일 크기 계산
        if [ -f "$output" ]; then
            size=$(du -h "$output" | cut -f1)
            echo -e "${GREEN}✓ 완료: $file ($size, ${elapsed}초)${NC}"
        else
            echo -e "${YELLOW}⚠ 다운로드 완료되었으나 파일을 찾을 수 없습니다${NC}"
        fi
    else
        echo -e "${RED}✗ 실패: $file${NC}"
        return 1
    fi
    echo
}

# 메인 다운로드
echo
echo "모델 파일 다운로드를 시작합니다..."
echo

# 모델 파일
download_file "$MODEL_REPO" "$MODEL_FILE" "$MODELS_DIR/$MODEL_FILE"

# mmproj 파일
download_file "$MODEL_REPO" "$MMPROJ_FILE" "$MODELS_DIR/$MMPROJ_FILE"

echo
echo "=========================================="
echo -e "${GREEN}다운로드 완료!${NC}"
echo "=========================================="
echo
echo "다운로드된 파일:"
ls -lh "$MODELS_DIR"/*.gguf 2>/dev/null || echo "  (GGUF 파일 없음)"
echo
echo "모델이 준비되었습니다. 다음을 실행하세요:"
echo "  python3 5_extract_vocab_final.py"
echo
