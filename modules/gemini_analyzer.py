import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import time

# CRITICAL: override=True to force reload environment variables
load_dotenv(override=True)

def get_model():
    """Gemini 모델 초기화"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")
    
    genai.configure(api_key=api_key)
    # Using gemini-2.5-flash-lite (has available quota, 2.0-flash quota exceeded)
    return genai.GenerativeModel('gemini-2.5-flash-lite')

def analyze_sentiment_batch(articles, batch_size=50):
    """
    Analyzes sentiment for a batch of articles using Gemini.
    Returns a list of sentiments corresponding to the articles.
    """
    if not articles:
        return []

    model = get_model()
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
            response = model.generate_content(prompt)
            text = response.text.strip()
            
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
    Generates a comprehensive issue report using Gemini.
    """
    if not articles:
        return "No articles found to analyze."

    model = get_model()
    
    # Limit articles for context window if necessary (though 1.5 has large context)
    # We will pass Title, Date, Press, and Sentiment
    
    articles_text = ""
    for art in articles[:50]: # Context limit safety (top 50)
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
       - 시간 순서대로 여론의 변화를 국면별(Phase)로 분석 (2-4개 국면)
       - 각 Phase는 ### 헤딩 레벨로 작성: "### Phase 1", "### Phase 2", "### Phase 3", "### Phase 4"
       - 각 Phase별: [날짜], 주요 보도 내용, 대중 반응, 감성 기조 포함
       - **전환점 (Turning Point)**: Phase와 동일한 ### 헤딩 레벨로 작성: "### 전환점 (Turning Point)"
       - 전환점 내용: 여론 방향이 바뀐 결정적 사건, 전후 보도 톤 변화, 야기한 주요 요인 분석
       - 명확한 전환점이 없다면 이 섹션을 생략
       - **중요**: 마크다운 형식을 정확히 사용 (### 다음에 공백 한 칸, 그 다음 제목)
    
    3. **헤드라인 및 프레임 분석 (Frame Analysis)**
       3.1 **프레임 유형 분류**: 
          - 실제 뉴스 헤드라인과 내용을 분석하여 주요 프레임 카테고리를 3-6개 도출
          - 각 프레임별로: 프레임명, 기사 건수, 대표 사례 또는 특징 설명, 비율(%)
          - **표 형식**: 프레임명 | 기사 건수 | 대표 사례 또는 특징 설명 | 비율(%) 순서로 컬럼 배치
          - 예시 프레임: 책임 소재, 갈등, 인간 관심, 경제적 결과, 윤리/도덕, 정책/제도, 사회적 영향, 기술/혁신 등
          - 데이터에 기반하여 가장 두드러진 프레임을 자동으로 선정하고 분류
       3.2 **헤드라인 톤 분석**: 
          - 실제 헤드라인에 사용된 어휘를 분석하여 톤 카테고리를 3-5개 도출
          - 각 톤별로: 톤 유형명, 대표 어휘 예시, 비율(%)
          - 예시 톤 유형: 선정적/자극적, 중립적/사실전달, 완화적/긍정적, 비판적/부정적, 분석적/해설적 등
          - **중요**: 모든 톤 카테고리의 비율 합계가 정확히 100%가 되도록 계산
          - 데이터에 기반하여 실제로 사용된 톤을 자동으로 분류
          - **주의**: 비율 합계 계산식(예: "43.9 + 30.8 + 23.1 = 100%")은 표시하지 말고, 각 톤별 비율만 표시
       3.3 **토픽 모델링**: 주요 논점 토픽 3-5개 도출 (주제명, 대표 키워드, 비율(%))
       3.4 **키워드 네트워크**:
          - **키워드 분석**: 자주 함께 등장하는 주요 키워드들을 분석하여 이슈의 맥락 파악
          - **유관 키워드 TOP 10**: 
            * Format: "N. <mark>Keyword1/Keyword2/Keyword3</mark> (Context/Meaning)" 
            * 반드시 <mark> 태그를 사용하여 키워드 조합을 강조하세요.
          - 키워드 간 연관성 분석
    
    4. **주요 쟁점 분석 (Key Issues)**
       - 이슈의 핵심 논점 3-5가지 정리
       - 각 쟁점별: 쟁점명, 구체적 논점 설명, 관련 기사 건수/비율, 대중 반응, 잠재적 영향
    
    5. **언론사 비교 분석**
       5.1 **언론사별 편향성 평가**: 보수, 진보, 중도/경제 매체별 주요 프레임 및 어조 비교
       5.2 **언론사별 보도 분포**: 
          - **활발한 상위 5개사**: 보도 건수가 많은 순서대로 정렬 (1위부터 5위까지)
          - 각 언론사별: 언론사명, 기사 건수, 비율(%)
          - 대형 매체 vs 중소 매체 비교 및 특징 분석
    
    6. **결론 및 향후 전망 (Conclusion & Future Scenarios)**
       6.1 **종합 평가**: 이슈 심각도(상/중/하), 대중 감성 방향, 주요 리스크 및 기회 요인
       6.2 **향후 전망 시나리오**: 
          - 각 시나리오별로 일관된 형식 사용
          - **긍정적 전개 (Best)**: 
            * 가능성: [평가]
            * 예상 결과 및 조건: (하위 항목들을 bullet point로 나열)
          - **현상 유지 (Likely)**: 
            * 가능성: [평가]
            * 예상 결과 및 조건: (하위 항목들을 bullet point로 나열)
          - **부정적 심화 (Worst)**: 
            * 가능성: [평가]
            * 예상 결과 및 조건: (하위 항목들을 bullet point로 나열)
          - **중요**: 모든 시나리오의 하위 항목(가능성, 예상 결과 및 조건) 사이에 동일한 줄간격 유지
          - **중요**: "예상 결과 및 조건" 하위의 모든 bullet point들도 동일한 줄간격으로 작성
       6.3 **권고사항 (Recommendations)**: 
          - **커뮤니케이션 전략**: 
            * 구체적인 전략 3-5가지를 bullet point로 나열
            * 각 항목 사이에 동일한 줄간격 유지
          - **모니터링 포인트**: 
            * 주요 모니터링 항목 3-5가지를 bullet point로 나열
            * 각 항목 사이에 동일한 줄간격 유지
          - **리스크 관리 방안**: 
            * 구체적인 관리 방안 3-5가지를 bullet point로 나열
            * 각 항목 사이에 동일한 줄간격 유지
          - **중요**: 모든 하위 섹션(커뮤니케이션 전략, 모니터링 포인트, 리스크 관리 방안)의 bullet point들은 동일한 줄간격과 들여쓰기 사용
    
    Write in Korean. Professional and analytical tone.
    Output ONLY the Markdown content. Use proper headers and bullet points.
    Ensure HTML tags like <mark> are used strictly following the format in section 3.4.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating report: {e}")
        raise  # Re-raise to let caller handle the error

def translate_report(report_content, target_language="English"):
    """
    Translates a report from Korean to English or vice versa using Gemini.
    
    Args:
        report_content (str): The markdown report content to translate
        target_language (str): "English" or "Korean"
    
    Returns:
        str: Translated report content in markdown format
    """
    if not report_content or report_content == "No report content.":
        return report_content
    
    model = get_model()
    
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
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error translating report: {e}")
        return report_content  # Return original if translation fails
