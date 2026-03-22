import requests
from datetime import datetime
from typing import Dict, Any, List
import time


class NotionArchiver:
    """노션 데이터베이스에 뉴스 저장"""

    BASE_URL = "https://api.notion.com/v1"

    def __init__(self, config: Dict[str, Any]):
        self.token = config['integration_token']
        self.database_id = config['database_id']
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def archive(self, articles: List[Dict]) -> Dict[str, Any]:
        """기사 목록을 노션에 저장"""
        results = {
            'success': 0,
            'skipped': 0,
            'failed': 0,
            'errors': []
        }

        for article in articles:
            try:
                # 중복 체크
                if self._is_duplicate(article['url']):
                    results['skipped'] += 1
                    continue

                # 페이지 생성
                self._create_page(article)
                results['success'] += 1

                # Rate limit 방지
                time.sleep(0.5)

            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'title': article['title'],
                    'error': str(e)
                })

        return results

    def _is_duplicate(self, url: str) -> bool:
        """URL 기반 중복 체크"""
        query_url = f"{self.BASE_URL}/databases/{self.database_id}/query"

        payload = {
            "filter": {
                "property": "URL",
                "url": {
                    "equals": url
                }
            }
        }

        response = requests.post(query_url, headers=self.headers, json=payload, timeout=30)

        if response.status_code == 200:
            results = response.json().get('results', [])
            return len(results) > 0

        return False

    def _create_page(self, article: Dict) -> Dict:
        """노션 페이지 생성"""
        url = f"{self.BASE_URL}/pages"

        # 속성 매핑
        properties = {
            "이름": {
                "title": [{"text": {"content": article['title'][:100]}}]
            },
            "URL": {
                "url": article['url']
            },
            "Source": {
                "select": {"name": article['source']}
            },
            "Category": {
                "select": {"name": article.get('category', '💭 Opinion')}
            },
            "Importance": {
                "select": {"name": article.get('importance', '🟡 Medium')}
            },
            "Tags": {
                "multi_select": [{"name": tag} for tag in article.get('tags', [])[:5]]
            },
            "Summary": {
                "rich_text": [{"text": {"content": article.get('summary', '')[:2000]}}]
            },
            "Archived": {
                "date": {"start": datetime.utcnow().isoformat()}
            },
            "Status": {
                "select": {"name": "📥 Inbox"}
            },
            "Language": {
                "select": {"name": "🇺🇸 English" if article.get('language') == 'en' else "🇰🇷 Korean"}
            }
        }

        # Published 날짜 (있는 경우)
        if article.get('published_at'):
            properties["Published"] = {
                "date": {"start": article['published_at'][:10]}  # YYYY-MM-DD
            }

        # 본문 블록 생성
        children = self._create_content_blocks(article)

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
            "children": children
        }

        response = requests.post(url, headers=self.headers, json=payload, timeout=30)

        if response.status_code != 200:
            raise Exception(f"Failed to create page: {response.text}")

        return response.json()

    def _create_content_blocks(self, article: Dict) -> List[Dict]:
        """페이지 본문 블록 생성"""
        blocks = []

        # 요약 섹션
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "📝 Summary"}}]
            }
        })

        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": article.get('summary', 'No summary available.')}}]
            }
        })

        # 핵심 포인트 (있는 경우)
        if article.get('key_points'):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "🎯 Key Points"}}]
                }
            })

            for point in article['key_points']:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": point}}]
                    }
                })

        # 원문 링크
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🔗 Original Article"}}]
            }
        })

        blocks.append({
            "object": "block",
            "type": "bookmark",
            "bookmark": {
                "url": article['url']
            }
        })

        # 구분선
        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })

        # 메모 섹션
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "📝 My Notes"}}]
            }
        })

        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": ""}}]
            }
        })

        return blocks
