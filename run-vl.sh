#!/bin/bash
# Qwen2.5-VL-3B-Instruct on Orange Pi 5 (RK3588)
# CPU+NEON+OpenBLAS optimized build

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LLAMA_CLI="${SCRIPT_DIR}/llama.cpp/build/bin/llama-cli"
MODEL="${SCRIPT_DIR}/models/Qwen2.5-VL-3B-Instruct-Q8_0.gguf"
MMPROJ="${SCRIPT_DIR}/models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf"

# Use A76 performance cores only (cores 4-7)
THREADS=4

# Options
IMAGE=""
PROMPT=""
CTX=4096
N_TOKENS=256

usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -i, --image FILE   Image file for vision analysis"
    echo "  -p, --prompt TEXT  Prompt text"
    echo "  -c, --ctx NUM      Context length (default: 4096)"
    echo "  -n, --tokens NUM   Max tokens to generate (default: 256)"
    echo "  -t, --threads NUM  Number of threads (default: 4)"
    echo "  -h, --help         Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 -p 'What is the meaning of life?'"
    echo "  $0 -i photo.jpg -p 'Describe this image'"
    echo "  $0  # Interactive chat mode"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--image) IMAGE="$2"; shift 2 ;;
        -p|--prompt) PROMPT="$2"; shift 2 ;;
        -c|--ctx) CTX="$2"; shift 2 ;;
        -n|--tokens) N_TOKENS="$2"; shift 2 ;;
        -t|--threads) THREADS="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

if [ ! -f "$MODEL" ]; then
    echo "Error: Model not found at $MODEL"
    exit 1
fi

CMD="taskset -c 4-7 $LLAMA_CLI -m $MODEL --mmproj $MMPROJ -c $CTX -n $N_TOKENS -t $THREADS"

if [ -n "$IMAGE" ]; then
    if [ ! -f "$IMAGE" ]; then
        echo "Error: Image not found: $IMAGE"
        exit 1
    fi
    CMD="$CMD --image $IMAGE"
fi

if [ -n "$PROMPT" ]; then
    CMD="$CMD -p \"$PROMPT\""
fi

echo "=== Qwen2.5-VL-3B on Orange Pi 5 (RK3588) ==="
echo "Threads: $THREADS (A76 performance cores)"
echo "Context: $CTX"
echo "Model: $(basename $MODEL)"
echo ""

eval $CMD
