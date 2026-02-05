#!/bin/bash

# AI News Curator - Setup Script

set -e

echo "🚀 AI News Curator 설정을 시작합니다..."
echo ""

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")/.."

# Python 버전 확인
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python 버전: $python_version"

# 가상환경 생성
if [ ! -d "venv" ]; then
    echo "📦 가상환경 생성 중..."
    python3 -m venv venv
fi

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
echo "📦 의존성 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt

# 디렉토리 생성
echo "📁 디렉토리 생성 중..."
mkdir -p .claude/skills
mkdir -p agents/collector agents/analyzer agents/archiver
mkdir -p config
mkdir -p data/cache data/logs

# 설정 파일 복사
if [ ! -f "config/credentials.yaml" ]; then
    cp config/credentials.yaml.example config/credentials.yaml
    echo "⚠️  config/credentials.yaml 파일을 생성했습니다."
    echo "   노션 Integration Token과 Database ID를 입력해주세요."
fi

# .gitignore 확인
if [ ! -f ".gitignore" ]; then
    touch .gitignore
fi

if ! grep -q "credentials.yaml" .gitignore 2>/dev/null; then
    echo "config/credentials.yaml" >> .gitignore
fi

echo ""
echo "✅ 설정 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. 노션에서 Integration 생성 (https://www.notion.so/my-integrations)"
echo "2. 노션에서 데이터베이스 생성 및 Integration 연결"
echo "3. config/credentials.yaml에 토큰과 Database ID 입력"
echo "4. ./scripts/run.sh 실행"
