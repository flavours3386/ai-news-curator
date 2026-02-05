import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from agents.collector.rss_collector import RSSCollector
from agents.analyzer.analyzer import ContentAnalyzer
from agents.archiver.notion_archiver import NotionArchiver


class Orchestrator:
    """전체 워크플로우 조율"""

    def __init__(self, config_dir: str = 'config'):
        self.config_dir = Path(config_dir)
        self.sources_config = self._load_yaml('sources.yaml')
        self.notion_config = self._load_yaml('notion.yaml')
        self.credentials = self._load_yaml('credentials.yaml')

        # 에이전트 초기화
        self.collector = RSSCollector(self.sources_config)
        self.analyzer = ContentAnalyzer()
        self.archiver = NotionArchiver({
            'integration_token': self.credentials['notion']['integration_token'],
            'database_id': self.credentials['notion']['database_id']
        })

    def _load_yaml(self, filename: str) -> Dict:
        """YAML 파일 로드"""
        path = self.config_dir / filename
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

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
