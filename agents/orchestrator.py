import os
import yaml
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from agents.collector.rss_collector import RSSCollector
from agents.analyzer.analyzer import ContentAnalyzer
from agents.archiver.notion_archiver import NotionArchiver
from agents.linkedin.filter import NewsFilter
from agents.linkedin.generator import PostGenerator
from agents.linkedin.post_archiver import PostArchiver


class Orchestrator:
    """전체 워크플로우 조율"""

    def __init__(self, config_dir: str = 'config'):
        self.config_dir = Path(config_dir)
        self.sources_config = self._load_yaml('sources.yaml')
        self.notion_config = self._load_yaml('notion.yaml')
        self.credentials = self._load_credentials()
        self.linkedin_config = self._load_yaml('linkedin.yaml')

        # 에이전트 초기화
        self.collector = RSSCollector(self.sources_config)
        self.analyzer = ContentAnalyzer()
        self.archiver = NotionArchiver({
            'integration_token': self.credentials['notion']['integration_token'],
            'database_id': self.credentials['notion']['database_id']
        })

        # LinkedIn 포스트 생성 에이전트 초기화
        api_key = self.credentials.get('anthropic', {}).get('api_key', '')
        linkedin_db_id = self.credentials.get('notion', {}).get('linkedin_database_id', '')

        self.linkedin_enabled = bool(api_key and linkedin_db_id)
        if self.linkedin_enabled:
            self.news_filter = NewsFilter(
                config=self.linkedin_config.get('filter', {}),
                api_key=api_key
            )
            self.post_generator = PostGenerator(
                config=self.linkedin_config,
                api_key=api_key
            )
            self.post_archiver = PostArchiver({
                'integration_token': self.credentials['notion']['integration_token'],
                'database_id': linkedin_db_id
            })

    def _load_yaml(self, filename: str) -> Dict:
        """YAML 파일 로드"""
        path = self.config_dir / filename
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_credentials(self) -> Dict:
        """credentials.yaml 또는 환경변수에서 인증 정보 로드"""
        cred_path = self.config_dir / 'credentials.yaml'

        # 1) 로컬: credentials.yaml 존재 시 yaml에서 로드
        if cred_path.exists():
            print("🔑 Loading credentials from credentials.yaml")
            with open(cred_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)

        # 2) Railway: 환경변수에서 로드
        notion_token = os.environ.get('NOTION_TOKEN')
        notion_db_id = os.environ.get('NOTION_DATABASE_ID')
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY')

        if notion_token and notion_db_id:
            print("🔑 Loading credentials from environment variables")
            return {
                'notion': {
                    'integration_token': notion_token,
                    'database_id': notion_db_id,
                    'linkedin_database_id': os.environ.get('NOTION_LINKEDIN_DATABASE_ID', ''),
                },
                'anthropic': {
                    'api_key': anthropic_key or '',
                },
            }

        # 3) 둘 다 없음 → 에러
        raise RuntimeError(
            "credentials.yaml not found and required environment variables are missing.\n"
            "Set NOTION_TOKEN, NOTION_DATABASE_ID, and ANTHROPIC_API_KEY as environment variables,\n"
            "or create config/credentials.yaml."
        )

    def run(self, hours_lookback: int = 24) -> Dict[str, Any]:
        """전체 워크플로우 실행"""
        print(f"\n{'='*50}")
        print(f"🚀 AI News Curator - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*50}\n")

        results = {
            'started_at': datetime.now().isoformat(),
            'steps': {}
        }

        # Step 1: 수집
        print("📡 Step 1: Collecting news...")
        collected = self.collector.collect(hours_lookback)
        results['steps']['collection'] = {
            'total': collected['total_count'],
            'sources': len(self.sources_config.get('rss_feeds', {}).get('english', []))
        }
        print(f"   ✓ Collected {collected['total_count']} articles\n")

        if collected['total_count'] == 0:
            print("   ⚠️ No articles collected. Exiting.")
            return results

        # Step 2: 분석
        print("🔍 Step 2: Analyzing content...")
        analyzed = self.analyzer.analyze(collected['articles'])

        importance_counts = {}
        for article in analyzed:
            imp = article['importance']
            importance_counts[imp] = importance_counts.get(imp, 0) + 1

        results['steps']['analysis'] = {
            'total': len(analyzed),
            'by_importance': importance_counts
        }
        print(f"   ✓ Analyzed {len(analyzed)} articles")
        for imp, count in importance_counts.items():
            print(f"     - {imp}: {count}")
        print()

        # Step 3: 저장
        print("💾 Step 3: Archiving to Notion...")
        archive_result = self.archiver.archive(analyzed)
        results['steps']['archive'] = archive_result
        print(f"   ✓ Success: {archive_result['success']}")
        print(f"   ✓ Skipped (duplicates): {archive_result['skipped']}")
        if archive_result['failed'] > 0:
            print(f"   ✗ Failed: {archive_result['failed']}")
        print()

        # Step 4~6: LinkedIn 포스트 생성 (설정된 경우)
        if self.linkedin_enabled:
            linkedin_start = time.time()

            # Step 4: 관련 뉴스 필터링
            print("🔍 Step 4: Filtering news for LinkedIn posts...")
            filtered = self.news_filter.filter(analyzed)
            results['steps']['linkedin_filter'] = {
                'input': len(analyzed),
                'output': len(filtered)
            }
            print(f"   ✓ Filtered {len(filtered)} relevant articles\n")

            if filtered:
                # Step 5: 포스트 생성
                print("✏️ Step 5: Generating LinkedIn posts...")
                posts = self.post_generator.generate(filtered)
                results['steps']['linkedin_generate'] = {
                    'generated': len(posts)
                }
                print(f"   ✓ Generated {len(posts)} posts\n")

                if posts:
                    # Step 6: 포스트 DB 저장
                    print("💾 Step 6: Archiving posts to Notion...")
                    post_archive_result = self.post_archiver.archive(posts)
                    results['steps']['linkedin_archive'] = post_archive_result
                    print(f"   ✓ Success: {post_archive_result['success']}")
                    if post_archive_result['failed'] > 0:
                        print(f"   ✗ Failed: {post_archive_result['failed']}")
                    print()
            else:
                print("   ⚠️ No relevant articles for LinkedIn posts. Skipping Steps 5~6.\n")

            linkedin_elapsed = time.time() - linkedin_start
            results['steps']['linkedin_elapsed'] = f"{linkedin_elapsed:.1f}s"
        else:
            print("⏭️ LinkedIn post generation skipped (API key or DB ID not configured)\n")

        # 완료
        results['finished_at'] = datetime.now().isoformat()
        print(f"{'='*50}")
        print("✅ Workflow completed!")
        print(f"{'='*50}\n")

        return results


def main():
    """메인 실행"""
    orchestrator = Orchestrator()
    results = orchestrator.run(hours_lookback=24)

    # 결과 저장
    Path('data/logs').mkdir(parents=True, exist_ok=True)
    with open('data/logs/last_run.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
