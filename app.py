import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import io
import os
import json
from dotenv import load_dotenv
from modules import news_collector, gemini_analyzer, github_storage

# Load environment variables
load_dotenv(override=True)

# Page Config
st.set_page_config(
    page_title="Media Analysis Insight",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Admin Session State
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# Initialize View State
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = None
if 'scroll_to_top' not in st.session_state:
    st.session_state.scroll_to_top = False

# JavaScript for Scroll to Top
if st.session_state.scroll_to_top:
    st.components.v1.html(
        "<script>window.parent.window.scrollTo(0,0);</script>",
        height=0
    )
    st.session_state.scroll_to_top = False

# Custom CSS
st.markdown("""
<style>
    /* Global Styles */
    .reportview-container {
        background: #ffffff;
    }
    .main {
        background-color: #ffffff;
        padding-top: 2rem;
    }
    h1, h2, h3 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #333;
    }
    h2 {
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    /* Metrics */
    .metric-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        background-color: #fafafa;
    }
    
    /* Tables */
    .stDataFrame {
        border: none !important;
    }
    
    /* Custom Gold Theme for Charts */
    .gold-accent {
        color: #D4AF37;
    .gold-accent {
        color: #D4AF37;
    }
    
    /* Custom Header Styles */
    .custom-header {
        background-color: #000000;
        padding: 40px 20px;
        color: #ffffff;
        margin: -4rem -5rem 2rem -5rem; /* Increased negative top margin to pull it up */
        text-align: center;
    }
    .custom-header h1 {
        color: #ffffff;
        margin: 0 0 20px 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .badge-container {
        display: flex;
        justify-content: center;
        gap: 15px;
        flex-wrap: wrap;
    }
    .info-badge {
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 50px;
        padding: 5px 20px;
        font-size: 0.9rem;
        color: #e0e0e0;
        display: flex;
        align-items: center;
        background: rgba(255, 255, 255, 0.05);
    }
    .info-badge strong {
        color: #ffffff;
        margin-left: 5px;
    }
    
    /* Force buttons to respect newlines */
    div[data-testid="stButton"] > button > div > p {
        white-space: pre-wrap;
        line-height: 1.2;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---

def parse_date(date_val):
    """Robust date parsing helper."""
    if pd.isna(date_val): return None
    if isinstance(date_val, str):
        if len(date_val) == 10 and date_val[4] == '-' and date_val[7] == '-': return date_val
        try: return pd.to_datetime(date_val).strftime('%Y-%m-%d')
        except: return None
    try: return pd.to_datetime(date_val).strftime('%Y-%m-%d')
    except: return None

def load_data(keyword):
    """Load report data from storage."""
    return github_storage.load_report(keyword)

def run_new_analysis(keyword, start_date, end_date):
    """Run the analysis pipeline."""
    # 1. Collect
    result = news_collector.search_naver_news(keyword, str(start_date), str(end_date))
    if not result['success']:
        return False, result.get('error')
    
    articles = result['article_details']
    if not articles:
        return False, "No articles found."

    # 2. Sentiment (Fallback to Neutral if fails to save time/cost or on error)
    # in this simplified flow, we'll run it but handle errors gracefully
    try:
        sentiments = gemini_analyzer.analyze_sentiment_batch(articles)
    except:
        sentiments = ["Neutral"] * len(articles)
        
    for i, art in enumerate(articles):
        art['sentiment'] = sentiments[i] if i < len(sentiments) else "Neutral"
    
    # 3. Generate Report
    pos = sentiments.count('Positive')
    neg = sentiments.count('Negative')
    neu = sentiments.count('Neutral')
    sentiment_summary = f"Positive: {pos}, Negative: {neg}, Neutral: {neu}"
    
    report_json = gemini_analyzer.generate_issue_report(keyword, articles, sentiment_summary)
    
    # 4. Save
    data = {
        "keyword": keyword,
        "period": f"{start_date} ~ {end_date}",
        "summary_stats": { "positive": pos, "negative": neg, "neutral": neu },
        "report": report_json,
        "articles": articles,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if github_storage.save_report(keyword, data):
        return True, "Success"
    else:
        return False, "Failed to save"

# --- Main App Layout ---

# Sidebar for Navigation/Admin
with st.sidebar:
    st.title("Settings")
    
    # Keyword Loader
    try:
        keywords = github_storage.get_keyword_list()
    except:
        keywords = []
    
    # No auto-selection: Always start with "Select..." to show welcome page
    default_idx = 0
        
    selected_keyword = st.selectbox("Load Report", ["Select..."] + keywords, index=default_idx)
    
    st.divider()
    
    # Admin Protection
    if not st.session_state.is_admin:
        with st.expander("🔐 Admin Access"):
            pwd = st.text_input("Password", type="password")
            if st.button("Login"):
                if pwd == "123456789":
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("Invalid password")
    
    # New Analysis (Only for Admin)
    if st.session_state.is_admin:
        st.subheader("New Analysis")
        new_kw = st.text_input("Keyword")
        c1, c2 = st.columns(2)
        s_date = c1.date_input("Start", datetime.now())
        e_date = c2.date_input("End", datetime.now())
        
        if st.button("Run Analysis", type="primary"):
            with st.spinner("Analyzing..."):
                success, msg = run_new_analysis(new_kw, s_date, e_date)
                if success:
                    st.success("Done!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Error: {msg}")
            
        st.divider()
        st.caption("Maintenance")
        
        # Format Update Button (Regenerate Report with existing data)
        # Only available if a keyword is selected and data exists
        sidebar_data = None
        if selected_keyword and selected_keyword != "Select...":
             sidebar_data = load_data(selected_keyword)
             
        if selected_keyword and selected_keyword != "Select..." and sidebar_data:
            if st.button("Format Update", help="Regenerate report text with latest format using existing data"):
                data = sidebar_data # Use loaded data
                with st.spinner("Updating report format..."):
                    try:
                        # Re-run Gemini analysis with existing articles
                        articles = data.get('articles', [])
                        # Recalculate basic sentiment summary for context
                        # We use stored summary stats if available, or just pass a simple string
                        stats = data.get('summary_stats', {})
                        pos = stats.get('positive', 0)
                        neg = stats.get('negative', 0)
                        neu = stats.get('neutral', 0)
                        sentiment_summary = f"Positive: {pos}, Negative: {neg}, Neutral: {neu}"
                        
                        new_report_json = gemini_analyzer.generate_issue_report(selected_keyword, articles, sentiment_summary)
                        
                        # Update data object
                        data['report'] = new_report_json
                        data['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Save
                        if github_storage.save_report(selected_keyword, data):
                            st.success("Report updated!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to save updated report.")
                    except Exception as e:
                        st.error(f"Update failed: {e}")
        
        # Delete Keyword Section
        st.divider()
        st.caption("⚠️ Danger Zone")
        
        if keywords:  # Only show if there are keywords to delete
            delete_keyword = st.selectbox("Select Keyword to Delete", ["Select..."] + keywords, key="delete_select")
            
            if delete_keyword and delete_keyword != "Select...":
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.warning(f"⚠️ Delete '{delete_keyword}'?")
                with col2:
                    if st.button("🗑️ Delete", type="secondary", use_container_width=True):
                        if github_storage.delete_report(delete_keyword):
                            st.success(f"Deleted '{delete_keyword}'")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Delete failed")
            
        if st.button("Logout"):
            st.session_state.is_admin = False
            st.rerun()

# Main Content Area

if selected_keyword and selected_keyword != "Select...":
    data = load_data(selected_keyword)
    if not data and selected_keyword == "흑백요리사":
        # Handle case where default doesn't exist yet
        st.info("Creating default report for '흑백요리사'...")
        # Optional: could auto-trigger analysis here if needed, but safer to just show "Not found" 
        # but let's assume it might be there or user will run it.
        # For now, if load fails, show error.
        pass

    if data:
        # Parse JSON Report
        report = data.get('report', {})
        if isinstance(report, str):
            try:
                report = json.loads(report)
            except Exception as e:
                st.error(f"Failed to parse report data: {e}")
                report = {}
        
        if 'error' in report:
            error_msg = report.get('error', '')
            
            # Special handling for "model not found" errors (stale data)
            if "not found" in str(error_msg) or "404" in str(error_msg):
                st.error(f"⚠️ 저장된 분석 결과에 오류가 있습니다 (이전 버전 모델 참조 등).")
                st.info("💡 **해결 방법**: 우측 사이드바의 **'Format Update'** 버튼을 누르거나, **[New Analysis]**를 실행하여 최신 모델(Gemini 2.5)로 다시 분석해주세요.")
                with st.expander("상세 오류 내용 (Cached Error)"):
                    st.code(error_msg)
            else:
                st.error(f"❌ Analysis Error: {error_msg}")
            
            # Show error type if available
            if 'error_type' in report:
                st.warning(f"Error Type: {report.get('error_type')}")
            
            # Show traceback in expander for debugging
            if 'traceback' in report:
                with st.expander("🔍 Show Error Details (for debugging)"):
                    st.code(report.get('traceback'), language='python')
            
            # Show raw response if available
            if 'raw_response' in report:
                with st.expander("📄 Show AI Response"):
                    st.text(report.get('raw_response')[:2000])  # Limit to 2000 chars
            
        # --- Routing Logic ---
        # Check for query param 'date' to trigger Daily View
        # Compatible with Streamlit > 1.30 (st.query_params)
        query_params = st.query_params
        q_date = query_params.get("date", None)
        
        # If query param is set, overrid session state
        if q_date:
            st.session_state.selected_date = q_date

        # 1. Custom Header
        article_count = len(data.get('articles', []))
        period_str = data.get('period', '-')
        
        # 1. Custom Header (MOVED TO CONDITIONAL VIEWS)
        article_count = len(data.get('articles', []))
        period_str = data.get('period', '-')
         
        # Make space for normal content (margin removed by header negative margin)
        st.write("") 
        st.write("")

        # 2. Hero Chart (Volume with Peaks) - The "Gold" Chart
        if 'articles' in data:
            df = pd.DataFrame(data['articles'])
            df['date'] = df['date'].apply(parse_date)
            df = df.dropna(subset=['date'])
            
            daily_vol = df.groupby('date').size().reset_index(name='count')
            
            # Ensure full date range (Continuous Timeline)
            if not daily_vol.empty:
                # Convert to datetime for range generation
                daily_vol['date'] = pd.to_datetime(daily_vol['date'])
                min_date = daily_vol['date'].min()
                max_date = daily_vol['date'].max()
                
                # Create date range
                full_range = pd.date_range(start=min_date, end=max_date)
                
                # Reindex
                daily_vol = daily_vol.set_index('date').reindex(full_range, fill_value=0).reset_index()
                daily_vol.columns = ['date', 'count']
                
                # Convert back to string for consistency
                daily_vol['date'] = daily_vol['date'].dt.strftime('%Y-%m-%d')
            
            # Create Gold Area Chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily_vol['date'], 
                y=daily_vol['count'],
                fill='tozeroy',
                mode='lines+markers',
                line=dict(color='#000000', width=3, shape='spline'), # Black color
                fillcolor='rgba(200, 200, 200, 0.3)', # Light Gray
                name='Volume'
            ))
            
            # Annotations from Report Peaks
            if 'peak_analysis' in report:
                for peak in report['peak_analysis']:
                    p_date = peak.get('date')
                    # Find y value for this date
                    row = daily_vol[daily_vol['date'] == p_date]
                    if not row.empty:
                        y_val = row['count'].values[0]
                        fig.add_annotation(
                            x=p_date, y=y_val,
                            text=f"<b>{peak.get('reason', '')}</b>",
                            showarrow=True,
                            arrowhead=2,
                            yshift=10,
                            bgcolor="rgba(255,255,255,0.8)",
                            bordercolor="#D4AF37"
                        )

            fig.update_layout(
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=20, b=20, l=40, r=40),
                xaxis=dict(
                    showgrid=True, 
                    gridcolor='#f0f0f0',
                    range=[min_date, max_date], # Clamp to actual data range
                    fixedrange=True # Prevent zooming out to empty space
                ),
                yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
            )
            # --- Shared Data Preparation ---
            daily_data = daily_vol.sort_values('date')
            dates = daily_data['date'].tolist()
            counts = daily_data['count'].tolist()
            daily_trends = report.get('daily_trends', [])

            # --- VIEW SWITCHING ---
            
            if st.session_state.selected_date and q_date:
                # =========================================================
                # VIEW 1: DAILY REPORT PAGE
                # =========================================================
                
                # --- State Initialization for Daily View ---
                if 'daily_lang' not in st.session_state:
                    st.session_state.daily_lang = 'KR'
                if 'daily_translations' not in st.session_state:
                    st.session_state.daily_translations = {}

                sel_date = st.session_state.selected_date
                
                # Header Date String
                try:
                    dt_obj = datetime.strptime(sel_date, "%Y-%m-%d")
                    header_date_str = dt_obj.strftime("%Y년 %m월 %d일")
                except:
                    header_date_str = sel_date
                
                # Title Construction: Keyword + Date + Media Analysis
                # e.g. "흑백요리사 2026년 1월 1일 미디어 분석"
                keyword = data.get('keyword', '이슈')
                page_title = f"{keyword} {header_date_str} 미디어 분석"
                if st.session_state.daily_lang == 'EN':
                     # Simple English conversion for title
                     page_title = f"{keyword} Media Analysis - {sel_date}"

                # --- Top Control Bar (Above Header) ---
                # Layout: [Spacer (Left, 3)] [Controls (Right, 2.5)]
                # Align Right Above the Black Box (Wider for Korean text)
                _, top_c2 = st.columns([3, 2.5])
                
                with top_c2:
                    # Control Buttons: KR | EN | RETURN
                    # Optimized ratio to fit "전체 리포트로 돌아가기" just right
                    b_c1, b_c2, b_c3 = st.columns([1, 1, 2.2])
                    if b_c1.button("KR", use_container_width=True):
                        st.session_state.daily_lang = 'KR'
                        st.rerun()
                    if b_c2.button("EN", use_container_width=True):
                        st.session_state.daily_lang = 'EN'
                        st.rerun()
                    if b_c3.button("전체 리포트로 돌아가기", use_container_width=True):
                        st.session_state.selected_date = None
                        st.query_params.clear()
                        st.rerun()
                
                # Daily Header: Left Aligned, Thin Black Box (Below Controls)
                st.markdown(f"""
                <div style="background-color:#000; padding: 1rem 2rem; border-radius: 5px; margin-bottom: 2rem; text-align: left;">
                    <h2 style='color: white; margin:0; font-size: 1.6rem; border-bottom: none;'>{page_title}</h2>
                </div>
                """, unsafe_allow_html=True)

                st.write("") # Spacing

                # Hero Graph with Highlight (Red Point)
                highlight_row = daily_vol[daily_vol['date'] == sel_date]
                if not highlight_row.empty:
                    hy_val = highlight_row['count'].values[0]
                    fig.add_trace(go.Scatter(
                        x=[sel_date], 
                        y=[hy_val],
                        mode='markers',
                        marker=dict(color='red', size=20, symbol='circle', line=dict(color='white', width=2)),
                        name='Selected Date',
                        showlegend=False
                    ))
                
                # Hide Legend for the entire Daily View Graph
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

                # 1. 요약 보고 (Executive Summary)
                st.header("1. 요약 보고 (Executive Summary)")
                
                # Context Math
                first_date_str = daily_vol['date'].min()
                try:
                    context_str = f"{header_date_str} 분석입니다."
                    if st.session_state.daily_lang == 'EN':
                        context_str = f"Analysis for {sel_date}."
                except:
                    context_str = f"{header_date_str} 분석입니다."

                daily_trends = report.get('daily_trends', [])
                day_summary = next((item for item in daily_trends if item['date'] == sel_date), None)
                
                # --- Content Translation Logic ---
                if day_summary and st.session_state.daily_lang == 'EN':
                    # Check Cache
                    if sel_date in st.session_state.daily_translations:
                        day_summary = st.session_state.daily_translations[sel_date]
                    else:
                        # Perform Translation
                        with st.spinner("Translating report to English..."):
                             trans_summary = gemini_analyzer.translate_daily_report(day_summary)
                             st.session_state.daily_translations[sel_date] = trans_summary
                             day_summary = trans_summary
                
                if day_summary:
                    # 1. Context Sentence
                    one_line = day_summary.get('one_line_summary', '')
                    if not one_line:
                        one_line = f"Start of media analysis."

                    # Combine logic (KR/EN)
                    if st.session_state.daily_lang != 'EN':
                         month_str = dt_obj.strftime("%m").lstrip('0')
                         day_str = dt_obj.strftime("%d").lstrip('0')
                         st.markdown(f"**{month_str}월 {day_str}일은 {one_line}**")
                    else:
                         st.markdown(f"**{sel_date}: {one_line}**")
                    
                    # 1.1 Narrative Summary (New Request)
                    narrative = day_summary.get('narrative_summary', '')
                    # Fallback to key_features list if narrative is missing (backward compatibility)
                    if not narrative:
                        k_feats = day_summary.get('key_features', [])
                        if k_feats:
                            narrative = " ".join(k_feats)
                    
                    if narrative:
                        st.write("")
                        st.markdown(f"{narrative}")

                    # 1.2 Sub-topics Analysis
                    sub_topics = day_summary.get('sub_topics', [])
                    
                    if sub_topics:
                        total_daily_count = highlight_row['count'].values[0] if not highlight_row.empty else 0
                        
                        # Use actual total from data if possible, or sum of subtopics
                        # valid_sum = sum(int(t.get('count',0)) for t in sub_topics if str(t.get('count',0)).isdigit())
                        
                        intro_text = f"{total_daily_count}건의 기사는 크게 {len(sub_topics)}가지 주제로 나뉩니다:"
                        if st.session_state.daily_lang == 'EN':
                            intro_text = f"The {total_daily_count} articles are divided into {len(sub_topics)} main topics:"
                            
                        st.write("")
                        st.markdown(f"{intro_text}")
                        
                        for idx, topic in enumerate(sub_topics, 1):
                            t_name = topic.get('name', 'General')
                            t_cnt = topic.get('count', '-')
                            t_pct = topic.get('percent', '-')
                            t_ex = topic.get('examples', '')
                            t_desc = topic.get('description', '')
                            # Modified format: 1) Topic (Count, %) - Description
                            if t_desc:
                                st.markdown(f"&nbsp;&nbsp;{idx}) **{t_name}** ({t_cnt}건, {t_pct}%) - {t_desc}")
                            else:
                                st.markdown(f"&nbsp;&nbsp;{idx}) **{t_name}** ({t_cnt}건, {t_pct}%)")

                if day_summary:
                    # 1. Executive Summary Divider (Ensure it's after content)
                    st.divider()

                    # 2. 주요 분석 (Key Findings)
                    st.header("2. 주요 분석 (Key Findings)")
                    
                    key_findings = day_summary.get('key_findings', {})
                    if key_findings:
                        # 2.1 Article Analysis
                        aa = key_findings.get('article_analysis', [])
                        if aa:
                            st.markdown("### 2.1 핵심 기사 분석")
                            for item in aa:
                                st.markdown(f"- {item}")
                        
                        # 2.2 Subject Direction
                        mf = key_findings.get('media_focus', [])
                        if mf:
                            st.write("")
                            st.markdown("### 2.2 주요 매체별 관심 방향")
                            for item in mf:
                                st.markdown(f"- {item}")

                        # 2.3 Dynamics
                        dy = key_findings.get('dynamics', [])
                        if dy:
                            st.write("")
                            st.markdown("### 2.3 브랜드/인물 역학")
                            for item in dy:
                                st.markdown(f"- {item}")
                    else:
                        st.info("No Key Findings Analysis Available.")

                    # 2. Key Findings Divider (Ensure it's after content)
                    st.divider()

                    # 3. 상세 분석 (Detailed Analysis)
                    st.header("3. 상세 분석 (Detailed Analysis)")
                    
                    daily_themes = day_summary.get('daily_themes', [])
                    if daily_themes:
                        for idx, theme in enumerate(daily_themes, 1):
                            t_name = theme.get('name', 'General')
                            t_stats = theme.get('stats', '')
                            t_msg = theme.get('core_message', '')
                            t_details = theme.get('details', [])
                            t_traits = theme.get('reporter_traits', '')
                            t_impact = theme.get('social_impact', '')
                            
                            # Theme Sub-Header
                            st.markdown(f"#### ■ THEME {idx}: {t_name} <span style='color:#666; font-size:0.9em;'>({str(t_stats).replace('articles', '건')})</span>", unsafe_allow_html=True)
                            st.write("")
                            
                            # Core Message
                            st.markdown(f"- **핵심 메시지**: \"{t_msg}\"")
                            st.write("")
                            
                            # Details
                            if t_details:
                                narrative_details = []
                                for det in t_details:
                                    if isinstance(det, dict):
                                        d_title = det.get('title', '')
                                        d_content = det.get('content', '')
                                        narrative_details.append(f"{d_title}: {d_content}")
                                    else:
                                        narrative_details.append(str(det))
                                
                                st.markdown(f"- **세부 내용**: {' '.join(narrative_details)}")
                                st.write("")
                            
                            # Reporter Traits (converted to bullet point)
                            if t_traits:
                                st.markdown(f"- **기자의 보도 특성**: {t_traits}")
                                st.write("")
                            
                            # Social Impact (converted to bullet point)
                            if t_impact:
                                st.markdown(f"- **사회적 영향**: {t_impact}")
                                st.write("")
                            
                    else:
                        st.info("구체적인 상세 분석 데이터가 없습니다. Format Update를 실행해주세요.")

                st.divider()

                # 4. 키워드 분석 (Keyword Analysis)
                st.header("4. 키워드 분석 (Keyword Analysis)")
                
                # Use Global Keyword Analysis as Daily Specific isn't granularly available yet
                # ideally we would filter this, but for now we show the context
                k_analysis = report.get('keyword_analysis', {})
                
                col_t, col_p, col_b = st.columns(3)
                
                with col_t:
                    st.subheader("Topics")
                    top = k_analysis.get('topics', [])
                    if top:
                        t_df = pd.DataFrame(top)[['rank', 'keyword', 'count']]
                        t_df = t_df.sort_values('count', ascending=False)
                        st.dataframe(t_df, hide_index=True, use_container_width=True)
                    else:
                        st.write("-")

                with col_p:
                    st.subheader("People")
                    ppl = k_analysis.get('people', [])
                    if ppl:
                        p_df = pd.DataFrame(ppl)[['rank', 'keyword', 'count']]
                        p_df = p_df.sort_values('count', ascending=False)
                        st.dataframe(p_df, hide_index=True, use_container_width=True)
                    else:
                        st.write("-")

                with col_b:
                    st.subheader("Brands")
                    brand = k_analysis.get('brands_companies', [])
                    if brand:
                        b_df = pd.DataFrame(brand)[['rank', 'keyword', 'count']]
                        b_df = b_df.sort_values('count', ascending=False)
                        st.dataframe(b_df, hide_index=True, use_container_width=True)
                    else:
                        st.write("-")

                st.divider()

                # 5. 주요 보도 기사
                st.header("5. 주요 보도 기사")
                
                # Full Article List with No. and Key People
                day_articles = df[df['date'] == sel_date]
                if not day_articles.empty:
                    display_df = day_articles[['date', 'title', 'press', 'link']].copy()
                    
                    # Add No. Column (1-based index)
                    display_df.insert(0, 'No.', range(1, len(display_df) + 1))
                    
                    # Add Key People Column (Matched from title against daily people)
                    kp_raw = day_summary.get('key_people', '-') if day_summary else '-'
                    if kp_raw and kp_raw != '-':
                        # Split by comma to get individual names
                        all_kp_list = [p.strip() for p in kp_raw.replace(',', ' ').split() if p.strip()]
                        
                        def get_article_kp(row_title):
                            found = [p for p in all_kp_list if p in row_title]
                            return ", ".join(found) if found else "-"
                            
                        display_df['key_people'] = display_df['title'].apply(get_article_kp)
                    else:
                        display_df['key_people'] = '-'
                    
                    st.dataframe(
                        display_df,
                        column_config={
                            "No.": st.column_config.NumberColumn("No.", format="%d", width="small"),
                            "date": st.column_config.TextColumn("Date", width="small"),
                            "title": st.column_config.TextColumn("Headline", width="large"),
                            "press": st.column_config.TextColumn("Press", width="small"),
                            "link": st.column_config.LinkColumn("Link"),
                            "key_people": st.column_config.TextColumn("Key People", width="medium")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Excel Download Logic
                    try:
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            display_df.to_excel(writer, index=False, sheet_name='Articles')
                        
                        excel_data = output.getvalue()
                        
                        # Filename: Keyword_SelectedDate_TodayDate.xlsx
                        today_str = datetime.now().strftime("%Y%m%d")
                        clean_keyword = data['keyword'].replace(" ", "_")
                        clean_sel_date = sel_date.replace("-", "")
                        file_name = f"{clean_keyword}_{clean_sel_date}_{today_str}.xlsx"
                        
                        st.download_button(
                            label="Download as Excel",
                            data=excel_data,
                            file_name=file_name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception as e:
                        st.error(f"Excel generation failed: {e}")
                else:
                    if not day_summary:
                        st.info("데이터가 없습니다.")

                st.divider()
                
                # Bottom Navigation: Return to Global Report
                col1, col2, col3 = st.columns([3, 3, 2])
                with col3:
                    if st.button("전체 리포트로 돌아가기", key="btn_return_global", use_container_width=True):
                        if "date" in st.query_params:
                            del st.query_params["date"]
                        st.rerun()

            else: 
                # =========================================================
                # VIEW 2: MAIN DASHBOARD (Default)
                # =========================================================
                
                # --- State Initialization for Global View ---
                if 'global_lang' not in st.session_state:
                    st.session_state.global_lang = 'KR'
                if 'global_translations_cache' not in st.session_state:
                    st.session_state.global_translations_cache = {}

                # Create Header Layout with Control Buttons
                h_col1, h_col2 = st.columns([4, 1])
                with h_col2:
                    # Global Language Controls
                    b_gl1, b_gl2 = st.columns(2)
                    if b_gl1.button("KR", key="btn_global_kr", use_container_width=True):
                        st.session_state.global_lang = 'KR'
                        st.rerun()
                    if b_gl2.button("EN", key="btn_global_en", use_container_width=True):
                        st.session_state.global_lang = 'EN'
                        st.rerun()

                # --- Content Translation Logic ---
                if st.session_state.global_lang == 'EN':
                     # Check Cache for this specific report (using keyword as key proxy, or a hash)
                     cache_key = f"{data['keyword']}_{len(data.get('daily_trends', []))}" 
                     
                     if cache_key in st.session_state.global_translations_cache:
                         report = st.session_state.global_translations_cache[cache_key]
                     else:
                         with st.spinner("Translating Global Report to English..."):
                             trans_report = gemini_analyzer.translate_global_report(report)
                             st.session_state.global_translations_cache[cache_key] = trans_report
                             report = trans_report

                # Render Main Header (Only for Main Dashboard)
                st.markdown(f"""
                <div class="custom-header">
                    <h1>{data['keyword']} {'Media Analysis Report' if st.session_state.global_lang == 'EN' else '미디어 분석 리포트'}</h1>
                    <div class="badge-container">
                        <div class="info-badge">
                            {'Articles' if st.session_state.global_lang == 'EN' else '기사'} : {'Naver ' + data['keyword'] + ' Search Total' if st.session_state.global_lang == 'EN' else '네이버 \'' + data['keyword'] + '\' 키워드 검색 총'} <strong>{article_count}{' articles' if st.session_state.global_lang == 'EN' else '건'}</strong>
                        </div>
                        <div class="info-badge">
                            {'Period' if st.session_state.global_lang == 'EN' else '기간'} : <strong>{period_str}</strong>
                        </div>
                        <div class="info-badge">
                            {'Analysis' if st.session_state.global_lang == 'EN' else '분석'} : <strong>Macoll Marslab</strong>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Render Main Graph (No red point)
                st.plotly_chart(fig, use_container_width=True)
                
                # --- Daily Analysis Buttons (Grid) ---
                st.write("")
                # Use columns to create a button bar feel
                # Grid Layout: 5 columns per row
                
                # Helper to chunk list
                def chunker(seq, size):
                    for i in range(0, len(seq), size):
                        yield seq[i:i + size]
                        
                chunked_data = list(zip(dates, counts))
                
                for chunk in chunker(chunked_data, 5):
                    cols = st.columns(5)
                    for i, (date, count) in enumerate(chunk):
                        # Find topic for this date
                        topic = ""
                        day_data = next((item for item in daily_trends if item['date'] == date), None)
                        if day_data:
                            # Use new 'topic_keyword' if available
                            topic = day_data.get('topic_keyword', '')
                            
                            if not topic:
                                # Fallback logic
                                issue_text = day_data.get('key_issue', '')
                                first_part = issue_text.split(',')[0].split('.')[0]
                                first_part = first_part.replace("흑백요리사2", "").replace("흑백요리사", "").strip()
                                if len(first_part) > 8:
                                    topic = first_part[:7] + ".."
                                else:
                                    topic = first_part
                                
                        # Format: MM-DD \n Keyword
                        date_str = date[5:]
                        if topic:
                            btn_label = f"{date_str}\n{topic}"
                        else:
                            btn_label = f"{date_str}\n({count})"
                        
                        if cols[i].button(btn_label, key=f"btn_{date}", use_container_width=True):
                            st.query_params["date"] = date
                            st.rerun()

                st.divider()

                # 1. 요약 보고 (Executive Summary)
                hdr_1 = "1. 요약 보고 (Executive Summary)" if st.session_state.global_lang == 'KR' else "1. Executive Summary"
                st.header(hdr_1)
                exec_sum = report.get('executive_summary', {})
                
                # Narrative Tone Analysis
                tone = exec_sum.get('tone_analysis', '-')
                st.write(tone)
                st.write("")
                
                # Key Takeaways (list directly under narrative)
                for k in exec_sum.get('key_takeaways', []):
                    st.markdown(f"- {k}")

                st.divider()

                # 2. 일별 이슈 추이 (Issue Trends)
                hdr_2 = "2. 일별 이슈 추이 (Issue Trends)" if st.session_state.global_lang == 'KR' else "2. Daily Issue Trends"
                st.header(hdr_2)
                trends = report.get('daily_trends', [])
                if trends:
                    # Prepare formatted dataframe
                    formatted_trends = []
                    for t in trends:
                        # Date: MM/DD
                        d_raw = t.get('date', '')
                        try:
                            d_obj = datetime.strptime(d_raw, "%Y-%m-%d")
                            d_str = d_obj.strftime("%m/%d")
                        except:
                            d_str = d_raw

                        # Tone: Use new pre-formatted stat string
                        tone_display = t.get('sentiment_stat', t.get('dominant_sentiment', '-'))
                        
                        formatted_trends.append({
                            "Date": d_str,
                            "Vol": f"{t.get('volume', 0)}건",
                            "Issue": t.get('issue_short', t.get('key_issue', '-')),
                            "People": t.get('key_people', '-'),
                            "Tone": tone_display
                        })
                    
                    t_df = pd.DataFrame(formatted_trends)
                    st.dataframe(
                        t_df,
                        column_config={
                            "Date": st.column_config.TextColumn("Date", width="small"),
                            "Vol": st.column_config.TextColumn("Vol", width="small"),
                            "Issue": st.column_config.TextColumn("Issue", width="medium"),
                            "People": st.column_config.TextColumn("People", width="medium"),
                            "Tone": st.column_config.TextColumn("Tone", width="medium")
                        },
                        hide_index=True,
                        use_container_width=True
                    )

                st.divider()

                # 3. 키워드 분석 (Keyword Analysis)
                hdr_3 = "3. 키워드 분석 (Keyword Analysis)" if st.session_state.global_lang == 'KR' else "3. Keyword Analysis"
                st.header(hdr_3)
                k_analysis = report.get('keyword_analysis', {})
                
                col_t, col_p, col_b = st.columns(3)
                
                with col_t:
                    st.subheader("Topics")
                    topics = k_analysis.get('topics', [])
                    if topics:
                        t_df = pd.DataFrame(topics)[['rank', 'keyword', 'count']]
                        t_df = t_df.sort_values('count', ascending=False)
                        t_df['rank'] = range(1, len(t_df) + 1)
                        st.dataframe(t_df, hide_index=True, use_container_width=True)
                    else:
                        st.write("No data")

                with col_p:
                    st.subheader("People")
                    people = k_analysis.get('people', [])
                    if people:
                        p_df = pd.DataFrame(people)[['rank', 'keyword', 'count']]
                        p_df = p_df.sort_values('count', ascending=False)
                        p_df['rank'] = range(1, len(p_df) + 1)
                        st.dataframe(p_df, hide_index=True, use_container_width=True)
                    else:
                        st.write("No data")

                with col_b:
                    st.subheader("Brands")
                    brand = k_analysis.get('brands_companies', [])
                    if brand:
                        b_df = pd.DataFrame(brand)[['rank', 'keyword', 'count']]
                        b_df = b_df.sort_values('count', ascending=False)
                        b_df['rank'] = range(1, len(b_df) + 1)
                        st.dataframe(b_df, hide_index=True, use_container_width=True)
                    else:
                        st.write("No data")

                st.divider()

                # 4. 핵심 주제별 상세 분석 (Detailed Topic Analysis)
                hdr_4 = "4. 핵심 주제별 상세 분석 (Detailed Topic Analysis)" if st.session_state.global_lang == 'KR' else "4. Detailed Topic Analysis"
                st.header(hdr_4)
                d_analysis = report.get('detailed_topic_analysis', {})
                
                # 4.1 화제 분석
                sh_4_1 = "4.1 화제 분석" if st.session_state.global_lang == 'KR' else "4.1 Hot Topics"
                st.subheader(sh_4_1)
                hot = d_analysis.get('hot_topics', [])
                if hot:
                    for item in hot:
                        st.markdown(f"- **{item.get('title')}**: {item.get('content')}")
                else:
                    st.write("No data")
                st.write("")
                
                # 4.2 논란 분석
                sh_4_2 = "4.2 논란 분석" if st.session_state.global_lang == 'KR' else "4.2 Controversy Analysis"
                st.subheader(sh_4_2)
                cont = d_analysis.get('controversy_analysis', [])
                if cont:
                    for item in cont:
                        st.markdown(f"- **{item.get('title')}**: {item.get('content')}")
                else:
                    st.write("No data")
                st.write("")

                # 4.3 기업 협업 트렌드
                sh_4_3 = "4.3 기업 및 브랜드 캠페인 분석" if st.session_state.global_lang == 'KR' else "4.3 Corporate & Brand Campaign Analysis"
                st.subheader(sh_4_3)
                collab = d_analysis.get('brand_collabs', {})
                ov = collab.get('overview', '')
                if ov:
                    label_ov = "트렌드 개요" if st.session_state.global_lang == 'KR' else "Trend Overview"
                    st.markdown(f"**{label_ov}**: {ov}")
                
                cases = collab.get('cases', [])
                if cases:
                    st.write("")
                    for c in cases:
                        b_name = c.get('brand_name', c.get('name', 'Brand'))
                        collab_with = c.get('collaborator', '-')
                        camp = c.get('campaign_detail', c.get('description', '-'))
                        mkt = c.get('marketing_action', '-')
                        
                        l_collab = "협업 대상" if st.session_state.global_lang == 'KR' else "Collaborator"
                        l_camp = "캠페인" if st.session_state.global_lang == 'KR' else "Campaign"
                        l_mkt = "마케팅 활동" if st.session_state.global_lang == 'KR' else "Marketing Action"

                        st.markdown(f"""
                        **■ {b_name}**
                        - **{l_collab}**: {collab_with}
                        - **{l_camp}**: {camp}
                        - **{l_mkt}**: {mkt}
                        """)
                else:
                    if not ov:
                        st.write("No data")


                st.divider()

                # 5. 시기별 보도 흐름 (Time-series Coverage Flow)
                hdr_5 = "5. 시기별 보도 흐름 (Time-series Coverage Flow)" if st.session_state.global_lang == 'KR' else "5. Time-series Coverage Flow"
                st.header(hdr_5)
                ts_flow = report.get('time_series_flow', {})
                
                if ts_flow:
                    for phase_key in ['early', 'middle', 'late']:
                        phase = ts_flow.get(phase_key)
                        if phase:
                            # Dynamic Phase Name
                            if st.session_state.global_lang == 'KR':
                                p_name_display = "초기 (Early)" if phase_key == 'early' else "중기 (Middle)" if phase_key == 'middle' else "말기 (Late)"
                            else:
                                p_name_display = phase_key.capitalize()
                                
                            st.subheader(f"■ {p_name_display}: {phase.get('period', '')}")
                            st.markdown(f"- **{'주요 보도' if st.session_state.global_lang == 'KR' else 'Key Reports'}**: {phase.get('major_reports', '-')}")
                            st.markdown(f"- **{'대중 반응' if st.session_state.global_lang == 'KR' else 'Public Reaction'}**: {phase.get('public_reaction', '-')}")
                            st.write("")
                else:
                    st.write("No data")

                st.divider()

                # 6. 종합 결론 (Business & Impact Conclusion)
                hdr_6 = "6. 종합 결론 (Business & Impact Conclusion)" if st.session_state.global_lang == 'KR' else "6. Comprehensive Conclusion"
                st.header(hdr_6)
                # Info box removed as requested
                st.write(report.get('conclusion', '-'))


    else:
        # Data missing for selected keyword
        # Show error page with selected keyword name
        st.markdown(f"""
        <div class="custom-header">
            <h1>{selected_keyword} 미디어 분석 리포트</h1>
            <div class="badge-container">
                <div class="info-badge">
                    기사 : <strong style='color:#ff4b4b'>데이터 없음</strong>
                </div>
                <div class="info-badge">
                    기간 : <strong>-</strong>
                </div>
                <div class="info-badge">
                    분석 : <strong>Macoll Marslab</strong>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.warning(f"⚠️ '{selected_keyword}'에 대한 분석 데이터가 아직 없습니다. 우측 사이드바의 [New Analysis]를 통해 분석을 시작해주세요. (비밀번호: 123456789)")
        
else:
    # Landing Page
    st.markdown("""
    ## Welcome to Macoll Monitoring Room
    
    This dashboard provides AI-powered insights into news trends.
    
    **Select a keyword** from the sidebar to view an existing report.
    
    **Login as Admin** in the sidebar to create new analysis reports.
    """)
