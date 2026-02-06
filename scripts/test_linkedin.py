#!/usr/bin/env python3
"""LinkedIn 포스트 생성 파이프라인 단계별 테스트 스크립트

Usage:
    python scripts/test_linkedin.py --step filter     # 1차/2차 필터링 테스트
    python scripts/test_linkedin.py --step generate   # 포스트 생성 테스트
    python scripts/test_linkedin.py --step archive    # 노션 저장 테스트
    python scripts/test_linkedin.py --step full       # 전체 파이프라인 테스트
"""

import sys
import os
import argparse
import yaml
import json
import time
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.linkedin.filter import NewsFilter
from agents.linkedin.generator import PostGenerator
from agents.linkedin.post_archiver import PostArchiver
from agents.linkedin import LinkedInPostGenerator


def load_config():
    """설정 파일 로드"""
    config_dir = project_root / 'config'

    with open(config_dir / 'credentials.yaml', 'r', encoding='utf-8') as f:
        credentials = yaml.safe_load(f)

    with open(config_dir / 'linkedin.yaml', 'r', encoding='utf-8') as f:
        linkedin_config = yaml.safe_load(f)

    return credentials, linkedin_config


def get_sample_articles():
    """테스트용 샘플 뉴스 기사"""
    return [
        {
            'title': 'Salesforce Launches AI-Powered CRM Automation Suite',
            'url': 'https://example.com/salesforce-ai-crm',
            'source': 'TechCrunch AI',
            'summary': 'Salesforce has unveiled a new AI-powered suite that automates CRM workflows, '
                       'pipeline management, and lead scoring. The tool integrates with existing '
                       'Sales Cloud and aims to reduce manual data entry by 80%.',
            'excerpt': 'Salesforce unveils AI CRM automation suite for B2B sales teams.',
            'category': '🚀 Product',
            'tags': ['Salesforce', 'CRM', 'AI', 'Sales Automation', 'B2B'],
            'importance': '🟠 High',
            'published_at': '2025-01-15T09:00:00',
            'language': 'en'
        },
        {
            'title': 'HubSpot Report: B2B SaaS Companies Adopting PLG See 30% Lower CAC',
            'url': 'https://example.com/hubspot-plg-report',
            'source': 'VentureBeat AI',
            'summary': 'A new report from HubSpot reveals that B2B SaaS companies with '
                       'Product-Led Growth strategies have 30% lower customer acquisition costs '
                       'and 2x higher retention rates compared to sales-led peers.',
            'excerpt': 'PLG adoption reduces CAC by 30% for B2B SaaS companies.',
            'category': '💼 Business',
            'tags': ['HubSpot', 'PLG', 'SaaS', 'B2B Sales', 'CAC', 'Retention'],
            'importance': '🟠 High',
            'published_at': '2025-01-14T14:00:00',
            'language': 'en'
        },
        {
            'title': 'New Study Shows 65% of Sales Teams Now Use AI for Lead Generation',
            'url': 'https://example.com/ai-lead-generation',
            'source': 'MIT Technology Review',
            'summary': 'A comprehensive study of 500 B2B companies shows that AI-powered lead '
                       'generation tools have become mainstream, with adoption jumping from 20% '
                       'to 65% in just two years. Pipeline conversion rates improved by 40%.',
            'excerpt': 'AI lead generation adoption hits 65% among B2B sales teams.',
            'category': '💼 Business',
            'tags': ['AI', 'Lead Generation', 'B2B Sales', 'Pipeline', 'Sales Productivity'],
            'importance': '🔴 Critical',
            'published_at': '2025-01-13T10:00:00',
            'language': 'en'
        },
        {
            'title': 'OpenAI Releases New Model for Scientific Research',
            'url': 'https://example.com/openai-science',
            'source': 'OpenAI Blog',
            'summary': 'OpenAI has released a new specialized model for scientific research '
                       'that can analyze academic papers and generate hypotheses.',
            'excerpt': 'OpenAI new model for scientific research.',
            'category': '🔬 Research',
            'tags': ['OpenAI', 'AI', 'Research', 'Science'],
            'importance': '🟡 Medium',
            'published_at': '2025-01-12T08:00:00',
            'language': 'en'
        }
    ]


def test_filter():
    """1차/2차 필터링 테스트"""
    print(f"\n{'='*60}")
    print("🔍 테스트: 뉴스 필터링 (1차 키워드 + 2차 AI 관련성)")
    print(f"{'='*60}\n")

    credentials, linkedin_config = load_config()
    articles = get_sample_articles()

    print(f"📰 입력 뉴스: {len(articles)}건\n")
    for i, a in enumerate(articles, 1):
        print(f"  {i}. [{a['importance']}] {a['title']}")
    print()

    news_filter = NewsFilter(
        config=linkedin_config.get('filter', {}),
        api_key=credentials['anthropic']['api_key']
    )

    filtered = news_filter.filter(articles)

    print(f"\n📋 최종 필터링 결과: {len(filtered)}건\n")
    for i, a in enumerate(filtered, 1):
        print(f"  {i}. [{a.get('relevance_score', '?')}/10] {a['title']}")
        print(f"     사유: {a.get('relevance_reason', 'N/A')}")
        print(f"     매칭 키워드: {', '.join(a.get('matched_keywords', []))}")
        print()

    return filtered


def test_generate():
    """포스트 생성 테스트 (샘플 1건)"""
    print(f"\n{'='*60}")
    print("✏️ 테스트: LinkedIn 포스트 생성")
    print(f"{'='*60}\n")

    credentials, linkedin_config = load_config()

    # 샘플 기사 1건 (이미 필터링된 것으로 가정)
    sample = get_sample_articles()[0]
    sample['relevance_score'] = 9
    sample['relevance_reason'] = 'CRM 자동화 + AI = B2B Sales 핵심 트렌드'
    sample['matched_keywords'] = ['CRM', 'Sales Automation', 'B2B Sales']

    generator = PostGenerator(
        config=linkedin_config,
        api_key=credentials['anthropic']['api_key']
    )

    print(f"📰 입력 뉴스: {sample['title']}\n")

    start = time.time()
    posts = generator.generate([sample])
    elapsed = time.time() - start

    if posts:
        post = posts[0]
        print(f"\n{'─'*60}")
        print(f"📌 제목: {post['title']}")
        print(f"{'─'*60}")
        print(post['body'])
        print(f"{'─'*60}")
        print(f"🏷️ 해시태그: {' '.join(post['hashtags'])}")
        print(f"📂 카테고리: {post['category']}")
        print(f"🔗 원문: {post['source_url']}")
        print(f"⏱️ 소요시간: {elapsed:.1f}s")
    else:
        print("❌ 포스트 생성 실패")

    return posts


def test_archive():
    """노션 저장 테스트 (샘플 1건)"""
    print(f"\n{'='*60}")
    print("💾 테스트: 노션 LinkedIn DB 저장")
    print(f"{'='*60}\n")

    credentials, linkedin_config = load_config()

    sample_post = {
        'title': '[테스트] AI가 B2B Sales를 바꾸는 3가지',
        'body': '🚀 AI가 B2B 영업의 게임을 바꾸고 있습니다.\n\n'
                '최근 Salesforce의 AI CRM 자동화 발표를 보면서,\n'
                '14년간 B2B 현장에서 느꼈던 변화가 확실히 가속화되고 있다는 걸 체감합니다.\n\n'
                '핵심 변화 3가지:\n'
                '1️⃣ 리드 스코어링 자동화 → 영업 시간 30% 절약\n'
                '2️⃣ 파이프라인 예측 정확도 향상\n'
                '3️⃣ 데이터 입력 시간 80% 감소\n\n'
                '여러분의 팀은 AI를 영업에 어떻게 활용하고 계신가요?\n\n'
                '#AI #B2BSales #CRM #SalesAutomation #SaaS #RevOps',
        'hashtags': ['#AI', '#B2BSales', '#CRM', '#SalesAutomation', '#SaaS', '#RevOps'],
        'category': 'AI x Sales',
        'source_url': 'https://example.com/salesforce-ai-crm',
        'source_title': 'Salesforce Launches AI-Powered CRM Automation Suite'
    }

    archiver = PostArchiver({
        'integration_token': credentials['notion']['integration_token'],
        'database_id': credentials['notion']['linkedin_database_id']
    })

    print(f"📝 저장할 포스트: {sample_post['title']}\n")

    result = archiver.archive([sample_post])

    print(f"\n📊 결과:")
    print(f"   ✅ 성공: {result['success']}")
    print(f"   ❌ 실패: {result['failed']}")
    if result['errors']:
        for err in result['errors']:
            print(f"   에러: {err}")

    return result


def test_full():
    """전체 파이프라인 테스트 (필터 → 생성 → 저장)"""
    print(f"\n{'='*60}")
    print("🚀 테스트: 전체 파이프라인 (필터 → 생성 → 저장)")
    print(f"{'='*60}\n")

    credentials, linkedin_config = load_config()
    articles = get_sample_articles()

    print(f"📰 입력 뉴스: {len(articles)}건\n")

    pipeline = LinkedInPostGenerator(linkedin_config, credentials)

    start = time.time()
    result = pipeline.run(articles)
    elapsed = time.time() - start

    print(f"\n{'='*60}")
    print(f"📊 전체 파이프라인 결과")
    print(f"{'='*60}")
    print(f"   🔍 필터링 통과: {result['filtered']}건")
    print(f"   ✏️ 포스트 생성: {result['generated']}건")
    if result.get('archived'):
        print(f"   💾 노션 저장 성공: {result['archived'].get('success', 0)}건")
        print(f"   ❌ 노션 저장 실패: {result['archived'].get('failed', 0)}건")
    print(f"   ⏱️ 총 소요시간: {elapsed:.1f}s")

    return result


def main():
    parser = argparse.ArgumentParser(description='LinkedIn 포스트 생성 파이프라인 테스트')
    parser.add_argument(
        '--step',
        choices=['filter', 'generate', 'archive', 'full'],
        required=True,
        help='테스트할 단계: filter | generate | archive | full'
    )
    args = parser.parse_args()

    # 로깅 설정
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    step_map = {
        'filter': test_filter,
        'generate': test_generate,
        'archive': test_archive,
        'full': test_full
    }

    step_map[args.step]()


if __name__ == '__main__':
    main()
