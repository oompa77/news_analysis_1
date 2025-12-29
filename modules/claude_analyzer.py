import os
from anthropic import Anthropic
from dotenv import load_dotenv
import json
import time

# CRITICAL: override=True to force reload environment variables
load_dotenv(override=True)

def get_client():
    """
    Returns the configured Claude client.
    """
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment variables.")
    
    return Anthropic(api_key=api_key)

def analyze_sentiment_batch(articles, batch_size=50):
    """
    Analyzes sentiment for a batch of articles using Claude.
    Returns a list of sentiments corresponding to the articles.
    """
    if not articles:
        return []

    client = get_client()
    all_sentiments = []
    
    # Process in smaller batches for better accuracy
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i+batch_size]
        
        # Prepare prompt
        titles = [f"{j+1}. {article['title']}" for j, article in enumerate(batch)]
        titles_text = "\n".join(titles)
        
        prompt = f"""다음 뉴스 제목들의 감정을 분석해주세요.
각 제목을 '긍정', '부정', 또는 '중립'으로 분류하세요.

분류 기준:
- 긍정 (Positive): 좋은 소식, 성장, 발전, 성공 등
- 부정 (Negative): 나쁜 소식, 문제, 사고, 논란, 비판 등  
- 중립 (Neutral): 단순 정보 전달, 일반적인 소식

반드시 JSON 배열 형태로만 답변하세요. 예: ["Positive", "Negative", "Neutral", ...]
다른 설명 없이 JSON만 출력하세요.

제목들:
{titles_text}
"""
        
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            text = response.content[0].text.strip()
            
            # Clean up code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            sentiments = json.loads(text.strip())
            
            # Ensure length matches
            if len(sentiments) != len(batch):
                print(f"Warning: Batch count ({len(batch)}) and Sentiment count ({len(sentiments)}) mismatch.")
                while len(sentiments) < len(batch):
                    sentiments.append("Neutral")
                sentiments = sentiments[:len(batch)]
            
            all_sentiments.extend(sentiments)
            
            # Small delay to avoid rate limiting
            if i + batch_size < len(articles):
                time.sleep(1)
                
        except json.JSONDecodeError as e:
            print(f"Error parsing sentiment JSON response for batch {i//batch_size + 1}: {e}")
            print(f"Raw response: {text if 'text' in locals() else 'N/A'}")
            all_sentiments.extend(["Neutral"] * len(batch))
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            all_sentiments.extend(["Neutral"] * len(batch))
    
    return all_sentiments

def generate_issue_report(keyword, articles, sentiment_summary):
    """
    Generates a comprehensive issue report using Claude.
    """
    if not articles:
        return "No articles found to analyze."

    client = get_client()
    
    # Limit articles for context window
    articles_text = ""
    for art in articles[:50]:  # Context limit safety (top 50)
        articles_text += f"- [{art.get('date', 'Unknown Date')}] {art['title']} ({art.get('press', 'Unknown Press')})\n"

    stats_text = f"Total: {len(articles)}, Sentiment: {sentiment_summary}"

    prompt = f"""
    You are an expert news analyst. Create a high-quality 'Issue Report' for the keyword: '{keyword}'.
    Use the following news data (Title, Date, Press) to generate a professional, structured report.
    
    ## Data Summary
    {stats_text}
    
    ## News Headlines (Sample)
    {articles_text}
    
    ## Report Structure & Requirements
    
    1. **개요 (Executive Summary)**
       - 총 집계 기사 건수와 톤 분석
       - 전반적인 보도 기조 (긍정적/부정적/균형적)
       - 주요 보도 내용 3-5가지 핵심 카테고리 요약
    
    2. **여론 흐름 및 전환점 (Public Opinion Flow & Turning Points)**
       - 시간 순서대로 여론의 변화를 국면별(Phase)로 분석 (최소 2개 국면 이상)
       - 각 Phase별: [날짜], 주요 보도 내용, 대중 반응, 감성 기조 포함
       - **전환점 (Turning Point)**: 여론 방향이 바뀐 결정적 사건, 전후 보도 톤 변화, 야기한 주요 요인 분석
    
    3. **헤드라인 및 프레임 분석 (Frame Analysis)**
       3.1 **프레임 유형 분류**: 책임 소재, 갈등, 인간 관심, 경제적 결과, 윤리/도덕 프레임별 기사 비중 분석
       3.2 **헤드라인 톤 분석**: 선정적 어휘(폭로, 충격 등), 중립적 어휘(발표, 공개 등), 완화적 어휘(해명, 입장 등) 사용 비율
       3.3 **토픽 모델링**: 주요 논점 토픽 3-5개 도출 (주제명, 대표 키워드, 관련 기사 비율)
       3.4 **어휘 네트워크**:
          - 공기 단어(Co-occurrence) 분석
          - **중심성(Centrality) 높은 키워드 TOP 10**: 
            * Format: "N. <mark>Keyword1/Keyword2/Keyword3</mark> (Context/Meaning)" 
            * 반드시 <mark> 태그를 사용하여 키워드 조합을 강조하세요.
          - 키워드 간 연관성 분석
    
    4. **주요 쟁점 분석 (Key Issues)**
       - 이슈의 핵심 논점 3-5가지 정리
       - 각 쟁점별: 쟁점명, 구체적 논점 설명, 관련 기사 건수/비율, 대중 반응, 잠재적 영향
    
    5. **언론사 및 커뮤니티별 비교 분석**
       5.1 **언론사별 편향성 평가**: 보수, 진보, 중도/경제 매체별 주요 프레임 및 어조 비교
       5.2 **언론사별 보도 분포**: 주요 언론사별 기사 건수, 대형 매체 vs 중소 매체 비교, 활발한 상위 5개사
    
    6. **결론 및 향후 전망 (Conclusion & Future Scenarios)**
       6.1 **종합 평가**: 이슈 심각도(상/중/하), 대중 감성 방향, 주요 리스크 및 기회 요인
       6.2 **향후 전망 시나리오**: 긍정적 전개(Best), 현상 유지(Likely), 부정적 심화(Worst) 시나리오별 가능성 및 결과
       6.3 **권고사항 (Recommendations)**: 커뮤니케이션 전략, 모니터링 포인트, 리스크 관리 방안
    
    Write in Korean. Professional and analytical tone.
    Output ONLY the Markdown content. Use proper headers and bullet points.
    Ensure HTML tags like <mark> are used strictly following the format in section 3.4.
    """
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8192,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error generating report: {e}")
        raise  # Re-raise to let caller handle the error

def translate_report(report_content, target_language="English"):
    """
    Translates a report from Korean to English or vice versa using Claude.
    
    Args:
        report_content (str): The markdown report content to translate
        target_language (str): "English" or "Korean"
    
    Returns:
        str: Translated report content in markdown format
    """
    if not report_content or report_content == "No report content.":
        return report_content
    
    client = get_client()
    
    if target_language == "English":
        prompt = f"""
        Translate the following Korean report to English.
        Maintain all markdown formatting, including headers, lists, bold text, and HTML tags like <mark>.
        Preserve the structure and professional tone.
        Output ONLY the translated markdown content without any additional comments.
        
        Report:
        {report_content}
        """
    else:  # Korean
        prompt = f"""
        Translate the following English report to Korean.
        Maintain all markdown formatting, including headers, lists, bold text, and HTML tags like <mark>.
        Preserve the structure and professional tone.
        Output ONLY the translated markdown content without any additional comments.
        
        Report:
        {report_content}
        """
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8192,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error translating report: {e}")
        return report_content  # Return original if translation fails
