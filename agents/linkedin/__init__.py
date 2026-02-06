from .filter import NewsFilter
from .generator import PostGenerator
from .post_archiver import PostArchiver

__all__ = ['NewsFilter', 'PostGenerator', 'PostArchiver']


class LinkedInPostGenerator:
    """LinkedIn 포스트 생성 파이프라인 (필터 → 생성 → 저장)"""

    def __init__(self, linkedin_config, credentials):
        api_key = credentials['anthropic']['api_key']

        self.news_filter = NewsFilter(
            config=linkedin_config.get('filter', {}),
            api_key=api_key
        )
        self.post_generator = PostGenerator(
            config=linkedin_config,
            api_key=api_key
        )
        self.post_archiver = PostArchiver({
            'integration_token': credentials['notion']['integration_token'],
            'database_id': credentials['notion']['linkedin_database_id']
        })

    def run(self, articles):
        """필터링 → 생성 → 저장 전체 파이프라인 실행"""
        # Step 1: 필터링
        filtered = self.news_filter.filter(articles)
        if not filtered:
            return {'filtered': 0, 'generated': 0, 'archived': {}}

        # Step 2: 포스트 생성
        posts = self.post_generator.generate(filtered)

        # Step 3: 노션 저장
        archive_result = self.post_archiver.archive(posts)

        return {
            'filtered': len(filtered),
            'generated': len(posts),
            'archived': archive_result
        }
