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
    # Using gemini-2.5-flash (latest stable version)
    return genai.GenerativeModel('gemini-2.5-flash')

def analyze_sentiment_batch(articles, batch_size=25):
    """
    Analyzes sentiment for a batch of articles using Gemini.
    Returns a list of sentiments corresponding to the articles.
    Batch size reduced to 25 for better accuracy with large article counts (500+).
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
        
        prompt = f"""다음 뉴스 제목들의 감정을 정확하게 분석해주세요.
각 제목을 '긍정', '부정', 또는 '중립'으로 분류하세요.

분류 기준:

**긍정 (Positive)**:
- 성과, 성장, 발전, 성공, 호조, 증가, 개선, 혁신, 승리, 달성
- 긍정적 전망, 기대, 환영, 지지, 칭찬
- 예시: "○○, 역대 최고 실적 달성", "○○ 기술 세계 1위 등극", "○○ 주가 급등", "○○ 긍정 평가 확산"

**부정 (Negative)**:
- 문제, 사고, 논란, 비판, 우려, 감소, 악화, 갈등, 실패, 손실
- 부정적 전망, 위기, 경고, 반발, 비난
- 예시: "○○, 대규모 결함 발견", "○○ 논란 확산", "○○ 주가 폭락", "○○ 비판 여론 고조"

**중립 (Neutral)**:
- **매우 엄격하게 적용**: 오직 순수한 사실 전달만 하며 긍정도 부정도 아닌 경우에만 해당
- 일정 안내, 단순 공지, 통계 발표(감정적 뉘앙스 없이)
- 예시: "○○, 내일 기자회견 개최", "○○ 신제품 출시 예정", "○○, 연례 보고서 발표"

**중요 규칙**:
1. 조금이라도 긍정적이거나 부정적인 뉘앙스가 있다면 중립이 아닙니다
2. 애매한 경우, 제목의 전반적인 톤을 고려하여 긍정 또는 부정 중 더 가까운 쪽으로 분류하세요
3. "논란", "우려", "불안", "위기" 등의 단어는 부정으로 분류
4. "성과", "성공", "호조", "증가" 등의 단어는 긍정으로 분류
5. 중립은 전체의 10-20% 정도만 되도록 신중하게 판단하세요

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






    




    


def clean_json_text(text):
    """
    Cleans the AI response text to extract valid JSON.
    Removes markdown code blocks and whitespace.
    """
    text = text.strip()
    # Remove markdown code blocks if present
    if text.startswith("```"):
        # Remove first line (```json or just ```)
        parts = text.split("\n", 1)
        if len(parts) > 1:
            text = parts[1]
    
    if text.strip().endswith("```"):
        text = text.strip()[:-3]
        
    return text.strip()

def generate_issue_report(keyword, articles, context_summary, total_count=None):
    """
    Generates a structured JSON report using Gemini.
    """
    model = get_model()
    
    # Check prompt length (safety mechanism)
    # Check prompt length (safety mechanism) - Increased for full coverage
    articles_text = json.dumps(articles[:3000], ensure_ascii=False)
    
    prompt = f"""
    You are an expert news analyst. Your task is to analyze {len(articles)} news articles about '{keyword}' and generate a structured JSON report.
    
    CONTEXT SUMMARY:
    {context_summary}
    
    INSTRUCTIONS:
    1. Analyze the articles provided below.
    2. **CRITICAL**: You MUST generate a 'daily_trends' entry for **EVERY SINGLE DATE** present in the articles. Do NOT summarize multiple days into one. Do NOT skip any dates. Processing time is not an issue.
    3. Output ONLY valid JSON matching the structure below.
    3. Do NOT use markdown code blocks (e.g. ```json). Just raw JSON.
    4. ESCAPE all double quotes within string values (e.g. \\"quote\\"). This is CRITICAL.
    5. Ensure all JSON keys and string values are properly quoted.
    6. **LANGUAGE**: All content values MUST be in **KOREAN** (한국어).
    
    JSON STRUCTURE:
    {{
        "executive_summary": {{
            "total_articles": {len(articles)},
            "tone_analysis": "Overall tone narrative (2-3 sentences). Focus on HOT TOPICS first.",
            "key_takeaways": ["Point 1", "Point 2", "Point 3"]
        }},
        "daily_trends": [
            {{
                "date": "YYYY-MM-DD",
                "volume": 0,
                "one_line_summary": "One sentence daily summary",
                "narrative_summary": "Detailed narrative of the day's events",
                "sub_topics": [
                    {{
                        "name": "Topic Name",
                        "count": 0,
                        "percent": 0.0,
                        "description": "One line explanation of the topic content",
                        "examples": "Example entities"
                    }}
                ],
                "key_findings": {{
                    "article_analysis": ["Key Point 1", "Key Point 2"],
                    "media_focus": ["Media Focus 1", "Media Focus 2"],
                    "dynamics": ["Brand/Person Dynamics"]
                }},
                "daily_themes": [
                    {{
                        "name": "Theme Name",
                        "stats": "Article count info",
                        "core_message": "Core Message",
                        "details": [ "Detail 1", "Detail 2" ],
                        "reporter_traits": "Reporter characteristics",
                        "social_impact": "Social impact description"
                    }}
                ],
                "issue_short": "Main issue in max 4 Korean words",
                "sentiment_stat": "긍정 00%, 중립 00%, 부정 00%" ,
                "key_people": "Important people mentioned"
            }}
        ],
        "peak_analysis": [
            {{ "order": 1, "date": "YYYY-MM-DD", "volume": 0, "reason": "초단문 키워드 (2-3단어, 예: 논란 점화, 티저 공개)" }}
        ],
        "keyword_analysis": {{
            "people": [
                {{ "rank": 1, "keyword": "Name", "count": 0, "context": "Role/Issue" }}
                // ... Top 10 (Strictly identify top 10 key figures)
            ],
            "topics": [
                 {{ "rank": 1, "keyword": "Word", "count": 0, "context": "Context" }}
                 // ... Top 10 (Strictly use single "Words" centering on the topic, NOT phrases)
            ],
            "brands_companies": [
                 {{ "rank": 1, "keyword": "Brand/Company", "count": 0, "context": "Context" }}
                 // ... Top 10 (Strictly identify top 10 brands or companies. Clean names only. Exclude general terms.)
            ]
        }},
        "detailed_topic_analysis": {{
            "hot_topics": [ {{ "title": "T", "content": "C" }} ],
            "controversy_analysis": [ {{ "title": "T", "content": "C" }} ],
            "brand_collabs": {{
                "overview": "Overview of industry trends",
                "cases": [
                    {{
                        "brand_name": "Brand Name",
                        "collaborator": "Partner (Person/Company)",
                        "campaign_detail": "Specific Campaign/Product",
                        "marketing_action": "Marketing Strategy/Action"
                    }}
                ]
            }}
        }},
        "time_series_flow": {{
            "early": {{ "period": "", "major_reports": "", "public_reaction": "" }},
            "middle": {{ "period": "", "major_reports": "", "public_reaction": "" }},
            "late": {{ "period": "", "major_reports": "", "public_reaction": "" }}
        }},
        "conclusion": "Conclusion text"
    }}

    ARTICLES:
    {articles_text}
    """
    
    try:
        if len(prompt) > 1000000:
             # Simple truncation if too long
             prompt = prompt[:1000000] + "... (truncated)"

        # Configure for valid JSON output
        generation_config = {
            "temperature": 0.5,
            "response_mime_type": "application/json"
        }
        
        response = model.generate_content(prompt, generation_config=generation_config)
        text = response.text
        
        # Clean JSON text
        cleaned_text = clean_json_text(text)
        
        try:
             json_data = json.loads(cleaned_text)
             # Validate math
             json_data = validate_and_fix_math(json_data)
             return json.dumps(json_data, ensure_ascii=False)
        except json.JSONDecodeError as e:
             # Fallback: Try to find the first '{' and last '}'
             try:
                 start_idx = text.find('{')
                 end_idx = text.rfind('}')
                 if start_idx != -1 and end_idx != -1:
                     potential_json = text[start_idx:end_idx+1]
                     json_data = json.loads(potential_json)
                     json_data = validate_and_fix_math(json_data)
                     return json.dumps(json_data, ensure_ascii=False)
             except:
                 pass
             
             print(f"Error parsing JSON response: {e}")
             return json.dumps({"error": f"JSON parsing failed: {e}", "raw_response": text[:100]}, ensure_ascii=False)

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error generating report: {e}")
        print(f"Full traceback:\n{error_trace}")
        return json.dumps({
            "executive_summary": {"total_articles": 0, "tone_analysis": "Error", "key_takeaways": [str(e)]},
            "error": str(e),
            "traceback": error_trace[:500]
        }, ensure_ascii=False)



def validate_and_fix_math(json_data, total_count_for_day=None):
    """
    Enforces that 'sub_topics' counts sum up to the day's total volume.
    Uses 'Others' (기타) category for under-counts.
    """
    try:
        daily_trends = json_data.get('daily_trends', [])
        for day in daily_trends:
            # Use total_count_for_day if provided, otherwise try to get from 'volume' field
            total_vol = total_count_for_day if total_count_for_day is not None else day.get('volume')
            
            if isinstance(total_vol, str):
                if total_vol.isdigit(): total_vol = int(total_vol)
                else: 
                    print(f"Warning: 'volume' is not a valid integer: {total_vol}. Skipping math validation for this day.")
                    continue
            
            if not isinstance(total_vol, int) or total_vol < 0:
                print(f"Warning: Invalid 'volume' ({total_vol}) for math validation. Skipping for this day.")
                continue
            
            sub_topics = day.get('sub_topics', [])
            if not sub_topics:
                # If no sub_topics, and total_vol > 0, add an 'Others' category
                if total_vol > 0:
                    day['sub_topics'] = [{
                        "name": "기타",
                        "count": total_vol,
                        "percent": 100.0,
                        "examples": "-"
                    }]
                continue
                
            # Calculate current sum
            current_sum = sum(int(t.get('count', 0)) for t in sub_topics if str(t.get('count', 0)).isdigit())
            
            diff = total_vol - current_sum
            
            if diff > 0:
                # Under-counted: Add 'Others' category
                others_topic = next((t for t in sub_topics if '기타' in t.get('name', '') or 'Others' in t.get('name', '')), None)
                
                if others_topic:
                    others_topic['count'] = int(others_topic.get('count', 0)) + diff
                else:
                    # Create new 'Others' topic
                    sub_topics.append({
                        "name": "기타",
                        "count": diff,
                        "percent": 0, # Will be recalc
                        "examples": "-"
                    })
            elif diff < 0:
                # Over-counted: Subtract from largest topic (that isn't others preferably, or just largest)
                sorted_indices = sorted(range(len(sub_topics)), key=lambda k: int(sub_topics[k].get('count', 0)), reverse=True)
                
                remaining_diff = abs(diff)
                for idx in sorted_indices:
                    current_count = int(sub_topics[idx].get('count', 0))
                    if current_count >= remaining_diff:
                        sub_topics[idx]['count'] = current_count - remaining_diff
                        remaining_diff = 0
                        break
                    else:
                        # If the current topic's count is less than the remaining_diff,
                        # set it to 0 and reduce remaining_diff by current_count.
                        remaining_diff -= current_count
                        sub_topics[idx]['count'] = 0
                
                if remaining_diff > 0:
                    print(f"Warning: Could not fully correct over-counted sub_topics. Remaining diff: {remaining_diff}")
            
            # Recalculate Percentages
            for t in sub_topics:
                cnt = int(t.get('count', 0))
                if total_vol > 0:
                    pct = round((cnt / total_vol) * 100, 1) # 1 decimal place
                else:
                    pct = 0
                t['percent'] = pct
            
            # Ensure the 'volume' field in the JSON matches the actual total_vol used for calculation
            day['volume'] = total_vol
                
    except Exception as e:
        print(f"Math validation error: {e}")
        
    return json_data

def translate_daily_report(daily_data, target_lang='English'):
    """
    Translates the relevant fields of a daily summary (key_issue, sub_topics) into the target language.
    """
    prompt = f"""
    You are a professional translator. 
    Translate the following JSON content into {target_lang}.
    Maintain the original JSON structure strictly.
    Only translate the "value" strings. Do not translate keys.
    
    Data to translate:
    {json.dumps(daily_data, ensure_ascii=False)}
    
    Output Format: JSON
    """
    
    try:
        # Configure for valid JSON output
        generation_config = {
            "temperature": 0.5,
            "response_mime_type": "application/json"
        }
        response = model.generate_content(prompt, generation_config=generation_config)
        text = response.text.strip()
        # Clean up Markdown
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        return json.loads(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return daily_data  # Fallback to original

def translate_global_report(report_data, target_lang='English'):
    """
    Translates the entire global report into the target language.
    Translates structurally by section to minimize context window issues.
    """
    model = get_model() # Fix: Initialize model
    
    prompt = f"""
    You are a professional translator. 
    Translate the following Global Analysis Report content into {target_lang}.
    
    INSTRUCTIONS:
    1. Maintain the original JSON structure strictly.
    2. Only translate string values (values of keys). Do not translate keys.
    3. Translate:
       - executive_summary (tone_analysis, key_takeaways)
       - daily_trends (issue_short, sentiment_stat usually stays similar but check, one_line_summary, narrative_summary, sub_topics.name/description, key_findings, daily_themes)
       - peak_analysis (reason)
       - keyword_analysis (context)
       - detailed_topic_analysis (content, overview, cases)
       - time_series_flow (period, major_reports, public_reaction)
       - conclusion
    4. Return ONLY valid JSON.

    Data to translate:
    {json.dumps(report_data, ensure_ascii=False)}
    """
    
    try:
        # Configure for valid JSON output
        generation_config = {
            "temperature": 0.5,
            "response_mime_type": "application/json"
        }
        
        # Check token limit roughly - if too huge we might need to split, but for report dict it should be fine logic-wise
        # If deeply large, we rely on Gemini 2.0's large context window.
        
        response = model.generate_content(prompt, generation_config=generation_config)
        text = response.text.strip()
        
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        return json.loads(text)
    except Exception as e:
        print(f"Global translation error: {e}")
        return report_data

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
