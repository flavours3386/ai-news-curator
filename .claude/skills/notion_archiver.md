# Notion Archiver Skill

분석된 뉴스 기사를 노션 데이터베이스에 저장합니다.

## 노션 API 설정

### 필요한 정보
- Integration Token: 노션 내부 연동 토큰
- Database ID: 저장할 데이터베이스 ID

### Integration 생성 방법
1. https://www.notion.so/my-integrations 접속
2. "New integration" 클릭
3. 이름 입력: "AI News Curator"
4. Capabilities: Read, Update, Insert content
5. 토큰 복사 (secret_xxx...)
6. 데이터베이스에서 연동 초대 (Share → Invite)

## 데이터베이스 속성 매핑

| 분석 결과 필드 | 노션 속성 | 타입 |
|----------------|-----------|------|
| title | Title | title |
| url | URL | url |
| source | Source | select |
| category | Category | select |
| importance | Importance | select |
| tags | Tags | multi_select |
| summary | Summary | rich_text |
| published_at | Published | date |
| (현재시간) | Archived | date |
| "📥 Inbox" | Status | select |
| language | Language | select |

## 기능
- URL 기반 중복 체크
- Rate Limit 방지 (0.5초 딜레이)
- 실패 시 3회 재시도
- 부분 성공 허용

## 사용 예시

```bash
# 노션에 저장
python -c "
from agents.archiver import NotionArchiver
import yaml

with open('config/credentials.yaml') as f:
    creds = yaml.safe_load(f)

archiver = NotionArchiver(creds['notion'])
articles = [...]  # 분석된 기사 목록
result = archiver.archive(articles)
print(f'Success: {result[\"success\"]}, Skipped: {result[\"skipped\"]}')
"
```
