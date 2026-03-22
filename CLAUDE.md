# AI News Curator + LinkedIn Post Generator

## 프로젝트 소개

AI, B2B SaaS, Martech, E-commerce 관련 최신 뉴스를 자동으로 수집하여 노션에 아카이빙하고, B2B Sales/BizOps 관점의 LinkedIn 포스트를 자동 생성하는 에이전트입니다.

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

## RSS 소스 현황 (20개)

`config/sources.yaml`에서 관리. 총 20개 피드가 검증 완료되어 운영 중:

| 카테고리 | 피드 수 | 소스 |
|----------|---------|------|
| AI / Tech 미디어 | 5 | TechCrunch AI, MIT Tech Review, The Verge AI, Ars Technica, Wired AI |
| AI 기업 블로그 | 2 | OpenAI, Google AI |
| B2B SaaS / Sales / RevOps | 5 | SaaStr(H), HubSpot Sales(H), Salesforce(H), Pavilion, Close CRM |
| Martech / Marketing | 3 | MarTech, ChiefMartec, Marketing Brew |
| E-commerce | 2 | Practical Ecommerce, Digital Commerce 360 |
| General Business | 1 | First Round Review |
| 한국 미디어 | 2 | AI 타임스(H), 전자신문 AI |

- **(H)** = high priority
- Hacker News API: `"AI OR LLM OR GPT OR SaaS OR B2B Sales OR RevOps OR Martech"` 쿼리 사용

### 수집 필터 (content_keywords)

`sources.yaml`의 `content_keywords`로 수집 단계에서 1차 필터링. AI/ML 키워드(25개) + B2B SaaS/Sales/RevOps(33개) + Martech(7개) + E-commerce(7개) 총 72개 키워드 운영 중.

**선정 소스 bypass**: B2B SaaS, Martech, E-commerce, General Business 카테고리 피드(11개)는 `bypass_content_filter: true`로 설정되어 키워드 무관하게 모든 기사가 수집됨. AI/Tech 미디어와 한국 미디어만 키워드 필터 적용.

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
├── Dockerfile            # Railway 배포용 컨테이너
├── railway.toml          # Railway 빌드/배포/크론 설정
├── .dockerignore         # Docker 빌드 제외 파일
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

- **filter.keywords** — 1차 필터링 키워드 43개 (기존 19개 + B2B SaaS/Martech/E-commerce 24개 추가)
- **filter.relevance_threshold** — 2차 AI 관련성 평가 기준 (기본 7/10)
- **generation.max_posts_per_run** — 1회 최대 생성 수 (기본 3)
- **generation.max_length** — 본문 최대 길이 (기본 1800자)
- **profile** — 작성자 프로필, 경력, 전문분야
- **post_structure** — 포스트 구조 (hook → context → my_take → closing → source_link → hashtags)
- **writing_rules** — 작성 규칙

## Railway 배포

### 개요

Railway Cron Job으로 매일 자동 실행됩니다. `credentials.yaml` 없이 환경변수만으로 동작하도록 fallback 로직이 구현되어 있습니다.

### 배포 구조

- **Dockerfile** — `python:3.11-slim` 기반, `requirements.txt` 설치 후 orchestrator 실행
- **railway.toml** — Dockerfile 빌더 사용, 크론 스케줄 설정
- **크론 스케줄** — `0 21 * * *` (UTC 21:00 = KST 06:00, 매일 아침 실행)

### 환경변수 설정

Railway Dashboard → Variables에서 아래 환경변수를 설정합니다:

| 환경변수 | 필수 | 설명 |
|----------|------|------|
| `NOTION_TOKEN` | Y | 노션 Integration Token |
| `NOTION_DATABASE_ID` | Y | 뉴스 DB ID |
| `ANTHROPIC_API_KEY` | Y | Anthropic API 키 |
| `NOTION_LINKEDIN_DATABASE_ID` | N | LinkedIn Posts DB ID (없으면 포스트 생성 스킵) |

### 인증 정보 로드 순서

1. `config/credentials.yaml` 파일이 존재하면 YAML에서 로드 (로컬 개발)
2. YAML 없으면 환경변수에서 로드 (Railway 배포)
3. 둘 다 없으면 `RuntimeError` 발생

### 배포 방법

```bash
# 1. Railway CLI 설치 및 로그인
npm install -g @railway/cli
railway login

# 2. 프로젝트 연결
railway link

# 3. 환경변수 설정
railway variables set NOTION_TOKEN=xxx
railway variables set NOTION_DATABASE_ID=xxx
railway variables set ANTHROPIC_API_KEY=xxx
railway variables set NOTION_LINKEDIN_DATABASE_ID=xxx

# 4. 배포
railway up
```

## 주의사항

- `config/credentials.yaml`은 절대 커밋하지 마세요
- 노션 API Rate Limit: 요청당 0.5초 딜레이 적용됨
- Anthropic API 비용: 2차 필터는 Haiku(저비용), 포스트 생성은 Sonnet 사용
- 반드시 프로젝트 디렉토리에서 실행해야 합니다 (`config/` 상대경로 참조)

## 트러블슈팅

### Railway 크론잡 24시간 stuck 현상 (2025-02-25 ~ 2026-03-22)

**증상**: 크론잡이 24시간 동안 종료되지 않고 Running 상태 유지. 노션 DB에 데이터 미적재. Deploy Logs에 "Starting Container"만 표시.

**원인**: RSS 피드 서버의 간헐적 무응답 + 모든 네트워크 요청에 timeout 미설정.
- `feedparser.parse()`는 내부적으로 urllib 사용하며 기본 socket timeout이 없음
- `requests.post()`도 timeout 미지정 시 무한 대기
- ThreadPoolExecutor에서 1개 피드라도 hanging되면 `as_completed()` 전체가 blocking
- Dockerfile에서 `python -u` 미사용으로 stdout 버퍼링 → Railway 로그 미출력

**수정 내용**:
- `rss_collector.py`: `socket.setdefaulttimeout(30)` 추가
- `notion_archiver.py`: `requests.post()` 2곳에 `timeout=30` 추가
- `post_archiver.py`: `requests.post()`에 `timeout=30` 추가
- `Dockerfile`: `python -u` 플래그 추가 (stdout 실시간 출력)
- `agents/__init__.py`: 순환 import 제거 (`python -m agents.orchestrator` 실행 시 RuntimeWarning 해소)
