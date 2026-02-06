import time
import logging
from typing import Dict, Any, List

import anthropic

logger = logging.getLogger(__name__)


class PostGenerator:
    """Claude API를 사용한 LinkedIn 포스트 생성"""

    def __init__(self, config: Dict[str, Any], api_key: str):
        self.generation_config = config.get('generation', {})
        self.profile = config.get('profile', {})
        self.post_structure = config.get('post_structure', {})
        self.writing_rules = config.get('writing_rules', [])

        self.model = self.generation_config.get('model', 'claude-sonnet-4-20250514')
        self.max_posts = self.generation_config.get('max_posts_per_run', 3)
        self.max_length = self.generation_config.get('max_length', 1800)
        self.max_retries = self.generation_config.get('max_retries', 3)
        self.retry_delay = self.generation_config.get('retry_delay', 2)

        self.client = anthropic.Anthropic(api_key=api_key)
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """프로필 + 포스트 구조를 기반으로 시스템 프롬프트 생성"""
        career = '\n'.join(f"  - {h}" for h in self.profile.get('career_highlights', []))
        expertise = '\n'.join(f"  - {e}" for e in self.profile.get('expertise', []))

        structure_lines = '\n'.join(
            f"  - {key}: {value}" for key, value in self.post_structure.items()
        )

        rules_lines = '\n'.join(
            f"  - {rule}" for rule in self.writing_rules
        ) if self.writing_rules else ''

        return f"""너는 LinkedIn 포스트 전문 작성자이다. 아래 프로필의 관점에서 뉴스/트렌드 기반 포스트를 작성한다.

## 작성자 프로필
- 이름: {self.profile.get('name', '')}
- 역할: {self.profile.get('role', '')}
- 경력: {self.profile.get('experience', '')}
- 주요 경력:
{career}
- 전문 분야:
{expertise}
- 브랜딩 목표: {self.profile.get('branding_goal', '')}

## 작성 톤
{self.profile.get('tone', '')}

## 포스트 구조
{structure_lines}

## 제약조건
1. 한글로 작성 (전문용어는 영문 병기 가능)
2. 본문 {self.max_length}자 이내 (해시태그 제외)
3. 줄바꿈을 적극 활용하여 가독성 확보
4. 이모지는 포인트로만 사용 (과하지 않게)
5. 제목(Title)은 포스트 핵심을 15자 이내로 요약
6. 해시태그는 5-7개, 마지막 줄에 배치
7. 출처는 이름만 언급 (예: 'TechCrunch에 따르면'). 본문에 URL 링크 절대 넣지 않기
8. 개인 경험 언급 시 회사명/구체적 숫자 없이 자연스럽게
9. 마지막은 짧은 소감/전망으로 마무리. 댓글 유도 질문(CTA) 금지
10. 본문 끝에 반드시 '📎 출처는 첫 번째 댓글에' 한 줄 추가
{chr(10) + '## 작성 규칙' + chr(10) + rules_lines if rules_lines else ''}
## 출력 형식
반드시 아래 형식으로 출력:

[TITLE]
포스트 제목
[/TITLE]

[BODY]
포스트 본문 (해시태그 포함)
[/BODY]

[HASHTAGS]
#태그1 #태그2 #태그3
[/HASHTAGS]

[CATEGORY]
카테고리명
[/CATEGORY]"""

    def generate(self, articles: List[Dict]) -> List[Dict]:
        """필터링된 기사 목록으로 포스트 생성. 관련성 점수 순으로 상위 N개만."""
        # 상위 N개만 선택
        target_articles = articles[:self.max_posts]
        print(f"   📝 포스트 생성 대상: {len(target_articles)}건 (최대 {self.max_posts}건)")

        posts = []
        total_input_tokens = 0
        total_output_tokens = 0

        for i, article in enumerate(target_articles, 1):
            start_time = time.time()
            print(f"   [{i}/{len(target_articles)}] {article['title'][:50]}...")

            try:
                post = self._generate_single(article)
                elapsed = time.time() - start_time

                # 토큰 사용량 추적
                input_tokens = post.pop('_input_tokens', 0)
                output_tokens = post.pop('_output_tokens', 0)
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens

                posts.append(post)
                print(f"        ✅ 생성 완료 ({elapsed:.1f}s, in:{input_tokens} out:{output_tokens} tokens)")

            except anthropic.APIStatusError as e:
                if e.status_code == 402:
                    print(f"        ❌ API 크레딧 부족 (402). 포스트 생성 중단.")
                    break
                print(f"        ❌ API 에러 ({e.status_code}): {e.message}")

            except Exception as e:
                elapsed = time.time() - start_time
                print(f"        ❌ 생성 실패 ({elapsed:.1f}s): {e}")

        print(f"   📊 토큰 사용량 - input: {total_input_tokens}, output: {total_output_tokens}")
        return posts

    def _generate_single(self, article: Dict) -> Dict:
        """단일 기사에 대한 포스트 생성 (retry 로직 포함)"""
        user_prompt = self._build_user_prompt(article)

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    system=self.system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )

                result = self._parse_response(response.content[0].text)
                result['source_url'] = article.get('url', '')
                result['source_title'] = article.get('title', '')
                result['relevance_score'] = article.get('relevance_score', 0)
                result['_input_tokens'] = response.usage.input_tokens
                result['_output_tokens'] = response.usage.output_tokens

                return result

            except anthropic.APIStatusError:
                raise  # 402 등 API 상태 에러는 바로 올림

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    logger.warning(f"  Retry {attempt}/{self.max_retries}: {e}")
                    time.sleep(self.retry_delay)

        raise last_error

    def _build_user_prompt(self, article: Dict) -> str:
        """기사 데이터를 기반으로 유저 프롬프트 생성"""
        return f"""아래 뉴스를 기반으로 LinkedIn 포스트를 작성해주세요.

## 뉴스 정보
- 제목: {article.get('title', '')}
- 요약: {article.get('summary', article.get('excerpt', ''))}
- 카테고리: {article.get('category', '')}
- 태그: {', '.join(article.get('tags', []))}
- 출처: {article.get('source', '')}
- URL: {article.get('url', '')}

## AI 관련성 평가
- 점수: {article.get('relevance_score', 'N/A')}/10
- 이유: {article.get('relevance_reason', 'N/A')}
- 매칭 키워드: {', '.join(article.get('matched_keywords', []))}

위 뉴스의 핵심 인사이트를 추출하고, 작성자 프로필의 B2B Sales/BizOps 경험과 연결하여 실무자 관점의 포스트를 작성해주세요."""

    def _parse_response(self, text: str) -> Dict:
        """Claude 응답을 구조화된 딕셔너리로 파싱"""
        result = {
            'title': '',
            'body': '',
            'hashtags': [],
            'category': ''
        }

        # [TITLE] 파싱
        if '[TITLE]' in text and '[/TITLE]' in text:
            title_block = text.split('[TITLE]')[1].split('[/TITLE]')[0].strip()
            result['title'] = title_block

        # [BODY] 파싱
        if '[BODY]' in text and '[/BODY]' in text:
            body_block = text.split('[BODY]')[1].split('[/BODY]')[0].strip()
            result['body'] = body_block

        # [HASHTAGS] 파싱
        if '[HASHTAGS]' in text and '[/HASHTAGS]' in text:
            hashtags_block = text.split('[HASHTAGS]')[1].split('[/HASHTAGS]')[0].strip()
            result['hashtags'] = [
                tag.strip() for tag in hashtags_block.replace('#', ' #').split()
                if tag.startswith('#')
            ]

        # [CATEGORY] 파싱
        if '[CATEGORY]' in text and '[/CATEGORY]' in text:
            category_block = text.split('[CATEGORY]')[1].split('[/CATEGORY]')[0].strip()
            result['category'] = category_block

        # 파싱 실패 시 전체 텍스트를 body로
        if not result['body']:
            result['body'] = text
            result['title'] = text[:30] + '...'

        return result
