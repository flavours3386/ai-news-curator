import requests
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PostArchiver:
    """생성된 LinkedIn 포스트를 노션 DB에 저장"""

    BASE_URL = "https://api.notion.com/v1"
    MAX_RETRIES = 3

    def __init__(self, config: Dict[str, Any]):
        self.token = config['integration_token']
        self.database_id = config['database_id']
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def archive(self, posts: List[Dict]) -> Dict[str, Any]:
        """포스트 목록을 노션에 저장"""
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }

        for post in posts:
            success = False
            last_error = None

            for attempt in range(1, self.MAX_RETRIES + 1):
                try:
                    page = self._create_page(post)
                    results['success'] += 1
                    page_url = page.get('url', 'N/A')
                    logger.info(f"  ✅ 저장 완료: {post.get('title', '')[:40]} → {page_url}")
                    success = True
                    break
                except Exception as e:
                    last_error = e
                    if attempt < self.MAX_RETRIES:
                        logger.warning(f"  ⚠️ 저장 재시도 {attempt}/{self.MAX_RETRIES}: {e}")
                        time.sleep(1)

            if not success:
                results['failed'] += 1
                error_info = {
                    'title': post.get('title', ''),
                    'error': str(last_error)
                }
                results['errors'].append(error_info)
                print(f"   ❌ 저장 실패: {post.get('title', '')[:40]}")
                print(f"      본문 미리보기: {post.get('body', '')[:100]}...")

            # Rate limit 방지
            time.sleep(0.5)

        return results

    def _create_page(self, post: Dict) -> Dict:
        """노션 페이지 생성"""
        url = f"{self.BASE_URL}/pages"

        # rich_text 2000자 제한 처리 - 본문을 여러 블록으로 분할
        body_text = post.get('body', '')

        properties = {
            "Title": {
                "title": [{"text": {"content": post.get('title', '')[:100]}}]
            },
            "Post Body": {
                "rich_text": [{"text": {"content": body_text[:2000]}}]
            },
            "Source URL": {
                "url": post.get('source_url', '') or None
            },
            "Source Title": {
                "rich_text": [{"text": {"content": post.get('source_title', '')[:2000]}}]
            },
            "Category": {
                "select": {"name": post.get('category', 'General')}
            },
            "Hashtags": {
                "multi_select": [
                    {"name": tag[:100]} for tag in post.get('hashtags', [])[:10]
                ]
            },
            "Status": {
                "select": {"name": "📝 초안"}
            },
            "Created": {
                "date": {"start": datetime.utcnow().isoformat()}
            }
        }

        # Source URL이 빈 문자열이면 제거 (Notion API는 빈 URL 거부)
        if not post.get('source_url'):
            properties.pop('Source URL', None)

        # 본문 블록 생성
        children = self._create_content_blocks(post)

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
            "children": children
        }

        response = requests.post(url, headers=self.headers, json=payload, timeout=30)

        if response.status_code != 200:
            raise Exception(f"Notion API 에러 ({response.status_code}): {response.text[:300]}")

        return response.json()

    def _create_content_blocks(self, post: Dict) -> List[Dict]:
        """페이지 본문 블록 생성"""
        blocks = []
        body_text = post.get('body', '')

        # 본문을 줄바꿈 기준으로 블록 분할
        paragraphs = body_text.split('\n')

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 2000자 제한 처리
            while para:
                chunk = para[:2000]
                para = para[2000:]
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": chunk}}]
                    }
                })

        # 구분선
        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })

        # 첫 번째 댓글용 출처 링크 (복사해서 바로 붙여넣기)
        if post.get('source_url'):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"text": {"content": "💬 첫 번째 댓글용 출처 링크"}}]
                }
            })
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "icon": {"emoji": "📎"},
                    "rich_text": [{"text": {"content": post['source_url']}}]
                }
            })

        return blocks
