import feedparser
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import re


class RSSCollector:
    """RSS 피드에서 뉴스 수집"""

    # 기본 키워드 (config에 content_keywords가 없을 때 fallback)
    DEFAULT_KEYWORDS = [
        'ai', 'artificial intelligence', 'machine learning', 'deep learning',
        'neural network', 'llm', 'large language model', 'gpt', 'claude',
        'gemini', 'llama', 'transformer', 'diffusion', 'generative',
        'chatgpt', 'openai', 'anthropic', 'deepmind',
        '인공지능', '머신러닝', '딥러닝', '생성형'
    ]

    def __init__(self, config: Dict[str, Any]):
        self.feeds = config.get('rss_feeds', {})
        self.filters = config.get('filters', {})
        self.content_keywords = config.get('content_keywords', self.DEFAULT_KEYWORDS)

    def collect(self, hours_lookback: int = 24) -> Dict[str, Any]:
        """모든 RSS 피드에서 뉴스 수집"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_lookback)
        all_articles = []

        # 모든 피드 URL 수집
        feed_configs = []
        for lang, feeds in self.feeds.items():
            for feed in feeds:
                feed_copy = feed.copy()
                feed_copy['language'] = lang[:2]  # 'english' -> 'en'
                feed_configs.append(feed_copy)

        # 병렬 수집
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(self._fetch_feed, feed, cutoff_time): feed
                for feed in feed_configs
            }

            for future in as_completed(futures):
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                except Exception as e:
                    feed = futures[future]
                    print(f"Error fetching {feed['name']}: {e}")

        # 중복 제거
        unique_articles = self._deduplicate(all_articles)

        # 콘텐츠 키워드 기반 필터링
        filtered_articles = self._filter_by_keywords(unique_articles)

        return {
            'collected_at': datetime.utcnow().isoformat(),
            'total_count': len(filtered_articles),
            'articles': filtered_articles
        }

    def _fetch_feed(self, feed_config: Dict, cutoff_time: datetime) -> List[Dict]:
        """개별 피드 수집"""
        feed = feedparser.parse(feed_config['url'])
        articles = []

        for entry in feed.entries:
            published = self._parse_date(entry.get('published', entry.get('updated', '')))

            # 시간 필터링
            if published and published < cutoff_time:
                continue

            article = {
                'id': self._generate_id(entry.link),
                'title': self._clean_text(entry.title),
                'url': entry.link,
                'source': feed_config['name'],
                'published_at': published.isoformat() if published else None,
                'author': entry.get('author', ''),
                'excerpt': self._clean_text(entry.get('summary', '')[:500]),
                'image_url': self._extract_image(entry),
                'language': feed_config.get('language', 'en'),
                'priority': feed_config.get('priority', 'medium')
            }
            articles.append(article)

        return articles

    def _generate_id(self, url: str) -> str:
        """URL 기반 고유 ID 생성"""
        return hashlib.md5(url.encode()).hexdigest()

    def _deduplicate(self, articles: List[Dict]) -> List[Dict]:
        """URL 기반 중복 제거"""
        seen = set()
        unique = []
        for article in articles:
            if article['id'] not in seen:
                seen.add(article['id'])
                unique.append(article)
        return unique

    def _filter_by_keywords(self, articles: List[Dict]) -> List[Dict]:
        """콘텐츠 키워드 기반 필터링 (AI + B2B SaaS + Martech + E-commerce)"""
        filtered = []
        for article in articles:
            text = f"{article['title']} {article['excerpt']}".lower()
            if any(keyword in text for keyword in self.content_keywords):
                filtered.append(article)
        return filtered

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열 파싱 (timezone-naive로 변환)"""
        if not date_str:
            return None
        try:
            from dateutil import parser
            parsed = parser.parse(date_str)
            # timezone-aware인 경우 UTC로 변환 후 timezone 제거
            if parsed.tzinfo is not None:
                from datetime import timezone
                parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        except Exception:
            return None

    def _clean_text(self, text: str) -> str:
        """HTML 태그 제거 및 텍스트 정리"""
        if not text:
            return ""
        # HTML 태그 제거
        clean = re.sub(r'<[^>]+>', '', text)
        # 연속 공백 제거
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()

    def _extract_image(self, entry) -> str:
        """이미지 URL 추출"""
        # media:content
        if hasattr(entry, 'media_content') and entry.media_content:
            return entry.media_content[0].get('url', '')
        # enclosure
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enc in entry.enclosures:
                if enc.get('type', '').startswith('image'):
                    return enc.get('href', '')
        return ''
