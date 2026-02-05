#!/bin/bash

# AI News Curator - Run Script
# Usage: ./scripts/run.sh [hours]

set -e

# 색상
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 기본값: 24시간
HOURS=${1:-24}

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════╗"
echo "║     🤖 AI News Curator                     ║"
echo "║     Notion Archiving Edition               ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}"

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")/.."

# 환경 확인
if [ ! -f "config/credentials.yaml" ]; then
    echo -e "${RED}❌ config/credentials.yaml 파일이 없습니다.${NC}"
    echo "   config/credentials.yaml.example을 복사하고 설정해주세요."
    exit 1
fi

# 디렉토리 생성
mkdir -p data/cache data/logs

# 가상환경 활성화 (있는 경우)
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# 실행
echo -e "${YELLOW}▶ Running with ${HOURS} hours lookback...${NC}"
echo ""

python -m agents.orchestrator

echo ""
echo -e "${GREEN}✅ Done!${NC}"
