#!/bin/bash
#
# OCR Benchmark 설치 스크립트
# Orange Pi 5 (RK3588) - Debian/Ubuntu 기반
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "OCR Benchmark 설치"
echo "=========================================="
echo

# 시스템 패키지 설치
echo "[1/3] 시스템 패키지 설치..."
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-eng libgomp1 python3-pip git

# Python 패키지 설치
echo "[2/3] Python 패키지 설치..."
pip3 install --break-system-packages Pillow pytesseract huggingface_hub || pip3 install Pillow pytesseract huggingface_hub

# 권한 설정
echo "[3/3] 스크립트 실행 권한 설정..."
chmod +x scripts/*.sh
chmod +x *.sh 2>/dev/null || true

echo
echo -e "${GREEN}✓ 설치 완료!${NC}"
echo
echo "다음 단계:"
echo "  1. HuggingFace 토큰 설정:"
echo "     export HF_API_KEY='your_token_here'"
echo
echo "  2. 모델 다운로드:"
echo "     ./scripts/2_download_models.sh"
echo
echo "  3. 벤치마크 실행:"
echo "     python3 3_benchmark_ocr.py"
echo
echo "  4. 단어 추출:"
echo "     python3 5_extract_vocab_final.py"
echo
