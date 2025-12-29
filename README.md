# News Analysis Dashboard

AI 기반 뉴스 분석 대시보드 - Naver 뉴스를 수집하고 Google Gemini API를 활용하여 감성 분석 및 이슈 리포트를 생성합니다.

## 설치 방법

1. **저장소 클론**
```bash
git clone git@github.com:oompa77/news_analysis_1.git
cd news_analysis_1
```

2. **필수 패키지 설치**
```bash
pip install -r requirements.txt
```

3. **환경 변수 설정**
`.env.example` 파일을 `.env`로 복사하고 필요한 API 키를 입력하세요:
```bash
cp .env.example .env
```

그런 다음 `.env` 파일을 열어서 다음 항목들을 설정하세요:
- `NAVER_CLIENT_ID`: Naver Developers에서 발급받은 Client ID
- `NAVER_CLIENT_SECRET`: Naver Developers에서 발급받은 Client Secret
- `GOOGLE_API_KEY`: Google AI Studio에서 발급받은 Gemini API Key
- `GITHUB_TOKEN`: GitHub Personal Access Token (리포트 저장용)
- `GITHUB_REPO`: GitHub 저장소 이름 (예: username/repo)
- `ADMIN_PASSWORD`: 대시보드 관리자 비밀번호

## 실행 방법

```bash
streamlit run app.py
```

## 주요 기능

- 📰 Naver 뉴스 자동 수집
- 🤖 AI 기반 감성 분석 (Positive/Negative/Neutral)
- 📊 시계열 감성 트렌드 시각화
- 📝 자동 이슈 리포트 생성
- 💾 GitHub을 통한 데이터 저장
- 📥 Excel/Word 형식으로 리포트 다운로드

## 필수 API 키 발급 방법

### 1. Naver API
- [Naver Developers](https://developers.naver.com/apps/#/register) 접속
- 애플리케이션 등록 후 Client ID/Secret 발급

### 2. Google Gemini API
- [Google AI Studio](https://aistudio.google.com/app/apikey) 접속
- API 키 생성

### 3. GitHub Token
- GitHub Settings > Developer settings > Personal access tokens
- `repo` 권한으로 토큰 생성

## 라이선스

MIT License
