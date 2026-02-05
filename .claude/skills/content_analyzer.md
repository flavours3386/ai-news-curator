# Content Analyzer Skill

수집된 뉴스 기사를 분석하여 중요도 평가, 카테고리 분류, 요약을 생성합니다.

## 분석 항목

### 1. 중요도 점수 (Importance)
- 9-10점: 🔴 Critical (반드시 읽어야 함)
- 7-8점: 🟠 High (중요한 뉴스)
- 5-6점: 🟡 Medium (참고할 만함)
- 1-4점: ⚪ Low (스킵 가능)

### 2. 카테고리 분류
- 🔬 Research: 연구, 논문, 학술 발표
- 🚀 Product: 제품 출시, 업데이트
- 💼 Business: 기업, 투자, 인수합병
- ⚖️ Policy: 규제, 정책, 법안
- 🔓 OpenSource: 오픈소스 프로젝트
- 🎓 Tutorial: 가이드, 튜토리얼
- 💭 Opinion: 칼럼, 의견, 분석

### 3. 태그 추출
- 회사명: OpenAI, Anthropic, Google, Meta, Microsoft
- 모델명: GPT, Claude, Gemini, Llama, Mistral
- 기술: LLM, Vision, Audio, Multimodal, RAG, Fine-tuning

## 사용 예시

```bash
# 기사 분석
python -c "
from agents.analyzer import ContentAnalyzer

analyzer = ContentAnalyzer()
articles = [...]  # 수집된 기사 목록
analyzed = analyzer.analyze(articles)
print(f'Analyzed: {len(analyzed)} articles')
"
```
