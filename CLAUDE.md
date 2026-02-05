# AI News Curator - Notion Archiving Edition

## 프로젝트 소개

AI 관련 최신 뉴스를 자동으로 수집하여 노션 데이터베이스에 아카이빙하는 에이전트입니다.

## 빠른 시작

```bash
# 1. 설정
./scripts/setup.sh

# 2. credentials.yaml 수정 (노션 토큰, DB ID 입력)

# 3. 실행
./scripts/run.sh
```

## 주요 명령어

```bash
# 전체 워크플로우 실행
python -m agents.orchestrator

# 또는 스크립트 사용
./scripts/run.sh
```

## 데이터 흐름

```
RSS/API → 수집 → 분석 → 노션 저장
         (24시간)  (중요도,카테고리,요약)  (데이터베이스 페이지)
```

## 노션 데이터베이스 속성

| 속성 | 타입 | 설명 |
|------|------|------|
| Title | title | 기사 제목 |
| URL | url | 원문 링크 |
| Source | select | 뉴스 출처 |
| Category | select | 카테고리 |
| Importance | select | 중요도 |
| Tags | multi_select | 태그 |
| Summary | text | AI 생성 요약 |
| Published | date | 원문 발행일 |
| Archived | date | 수집일 |
| Status | select | 읽음 상태 |
| Language | select | 언어 |

## 파일 구조

```
ai-news-curator/
├── agents/           # 에이전트 모듈
│   ├── collector/    # 뉴스 수집
│   ├── analyzer/     # 콘텐츠 분석
│   └── archiver/     # 노션 저장
├── config/           # 설정 파일
├── data/             # 캐시, 로그
└── scripts/          # 실행 스크립트
```

## 주의사항

- `config/credentials.yaml`은 절대 커밋하지 마세요
- 노션 API Rate Limit: 요청당 0.5초 딜레이 적용됨
