from typing import Dict, Any, List


class ContentAnalyzer:
    """뉴스 기사 분석"""

    # 중요도 키워드 가중치
    IMPORTANCE_KEYWORDS = {
        # 새 모델/제품 출시
        'launch': 2.0, 'release': 2.0, 'announce': 1.8, 'introduce': 1.8,
        'unveil': 2.0, 'debut': 1.8, 'new': 1.2,

        # 주요 모델명
        'gpt-5': 3.0, 'gpt-4': 2.0, 'claude': 2.5, 'gemini': 2.5,
        'llama': 2.0, 'mistral': 2.0,

        # 주요 기업
        'openai': 2.0, 'anthropic': 2.0, 'google': 1.8, 'meta': 1.8,
        'microsoft': 1.8, 'deepmind': 2.0,

        # 중요 이벤트
        'breakthrough': 2.5, 'funding': 1.8, 'acquisition': 2.0,
        'partnership': 1.5, 'regulation': 2.0, 'ban': 2.0,

        # 한국어
        '출시': 2.0, '발표': 1.8, '공개': 1.8, '혁신': 2.5, '규제': 2.0
    }

    # 카테고리 키워드
    CATEGORY_KEYWORDS = {
        '🔬 Research': ['paper', 'study', 'research', 'arxiv', 'experiment', 'benchmark', '논문', '연구'],
        '🚀 Product': ['launch', 'release', 'update', 'beta', 'version', 'api', '출시', '업데이트'],
        '💼 Business': ['funding', 'acquisition', 'ipo', 'startup', 'investment', 'valuation', '투자', '인수'],
        '⚖️ Policy': ['regulation', 'law', 'government', 'policy', 'ban', 'legislation', '규제', '정책'],
        '🔓 OpenSource': ['github', 'open source', 'mit license', 'apache', 'release', '오픈소스'],
        '🎓 Tutorial': ['how to', 'guide', 'tutorial', 'course', 'learn', '가이드', '튜토리얼'],
        '💭 Opinion': ['opinion', 'analysis', 'perspective', 'think', 'believe', '의견', '분석']
    }

    # 소스별 신뢰도
    SOURCE_CREDIBILITY = {
        'MIT Technology Review': 10, 'Nature': 10, 'Science': 10,
        'TechCrunch': 9, 'TechCrunch AI': 9, 'The Verge': 8, 'The Verge AI': 8,
        'Wired': 8, 'Wired AI': 8,
        'VentureBeat': 8, 'VentureBeat AI': 8, 'Ars Technica': 8,
        'OpenAI Blog': 9, 'Anthropic News': 9, 'Google AI Blog': 9,
        'AI 타임스': 7, '전자신문': 7, '전자신문 AI': 7,
        'Hacker News': 7, 'Reddit': 6
    }

    def analyze(self, articles: List[Dict]) -> List[Dict]:
        """기사 목록 분석"""
        analyzed = []
        for article in articles:
            analyzed_article = self._analyze_article(article)
            analyzed.append(analyzed_article)

        # 중요도 순 정렬
        analyzed.sort(key=lambda x: x['importance_score'], reverse=True)
        return analyzed

    def _analyze_article(self, article: Dict) -> Dict:
        """개별 기사 분석"""
        text = f"{article['title']} {article.get('excerpt', '')}".lower()

        # 중요도 점수 계산
        importance_score = self._calculate_importance(text, article['source'])
        importance_label = self._score_to_label(importance_score)

        # 카테고리 분류
        category = self._classify_category(text)

        # 태그 추출
        tags = self._extract_tags(text)

        # 요약 생성 (실제로는 Claude API 호출)
        summary = article.get('excerpt', '')[:200] + '...'

        return {
            **article,
            'importance': importance_label,
            'importance_score': round(importance_score, 1),
            'category': category,
            'tags': tags,
            'summary': summary,
            'key_points': []  # Claude가 생성
        }

    def _calculate_importance(self, text: str, source: str) -> float:
        """중요도 점수 계산"""
        score = 5.0  # 기본 점수

        # 키워드 기반 점수
        for keyword, weight in self.IMPORTANCE_KEYWORDS.items():
            if keyword in text:
                score += weight

        # 소스 신뢰도 반영
        credibility = self.SOURCE_CREDIBILITY.get(source, 5)
        score = score * 0.7 + credibility * 0.3

        return min(score, 10.0)

    def _score_to_label(self, score: float) -> str:
        """점수를 레이블로 변환"""
        if score >= 8.5:
            return '🔴 Critical'
        elif score >= 7.0:
            return '🟠 High'
        elif score >= 5.0:
            return '🟡 Medium'
        else:
            return '⚪ Low'

    def _classify_category(self, text: str) -> str:
        """카테고리 분류"""
        max_score = 0
        best_category = '💭 Opinion'  # 기본값

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > max_score:
                max_score = score
                best_category = category

        return best_category

    def _extract_tags(self, text: str) -> List[str]:
        """태그 추출"""
        tags = []

        # 회사명
        companies = ['OpenAI', 'Anthropic', 'Google', 'Meta', 'Microsoft', 'DeepMind', 'Nvidia']
        for company in companies:
            if company.lower() in text:
                tags.append(company)

        # 모델명
        models = ['GPT', 'Claude', 'Gemini', 'Llama', 'Mistral', 'DALL-E', 'Midjourney', 'Stable Diffusion']
        for model in models:
            if model.lower() in text:
                tags.append(model)

        # 기술
        techs = ['LLM', 'RAG', 'Fine-tuning', 'Vision', 'Multimodal', 'Agents', 'API']
        for tech in techs:
            if tech.lower() in text:
                tags.append(tech)

        return list(set(tags))[:5]  # 최대 5개
