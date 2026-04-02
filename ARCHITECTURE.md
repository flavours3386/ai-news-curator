# AI News Curator + LinkedIn Post Generator - Architecture

## 시스템 개요

RSS/API 기반 뉴스 수집 -> AI 분석/필터링 -> 노션 아카이빙 -> LinkedIn 포스트 자동 생성까지의 6단계 순차 파이프라인. Railway Cron으로 매일 KST 06:00 자동 실행.

## 데이터 흐름

```
[RSS 피드 20개]           [Hacker News API]
       |                        |
       +-------+  +-------------+
               |  |
         [Step 1: collector]
          RSS 파싱 + 24h 필터
          content_keywords 1차 필터링
          bypass_content_filter 소스는 전량 통과
               |
         [Step 2: analyzer]
          Claude 기반 분석
          중요도 / 카테고리 / 태그 자동 분류
               |
         [Step 3: archiver]
          Notion 뉴스 DB 저장
          중복 URL 체크 → 스킵
          요청당 0.5초 딜레이
               |
         [Step 4: linkedin/filter]
          1차: 키워드 매칭 (43개)
          2차: Claude Haiku 관련성 평가 (7/10 기준)
               |
         [Step 5: linkedin/generator]
          Claude Sonnet 포스트 생성
          1회 최대 3개, 본문 1800자 제한
          hook → context → my_take → closing → hashtags
               |
         [Step 6: linkedin/post_archiver]
          Notion LinkedIn Posts DB 저장
          Status: "초안"
```

## 모듈 경계

| 모듈 | 파일 | 역할 |
|------|------|------|
| orchestrator | `agents/orchestrator.py` | Step 1~6 순차 실행, 에러 시 해당 Step만 실패 처리 |
| collector | `agents/collector/` | RSS 수집, 24시간 이내 기사 필터링, content_keywords 매칭 |
| analyzer | `agents/analyzer/` | Claude API로 중요도/카테고리/태그 분석 |
| archiver | `agents/archiver/` | Notion 뉴스 DB CRUD, URL 중복 검사 |
| filter | `agents/linkedin/filter.py` | 2단계 필터링: 키워드 -> AI 관련성 (Haiku) |
| generator | `agents/linkedin/generator.py` | Claude Sonnet으로 포스트 본문 생성 |
| post_archiver | `agents/linkedin/post_archiver.py` | Notion 포스트 DB 저장 |
| config | `config/*.yaml` | 소스/인증/스키마/포스트 설정 (코드 수정 없이 변경) |

## 에러 처리 전략

| 상황 | 처리 방식 |
|------|-----------|
| RSS 피드 무응답 | `socket.setdefaulttimeout(30)` + ThreadPoolExecutor 타임아웃 |
| Notion API 429 | 요청당 0.5초 딜레이로 사전 방지 |
| Notion API 요청 실패 | `requests.post(timeout=30)` + 개별 기사 실패 시 로깅 후 계속 |
| Claude API 실패 | 해당 기사 스킵, 로그에 기록 |
| LinkedIn DB ID 미설정 | Step 4~6 전체 스킵 (뉴스 수집만 실행) |
| 전체 파이프라인 예외 | orchestrator try/catch에서 에러 로깅 후 종료 |

## 제약사항

- **Notion API Rate Limit**: 초당 3건 권장. 0.5초 딜레이로 대응하지만 대량 수집 시 초과 가능.
- **Anthropic API 비용**: Haiku 필터(저비용) + Sonnet 생성(고비용). 일 1회 실행 기준 월 ~$5 이내.
- **RSS 피드 안정성**: 일부 피드는 간헐적 무응답. 30초 timeout으로 전체 파이프라인 blocking 방지.
- **Railway Cron 특성**: 크론잡이 24시간 이내에 종료되지 않으면 강제 종료됨.
- **인증 이중 경로**: 로컬(credentials.yaml) vs Railway(환경변수). 코드에서 YAML 우선 -> 환경변수 폴백 순서 유지.
