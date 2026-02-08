import json
import time
import logging
from typing import Dict, Any, List

import anthropic

logger = logging.getLogger(__name__)


class NewsFilter:
    """2단계 뉴스 필터링: 키워드 매칭 → Claude API 관련성 평가"""

    def __init__(self, config: Dict[str, Any], api_key: str):
        self.keywords = [kw.lower() for kw in config.get('keywords', [])]
        self.relevance_threshold = config.get('relevance_threshold', 7)
        self.client = anthropic.Anthropic(api_key=api_key)

    def filter(self, articles: List[Dict]) -> List[Dict]:
        """2단계 필터링 실행. 필터링된 기사 리스트 반환."""
        # 1차: 키워드 매칭
        keyword_matched = self._keyword_filter(articles)
        print(f"   📋 1차 키워드 필터: {len(articles)}건 → {len(keyword_matched)}건")

        if not keyword_matched:
            return []

        # 2차: Claude API 관련성 평가
        relevance_filtered = self._relevance_filter(keyword_matched)
        print(f"   🤖 2차 관련성 평가: {len(keyword_matched)}건 → {len(relevance_filtered)}건")

        # 관련성 점수 높은 순 정렬
        relevance_filtered.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        return relevance_filtered

    def _keyword_filter(self, articles: List[Dict]) -> List[Dict]:
        """1차 필터: 제목 + 요약 + 태그에서 키워드 매칭"""
        matched = []

        for article in articles:
            searchable = ' '.join([
                article.get('title', ''),
                article.get('summary', ''),
                article.get('excerpt', ''),
                ' '.join(article.get('tags', []))
            ]).lower()

            matched_keywords = [kw for kw in self.keywords if kw in searchable]

            if matched_keywords:
                article = article.copy()
                article['matched_keywords'] = matched_keywords
                article['keyword_match_count'] = len(matched_keywords)
                matched.append(article)

        # 매칭 수 기준 정렬
        matched.sort(key=lambda x: x['keyword_match_count'], reverse=True)
        return matched

    def _relevance_filter(self, articles: List[Dict]) -> List[Dict]:
        """2차 필터: Claude API로 관련성 평가 (Haiku 모델 사용)"""
        filtered = []

        for article in articles:
            try:
                score, reason = self._evaluate_relevance(article)
                article = article.copy()
                article['relevance_score'] = score
                article['relevance_reason'] = reason

                if score >= self.relevance_threshold:
                    filtered.append(article)
                    logger.info(f"  ✅ [{score}/10] {article['title'][:50]} - {reason}")
                else:
                    logger.info(f"  ❌ [{score}/10] {article['title'][:50]} - {reason}")

            except Exception as e:
                # API 호출 실패 시 1차 필터 결과 기준으로 포함
                logger.warning(f"  ⚠️ 관련성 평가 실패 ({article['title'][:40]}): {e}")
                article = article.copy()
                article['relevance_score'] = 5  # 기본값
                article['relevance_reason'] = f"평가 실패 (1차 필터 키워드 매칭: {article.get('keyword_match_count', 0)}건)"
                # 키워드 매칭 2개 이상이면 포함
                if article.get('keyword_match_count', 0) >= 2:
                    filtered.append(article)

            # Rate limit 방지
            time.sleep(0.3)

        return filtered

    def _evaluate_relevance(self, article: Dict) -> tuple:
        """Claude Haiku로 개별 기사 관련성 평가. (score, reason) 반환."""
        prompt = f"""다음 뉴스 기사가 B2B SaaS Sales/BizOps 실무자에게 링크드인 포스트로 작성할 만한 인사이트를 줄 수 있는지 평가해주세요.

제목: {article.get('title', '')}
요약: {article.get('summary', article.get('excerpt', ''))}
카테고리: {article.get('category', '')}
태그: {', '.join(article.get('tags', []))}
매칭 키워드: {', '.join(article.get('matched_keywords', []))}

0-10점으로 평가하고, 이유를 한 줄로 설명해주세요.
반드시 아래 JSON 형식으로만 응답하세요:
{{"score": 8, "reason": "CRM 자동화 트렌드와 직결"}}"""

        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()

        # JSON 파싱 (코드블록 감싸진 경우 처리)
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        result = json.loads(result_text)
        return int(result['score']), result['reason']
