"""
Test the complete news collection and sentiment analysis pipeline
"""
import os
from dotenv import load_dotenv
load_dotenv(override=True)

from modules import news_collector, gemini_analyzer
from datetime import datetime, timedelta

# Test with a simple keyword and short date range
keyword = "삼성전자"
end_date = datetime.now()
start_date = end_date - timedelta(days=3)  # Last 3 days

start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

print("="*60)
print("Testing News Collection and Sentiment Analysis Pipeline")
print("="*60)
print(f"Keyword: {keyword}")
print(f"Period: {start_str} ~ {end_str}")
print()

# Step 1: Collect News
print("[STEP 1] Collecting news articles...")
result = news_collector.search_naver_news(keyword, start_str, end_str)

if not result['success']:
    print(f"[ERROR] Collection failed: {result.get('error')}")
    exit(1)

articles = result['article_details']
total_count = len(articles)
print(f"[SUCCESS] Collected {total_count} articles")
print()

if total_count == 0:
    print("[WARNING] No articles found. Try a different keyword or date range.")
    exit(0)

# Show sample articles
print("Sample articles (first 3):")
for i, article in enumerate(articles[:3], 1):
    print(f"  {i}. [{article['date']}] {article['title'][:50]}...")
print()

# Step 2: Analyze Sentiment
print(f"[STEP 2] Analyzing sentiment for {total_count} articles...")
try:
    # Test with small batch first
    test_articles = articles[:10]  # Only test first 10 articles
    print(f"Testing with {len(test_articles)} articles...")
    
    sentiments = gemini_analyzer.analyze_sentiment_batch(test_articles, batch_size=10)
    
    if len(sentiments) != len(test_articles):
        print(f"[WARNING] Sentiment count mismatch: {len(sentiments)} vs {len(test_articles)}")
    
    print(f"[SUCCESS] Sentiment analysis complete!")
    print()
    
    # Count sentiment distribution
    pos_count = sentiments.count('Positive')
    neg_count = sentiments.count('Negative')
    neu_count = sentiments.count('Neutral')
    
    print("Sentiment Distribution:")
    print(f"  Positive: {pos_count} ({pos_count/len(sentiments)*100:.1f}%)")
    print(f"  Negative: {neg_count} ({neg_count/len(sentiments)*100:.1f}%)")
    print(f"  Neutral:  {neu_count} ({neu_count/len(sentiments)*100:.1f}%)")
    print()
    
    # Show detailed results
    print("Detailed Results (first 5):")
    for i in range(min(5, len(test_articles))):
        article = test_articles[i]
        sentiment = sentiments[i] if i < len(sentiments) else "Unknown"
        sentiment_kr = {'Positive': '긍정', 'Negative': '부정', 'Neutral': '중립'}.get(sentiment, sentiment)
        print(f"  {i+1}. [{sentiment_kr}] {article['title'][:60]}...")
    
    print()
    print("="*60)
    print("[EXCELLENT] Pipeline test completed successfully!")
    print("="*60)
    
except Exception as e:
    print(f"[ERROR] Sentiment analysis failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
