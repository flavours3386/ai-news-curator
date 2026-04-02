# AI News Curator + LinkedIn Post Generator - Plans

> 최종 업데이트: 2026-04-02

## 현재 우선순위

1. Railway 크론잡 안정 운영 유지 (일 1회 KST 06:00 자동 실행)
2. RSS 소스 품질 관리 (비활성/무응답 피드 교체)
3. LinkedIn 포스트 품질 개선 (프롬프트 튜닝)

## 로드맵

### Phase 1: 핵심 파이프라인 (완료)
- RSS 수집 20개 피드 + content_keywords 필터링
- Claude 기반 분석 (중요도/카테고리/태그)
- Notion 뉴스 DB 아카이빙
- LinkedIn 포스트 2단계 필터 + Sonnet 생성
- Railway Cron 배포

### Phase 2: 안정화 (완료)
- timeout 전면 적용 (feedparser 30초, requests 30초)
- ThreadPoolExecutor 타임아웃 처리
- Dockerfile `python -u` 추가 (stdout 실시간 출력)
- 순환 import 제거

### Phase 3: 확장 (미정)
- X(Twitter) 포스트 생성 (280자 별도 로직)
- 포스트 품질 피드백 루프 (게시 후 반응 데이터 수집)
- 멀티 언어 포스트 (영문 옵션)

## 기술적 의사결정

### 왜 feedparser인가?
- Python RSS 파싱의 사실상 표준. 다양한 피드 형식(RSS 2.0, Atom, RDF) 자동 처리.
- 단점: 내부 urllib에 socket timeout이 없어 `socket.setdefaulttimeout(30)` 필요.

### 왜 Haiku + Sonnet 분리인가?
- 2차 필터(관련성 평가)는 단순 판단 -> Haiku로 충분 (비용 1/10).
- 포스트 생성은 창의적 작문 -> Sonnet 필요.
- 월 비용 ~$5 이내 유지 가능.

### 왜 Railway Cron인가?
- GitHub Actions는 크론 정확도가 낮고 실행 시간 제한(6시간).
- Railway는 Docker 기반으로 환경 일관성 보장, 크론 정확도 높음.

## 기술 부채

| 항목 | 심각도 | 설명 |
|------|--------|------|
| 테스트 부재 | MEDIUM | agents/ 모듈에 단위 테스트 없음. RSS 파싱/필터링 로직 테스트 필요. |
| 에러 알림 없음 | LOW | 파이프라인 실패 시 로그만 남김. Slack/Telegram 알림 추가 고려. |
| Notion API 버전 고정 | LOW | 현재 버전에서 동작하지만, 향후 deprecation 대응 필요. |
