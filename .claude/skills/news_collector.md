# News Collector Skill

다양한 소스에서 AI 관련 최신 뉴스를 수집합니다.

## 수집 소스

### RSS 피드 (영어)
- TechCrunch AI
- MIT Technology Review
- The Verge AI
- VentureBeat AI
- Ars Technica
- Wired AI
- OpenAI Blog
- Anthropic News
- Google AI Blog

### RSS 피드 (한국어)
- AI 타임스
- 전자신문 AI

### API
- Hacker News (Algolia API)

## 필수 키워드 (하나 이상 포함)
- AI, artificial intelligence, machine learning
- deep learning, neural network, LLM
- GPT, Claude, Gemini, Llama
- transformer, diffusion, generative
- 인공지능, 머신러닝, 딥러닝

## 사용 예시

```bash
# 최근 24시간 뉴스 수집
python -c "
from agents.collector import RSSCollector
import yaml

with open('config/sources.yaml') as f:
    config = yaml.safe_load(f)

collector = RSSCollector(config)
result = collector.collect(hours_lookback=24)
print(f'Collected: {result[\"total_count\"]} articles')
"
```
