# AI News Curator + LinkedIn Post Generator - Agent Guide

> 이 파일은 목차다. 상세 내용은 각 링크를 따라가라.

## Quick Start

```bash
./scripts/setup.sh                          # 가상환경 + 의존성 설치
cp config/credentials.yaml.example config/credentials.yaml
# credentials.yaml에 Notion Token, Anthropic API Key, DB ID 입력
./venv/bin/python -m agents.orchestrator    # 전체 파이프라인 실행
```

## Golden Principles

1. **파이프라인은 단방향이다** — RSS 수집 -> 분석 -> 뉴스 저장 -> 필터 -> 포스트 생성 -> 포스트 저장. 역방향 의존 금지.
2. **credentials.yaml은 절대 커밋하지 않는다** — 로컬은 YAML, Railway는 환경변수. 코드에 하드코딩 금지.
3. **모든 네트워크 요청에 timeout을 설정한다** — feedparser 30초, requests 30초. 미설정 시 Railway 크론잡 24시간 stuck 재발.
4. **Notion API Rate Limit 준수** — 요청당 0.5초 딜레이. 병렬 호출 금지.
5. **AI 비용 최적화** — 2차 필터(관련성 평가)는 Haiku, 포스트 생성은 Sonnet. 모델 변경 시 비용 영향 확인 필수.
6. **소스 변경은 sources.yaml에서만** — RSS 피드 추가/삭제/키워드 변경은 코드 수정 없이 YAML로 관리.

## Key Files

```
ai-news-curator/
├── CLAUDE.md                    # 프로젝트 문서
├── AGENTS.md                    # 이 파일
├── ARCHITECTURE.md              # 시스템 아키텍처
├── docs/
│   ├── PRODUCT_SENSE.md         # 제품 방향
│   ├── PLANS.md                 # 우선순위, 로드맵
│   ├── design-docs/             # 설계 문서
│   └── exec-plans/              # 실행 계획
├── agents/
│   ├── orchestrator.py          # 전체 워크플로우 조율 (Step 1~6)
│   ├── collector/               # RSS 뉴스 수집
│   ├── analyzer/                # 콘텐츠 분석 (중요도, 카테고리, 태그)
│   ├── archiver/                # 뉴스 노션 저장
│   └── linkedin/                # LinkedIn 포스트 파이프라인
│       ├── filter.py            # 2단계 필터링 (키워드 + AI 관련성)
│       ├── generator.py         # Claude Sonnet 포스트 생성
│       └── post_archiver.py     # 포스트 노션 저장
├── config/
│   ├── sources.yaml             # RSS 피드 소스 (20개)
│   ├── linkedin.yaml            # LinkedIn 포스트 설정
│   ├── notion.yaml              # 뉴스 DB 스키마
│   └── credentials.yaml         # 인증 정보 (git 제외)
├── Dockerfile                   # Railway 배포용
├── railway.toml                 # Railway 크론 설정
└── requirements.txt
```

## Docs Map

| 문서 | 용도 | 변경 빈도 |
|------|------|-----------|
| [CLAUDE.md](CLAUDE.md) | 프로젝트 전체 컨텍스트, 실행 방법, 트러블슈팅 | 기능 추가/버그 수정 시 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 데이터 흐름, 모듈 경계, 에러 처리 | 모듈 구조 변경 시 |
| [docs/PRODUCT_SENSE.md](docs/PRODUCT_SENSE.md) | 제품 미션, 사용자, 핵심 가치 | 분기 1회 |
| [docs/PLANS.md](docs/PLANS.md) | 우선순위, 로드맵, 기술 부채 | 월 1회 |
| [config/sources.yaml](config/sources.yaml) | RSS 피드 소스 목록 | 소스 추가/삭제 시 |
| [config/linkedin.yaml](config/linkedin.yaml) | LinkedIn 포스트 생성 규칙 | 톤/구조 변경 시 |
