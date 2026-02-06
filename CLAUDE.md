# AI News Curator + LinkedIn Post Generator

## 프로젝트 소개

AI 관련 최신 뉴스를 자동으로 수집하여 노션에 아카이빙하고, B2B Sales/BizOps 관점의 LinkedIn 포스트를 자동 생성하는 에이전트입니다.

## 빠른 시작

```bash
# 1. 설정
./scripts/setup.sh

# 2. credentials.yaml 수정
#    - 노션 토큰, 뉴스 DB ID
#    - Anthropic API 키
#    - LinkedIn Posts DB ID

# 3. 실행
cd ~/Desktop/PJT/02.AI-News_curator
./venv/bin/python -m agents.orchestrator
```

## 주요 명령어

```bash
# 전체 워크플로우 실행 (뉴스 수집 → 분석 → 저장 → LinkedIn 포스트 생성)
./venv/bin/python -m agents.orchestrator

# LinkedIn 포스트 단계별 테스트
./venv/bin/python scripts/test_linkedin.py --step filter    # 뉴스 필터링
./venv/bin/python scripts/test_linkedin.py --step generate  # 포스트 생성
./venv/bin/python scripts/test_linkedin.py --step archive   # 노션 저장
./venv/bin/python scripts/test_linkedin.py --step full      # 전체 파이프라인
```

## 데이터 흐름

```
RSS/API → 수집 → 분석 → 뉴스 DB 저장 → 키워드 필터 → AI 관련성 평가 → 포스트 생성 → 포스트 DB 저장
         (24h)  (분석)   (Notion)      (1차 필터)    (Claude Haiku)    (Claude Sonnet)  (Notion)
```

## 파일 구조

```
02.AI-News_curator/
├── agents/
│   ├── collector/        # RSS 뉴스 수집
│   ├── analyzer/         # 콘텐츠 분석 (중요도, 카테고리, 태그)
│   ├── archiver/         # 뉴스 노션 저장
│   ├── linkedin/         # LinkedIn 포스트 생성
│   │   ├── filter.py     # 2단계 필터링 (키워드 + AI 관련성)
│   │   ├── generator.py  # Claude API 포스트 생성
│   │   └── post_archiver.py  # 포스트 노션 저장
│   └── orchestrator.py   # 전체 워크플로우 조율 (Step 1~6)
├── config/
│   ├── credentials.yaml       # 인증 정보 (git 제외)
│   ├── credentials.yaml.example
│   ├── sources.yaml           # RSS 피드 소스
│   ├── notion.yaml            # 뉴스 DB 스키마
│   └── linkedin.yaml          # LinkedIn 포스트 설정 (프로필, 톤, 구조, 필터 키워드)
├── scripts/
│   ├── test_linkedin.py  # LinkedIn 단계별 테스트
│   ├── setup.sh
│   └── run.sh
├── data/                 # 캐시, 로그
└── requirements.txt
```

## 노션 데이터베이스

### 뉴스 DB

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

### LinkedIn Posts DB

| 속성 | 타입 | 설명 |
|------|------|------|
| Title | title | 포스트 제목 |
| Post Body | rich_text | 포스트 본문 |
| Source URL | url | 원문 뉴스 링크 |
| Source Title | rich_text | 원문 뉴스 제목 |
| Category | select | 카테고리 |
| Hashtags | multi_select | 해시태그 |
| Status | select | 기본값 "📝 초안" |
| Created | date | 생성일 |
| Publish Date | date | 게시일 (수동) |

## LinkedIn 포스트 설정

`config/linkedin.yaml`에서 코드 수정 없이 조정 가능:

- **filter.keywords** — 1차 필터링 키워드 목록
- **filter.relevance_threshold** — 2차 AI 관련성 평가 기준 (기본 7/10)
- **generation.max_posts_per_run** — 1회 최대 생성 수 (기본 3)
- **generation.max_length** — 본문 최대 길이 (기본 1800자)
- **profile** — 작성자 프로필, 경력, 전문분야
- **post_structure** — 포스트 구조 (hook → context → my_take → closing → source_link → hashtags)
- **writing_rules** — 작성 규칙

## 주의사항

- `config/credentials.yaml`은 절대 커밋하지 마세요
- 노션 API Rate Limit: 요청당 0.5초 딜레이 적용됨
- Anthropic API 비용: 2차 필터는 Haiku(저비용), 포스트 생성은 Sonnet 사용
- 반드시 프로젝트 디렉토리에서 실행해야 합니다 (`config/` 상대경로 참조)
