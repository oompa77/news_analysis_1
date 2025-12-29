
구글의 최신 기술(Gemini 2.0 및 Antigravity 컨셉)과 Streamlit을 활용하여 **"AI 기반 이슈 리포트 대시보드"**를 완벽하게 구축하기 위한 **개발 명세서(Specification)**입니다.
이 내용을 바탕으로 AI 에이전트에게 코딩을 지시하거나 직접 개발을 진행하실 수 있습니다.
📝 Project Specification: AI Newsroom & Issue Report Dashboard
1. 프로젝트 개요
프로젝트 명: AI 기반 지능형 이슈 리포트 시스템
목적: 특정 키워드에 대한 네이버 뉴스를 수집, Gemini API로 감성 및 이슈 분석을 수행하여 의사결정용 1페이지 대시보드 제공
핵심 가치: 데이터 수집 자동화, AI 심층 분석, 인터랙티브 시각화, 서버리스 데이터 관리(GitHub+JSON)
2. 기술 스택 (Tech Stack)
Frontend/App: Streamlit
Language: Python 3.10+
AI Engine: Google Gemini API (Gemini 2.0 Flash / Pro)
Data API: Naver Search API (News)
Storage: GitHub Repository (JSON files)
Visualization: Plotly, Streamlit Components
Deployment: Streamlit Cloud
3. 시스템 아키텍처 및 데이터 흐름
관리자: 키워드/날짜 입력 → 네이버 API 뉴스 수집
분석 단계 1: 개별 뉴스 기사 Gemini 전송 → 감성 분류(우호/비판/중립)
분석 단계 2: 전체 뉴스 요약 Gemini 전송 → 5단계 심층 리포트 생성
저장: 결과를 JSON 형태로 GitHub 리포지토리 커밋(Push)
사용자: 대시보드 접속 → GitHub JSON 로드 → 인터랙티브 UI 출력
4. 기능 요구사항 (Functional Requirements)
4.1. 관리자 대시보드 (Admin Dashboard)
인증: 사이드바를 통한 간단한 Password 기반 접근 제어.
데이터 관리:
키워드 추가/삭제 및 뉴스 수집 기간(시작일~종료일) 설정.
'수집 및 AI 분석 실행' 버튼: 클릭 시 크롤링 + 감성분석 + 리포트 생성 프로세스 가동.
로그/통계:
stats.json을 활용한 일별 접속자 수 시각화 (Line Chart).
현재 저장된 키워드별 데이터 현황 요약.
4.2. 메인 이슈 리포트 (1-Page Newsroom)
Header Section:
키워드명 이슈 리포트 타이틀.
감성 지표 요약: 우호(파랑), 비판(빨강), 중립(회색) 건수 카드 출력.
Left Column (Interactive Area):
차트: 일자별 전체 기사량 및 감성별 기사수 파노라마 바 차트(Plotly).
필터링: 차트의 특정 막대(날짜/감성)를 클릭하면 하단 기사 리스트가 동적으로 업데이트.
기사 리스트: 최신순 30개 (매체명, 제목, 날짜). 제목 클릭 시 네이버 뉴스 원문 새창 열기.
Right Column (AI Report Area):
개요: 수집 정보 및 정량/정성 분석 요약.
여론의 흐름과 변곡점: [Phase]별 타임라인 분석 (월/일, 주요이슈, 지배여론, Turning Point).
핵심 이슈 분석: 3~4가지 핵심 쟁점 심층 정리.
유관 키워드 분석: 여론 주도 키워드 Top 10.
결론: 시나리오 2~3개 및 향후 과제 제시.
5. 데이터 스키마 (Data Schema - JSON)
5.1. news_data.json
code
JSON
{
  "keyword": "삼성전자",
  "period": "2024-05-01 ~ 2024-05-07",
  "summary_stats": { "positive": 45, "negative": 12, "neutral": 20 },
  "report": {
    "intro": "...",
    "phases": [ { "date": "05/01", "event": "...", "sentiment": "..." } ],
    "core_issues": [ "...", "..." ],
    "keywords": [ "반도체", "AI", "실적" ],
    "conclusion": "..."
  },
  "articles": [
    {
      "title": "기사 제목",
      "press": "언론사명",
      "date": "2024.05.01",
      "link": "naver_url",
      "sentiment": "우호적"
    }
  ]
}
6. 개발 가이드라인 (Implementation Logic)
6.1. Gemini Prompt Engineering (감성 분류용)
"다음 뉴스 제목과 요약을 읽고 [우호적, 비판적, 중립적] 중 하나로만 분류해줘. 다른 설명은 생략해."
6.2. Gemini Prompt Engineering (리포트 생성용)
"전체 뉴스 데이터를 분석하여 다음 5개 섹션(개요, 변곡점, 핵심 이슈, 키워드, 결론)을 전문가 스타일의 마크다운 형식으로 작성해줘. 각 섹션의 하위 항목을 반드시 포함할 것."
6.3. GitHub Storage 연동
PyGithub 라이브러리를 사용하여 repo.get_contents 및 repo.update_file 함수 구현.
Streamlit Secrets에 GH_TOKEN, REPO_NAME 저장 필수.
6.4. 인터랙티브 필터링 (Streamlit 1.35+ 전용)
code
Python
selection = st.plotly_chart(fig, on_select="rerun")
# selection 데이터를 추출하여 dataframe 필터링 로직 구현
7. 보안 및 배포 (Security & Deployment)
API Key 보호: st.secrets를 사용하여 네이버, 구글, 깃허브 키를 암호화 관리.
접속 제한: 관리자 대시보드는 st.text_input(type="password")를 통한 단순 세션 잠금 처리.
배포: GitHub 리포지토리와 Streamlit Cloud 연동.
이 명세서는 Google의 최신 Antigravity 모델/에이전트가 코드를 생성할 때 최적의 가이드라인으로 작용할 것입니다. 위 구조대로 개발을 시작해 보시겠습니까?