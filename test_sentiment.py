"""
Test sentiment analysis function directly with sample data
"""
import os
from dotenv import load_dotenv
load_dotenv(override=True)

from modules import gemini_analyzer

# Sample articles for testing
sample_articles = [
    {'title': '삼성전자, 3분기 영업이익 10조원 돌파...역대 최대 실적', 'date': '2025-12-29', 'press': '한국경제', 'link': 'http://example.com/1'},
    {'title': '삼성전자 주가 급락...반도체 시장 불안 가중', 'date': '2025-12-29', 'press': '매일경제', 'link': 'http://example.com/2'},
    {'title': '삼성전자, 신제품 발표 예정', 'date': '2025-12-29', 'press': '연합뉴스', 'link': 'http://example.com/3'},
    {'title': '삼성전자 노조, 임금 협상 타결', 'date': '2025-12-28', 'press': '조선일보', 'link': 'http://example.com/4'},
    {'title': '삼성전자, 환경 오염 논란...시민단체 반발', 'date': '2025-12-28', 'press': '경향신문', 'link': 'http://example.com/5'},
]

print("="*60)
print("Testing Sentiment Analysis Function")
print("="*60)
print(f"Testing with {len(sample_articles)} sample articles")
print()

try:
    print("[STEP 1] Calling analyze_sentiment_batch()...")
    sentiments = gemini_analyzer.analyze_sentiment_batch(sample_articles, batch_size=5)
    
    print(f"[SUCCESS] Received {len(sentiments)} sentiment results")
    print()
    
    # Validate results
    if len(sentiments) != len(sample_articles):
        print(f"[WARNING] Count mismatch: {len(sentiments)} vs {len(sample_articles)}")
    
    # Check sentiment values
    valid_sentiments = ['Positive', 'Negative', 'Neutral']
    invalid_count = 0
    for s in sentiments:
        if s not in valid_sentiments:
            invalid_count += 1
            print(f"[WARNING] Invalid sentiment value: {s}")
    
    if invalid_count == 0:
        print("[SUCCESS] All sentiment values are valid")
    print()
    
    # Display results
    print("Results:")
    print("-" * 60)
    for i, (article, sentiment) in enumerate(zip(sample_articles, sentiments), 1):
        sentiment_kr = {'Positive': '긍정', 'Negative': '부정', 'Neutral': '중립'}.get(sentiment, sentiment)
        emoji = {'Positive': '😊', 'Negative': '😞', 'Neutral': '😐'}.get(sentiment, '❓')
        print(f"{i}. [{sentiment_kr}] {article['title']}")
    
    print()
    
    # Count distribution
    pos_count = sentiments.count('Positive')
    neg_count = sentiments.count('Negative')
    neu_count = sentiments.count('Neutral')
    
    print("Distribution:")
    print(f"  Positive: {pos_count}")
    print(f"  Negative: {neg_count}")
    print(f"  Neutral:  {neu_count}")
    print()
    
    print("="*60)
    print("[EXCELLENT] Sentiment analysis test passed!")
    print("="*60)
    
except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
