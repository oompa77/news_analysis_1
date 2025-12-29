import time
import urllib.parse
from datetime import datetime, timedelta
import re
import pandas as pd
import requests
import base64
import hmac
import hashlib
import urllib.request
import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

# === 네이버 검색 API (블로그 검색수) ===
# WARNING: Default API keys are for development only. 
# For production, MUST set NAVER_CLIENT_ID and NAVER_CLIENT_SECRET in .env file
client_id = os.getenv("NAVER_CLIENT_ID", "HHBfGIKdIWDWO0K3P3HS")
client_secret = os.getenv("NAVER_CLIENT_SECRET", "B3BXtg23wW")

# === 네이버 검색광고 API (키워드 검색수) ===
# WARNING: Default API keys are for development only.
# For production, MUST set NAVER_AD_API_KEY, NAVER_AD_SECRET_KEY, and NAVER_CUSTOMER_ID in .env file
BASE_URL = 'https://api.searchad.naver.com'
API_KEY = os.getenv("NAVER_AD_API_KEY", '01000000004b8e249bfd7c88669c7914bf989c1f5b0631dceda827bb2d5e88783f5f053e83')
SECRET_KEY = os.getenv("NAVER_AD_SECRET_KEY", 'AQAAAADuPBoHxgrVFVgv2S8dhv9bOqTON0A5zyCisQFyApUJzA==')
CUSTOMER_ID = os.getenv("NAVER_CUSTOMER_ID", '323565')

class Signature:
    @staticmethod
    def generate(timestamp, method, uri, secret_key):
        message = "{}.{}.{}".format(timestamp, method, uri)
        hash = hmac.new(bytes(secret_key, "utf-8"), bytes(message, "utf-8"), hashlib.sha256)
        hash.hexdigest()
        return base64.b64encode(hash.digest())

def get_header(method, uri, api_key=API_KEY, secret_key=SECRET_KEY, customer_id=CUSTOMER_ID):
    """API 요청 헤더 생성"""
    timestamp = str(round(time.time() * 1000))
    signature = Signature.generate(timestamp, method, uri, secret_key)
    return {
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Timestamp': timestamp,
        'X-API-KEY': api_key,
        'X-Customer': str(customer_id),
        'X-Signature': signature
    }

def get_blog_total_count(query):
    """블로그 검색수 조회 (네이버 검색 API)"""
    encText = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/blog?query={encText}&display=1"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    try:
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            result = json.loads(response_body.decode('utf-8'))
            return result.get('total', 0)
        else:
            print(f"블로그 API 오류: {rescode}")
            return 0
    except Exception as e:
        print(f"블로그 API 호출 오류: {e}")
        return 0

def get_keyword_search_count(keyword_to_search):
    """키워드 검색수 조회 (네이버 검색광고 API) - 연관검색어 포함"""
    uri = '/keywordstool'
    method = 'GET'
    
    # 요청 URL 생성 (쿼리 파라미터 포함)
    request_url = BASE_URL + uri + f'?hintKeywords={keyword_to_search}&showDetail=1'
    
    # 헤더 생성
    headers = get_header(method, uri)
    
    # API 요청 보내기
    try:
        response = requests.get(request_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('keywordList'):
                # 모든 키워드 정보 반환 (연관검색어 포함)
                keyword_list = []
                for keyword_data in result['keywordList']:
                    # 안전한 숫자 변환 함수
                    def safe_int(value, default=0):
                        if value is None:
                            return default
                        if isinstance(value, str):
                            # '< 10' 같은 문자열 처리
                            if '<' in value:
                                return 5  # '< 10'이면 5로 처리
                            try:
                                return int(value)
                            except ValueError:
                                return default
                        try:
                            return int(value)
                        except (ValueError, TypeError):
                            return default
                    
                    pc_count = safe_int(keyword_data.get('monthlyPcQcCnt', 0))
                    mobile_count = safe_int(keyword_data.get('monthlyMobileQcCnt', 0))
                    total_count = pc_count + mobile_count
                    
                    keyword_info = {
                        'keyword': keyword_data.get('relKeyword', keyword_to_search),
                        'pc_count': pc_count,
                        'mobile_count': mobile_count,
                        'total_count': total_count
                    }
                    keyword_list.append(keyword_info)
                
                return keyword_list
            else:
                print(f"키워드 '{keyword_to_search}' 정보를 찾을 수 없습니다.")
                return None
        else:
            print(f"키워드 API 오류: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"키워드 API 호출 오류: {e}")
        return None

def setup_driver():
    """Chrome WebDriver 설정"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 헤드리스 모드
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        # Security Risk Options (commented out for safety):
        # --disable-web-security: Disables same-origin policy, can expose to XSS attacks
        # --remote-debugging-port: Can conflict in containerized environments
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # ChromeDriverManager를 사용하여 드라이버 설치 및 설정
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"ChromeDriverManager 오류: {e}")
            # 대안: 직접 chromedriver 경로 사용
            driver = webdriver.Chrome(options=chrome_options)
        
        # 자동화 감지 방지
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
        
    except Exception as e:
        print(f"WebDriver 설정 오류: {e}")
        # 최후의 수단: 기본 설정으로 시도
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e2:
            print(f"WebDriver 기본 설정도 실패: {e2}")
            raise Exception("Chrome WebDriver를 설정할 수 없습니다. Chrome 브라우저가 설치되어 있는지 확인해주세요.")

def detect_news_site(url):
    """URL을 분석하여 뉴스 사이트 유형을 감지"""
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc.lower()
    
    if 'news.naver.com' in domain:
        return 'naver_news'
    elif 'search.naver.com' in domain and ('where=news' in url or 'ssc=tab.news' in url):
        return 'naver_search_news'
    elif 'news.google.com' in domain:
        return 'google_news'
    elif 'search.google.com' in domain and 'tbm=nws' in url:
        return 'google_search_news'
    elif 'news.daum.net' in domain:
        return 'daum_news'
    else:
        return 'unknown'

def get_article_selectors(site_type):
    """사이트 유형에 따른 기사 선택자 반환"""
    selectors = {
        'naver_news': {
            'articles': 'div.main_component.droppable',
            'title': 'a.news_tit',
            'link': 'a.news_tit',
            'press': 'a.press',
            'date': 'span.info'
        },
        'naver_search_news': {
            'articles': 'div.sds-comps-vertical-layout.sds-comps-full-layout.sKYUZNwnLHdgmIxCzyqY, div[class*="sds-comps-vertical-layout"], li[class*="bx"], div.news_wrap, div.news_area, div.news_box, div[class*="news"], li[class*="news"], div[class*="article"], li[class*="article"], div[class*="item"], li[class*="item"]',
            'title': 'span.sds-comps-text.sds-comps-text-ellipsis.sds-comps-text-ellipsis-1.sds-comps-text-type-headline1, a.news_tit, span[class*="headline"], span[class*="title"], a[class*="headline"], a[class*="title"], strong, h3, h4, a[href*="news"], a[href*="article"], a[class*="link"], a[class*="tit"]',
            'link': 'a[href*="http"] span.sds-comps-text.sds-comps-text-ellipsis.sds-comps-text-ellipsis-1.sds-comps-text-type-headline1, a[href*="news"], a[href*="article"], a[href*="yna.co.kr"], a[href*="news.naver.com"], a[href*="view"], a[href*="read"], a[class*="link"], a[class*="tit"]',
            'press': 'span.sds-comps-text.sds-comps-text-ellipsis.sds-comps-text-ellipsis-1.sds-comps-text-type-body2.sds-comps-text-weight-sm, span.sds-comps-profile-info-title-text, a.press, span[class*="press"], span[class*="source"], span[class*="author"], a[class*="info"], span[class*="profile-info-title-text"], img[alt*="로고"], img[alt*="logo"], span[class*="media"], span[class*="agency"]',
            'date': 'span.sds-comps-text.sds-comps-text-type-body2.sds-comps-text-weight-sm, span.sds-comps-profile-info-subtext, span.info, span[class*="date"], span[class*="time"], span[class*="profile-info-subtext"], time, div[class*="date"], div[class*="time"], em[class*="date"], em[class*="time"], span[class*="info"], span[class*="meta"]'
        },
        'google_news': {
            'articles': 'article, div[data-n-tid]',
            'title': 'h3, h4, a[data-n-tid]',
            'link': 'a[href*="news"], a[href*="article"]',
            'press': 'time + a, span[class*="source"], a[class*="source"]',
            'date': 'time, span[class*="date"], span[class*="time"]'
        },
        'daum_news': {
            'articles': 'li.news_item, div.news_item',
            'title': 'a.link_txt, strong.tit_txt',
            'link': 'a.link_txt',
            'press': 'span.info_news, span.txt_copyright',
            'date': 'span.info_time, span.txt_time'
        },
        'general_news': {
            'articles': 'article, div.news-item, div.article, li.news-item',
            'title': 'h1, h2, h3, h4, a[class*="title"], a[class*="headline"]',
            'link': 'a[href*="news"], a[href*="article"], a[href*="story"]',
            'press': 'span[class*="author"], span[class*="source"], span[class*="byline"], a[class*="author"]',
            'date': 'time, span[class*="date"], span[class*="time"], span[class*="published"]'
        }
    }
    return selectors.get(site_type, selectors['general_news'])

def parse_relative_date(date_text):
    if not date_text or date_text == "날짜 없음":
        return "날짜 없음"
    
    date_text = date_text.strip()
    today = datetime.now()
    
    # "N분 전" 패턴
    minute_match = re.search(r'(\d+)분\s*전', date_text)
    if minute_match:
        minutes = int(minute_match.group(1))
        target_date = today - timedelta(minutes=minutes)
        return target_date.strftime('%Y-%m-%d')
    
    # "N시간 전" 패턴
    hour_match = re.search(r'(\d+)시간\s*전', date_text)
    if hour_match:
        hours = int(hour_match.group(1))
        target_date = today - timedelta(hours=hours)
        return target_date.strftime('%Y-%m-%d')
    
    # "N일 전" 패턴
    day_match = re.search(r'(\d+)일\s*전', date_text)
    if day_match:
        days = int(day_match.group(1))
        target_date = today - timedelta(days=days)
        return target_date.strftime('%Y-%m-%d')
    
    # "N주 전" 패턴
    week_match = re.search(r'(\d+)주\s*전', date_text)
    if week_match:
        weeks = int(week_match.group(1))
        target_date = today - timedelta(weeks=weeks)
        return target_date.strftime('%Y-%m-%d')
    
    # "방금 전", "조금 전" 등
    if date_text in ["방금 전", "조금 전", "금방"]:
        return today.strftime('%Y-%m-%d')
    
    # "오늘" 패턴
    if "오늘" in date_text:
        return today.strftime('%Y-%m-%d')
    
    # "어제" 패턴
    if "어제" in date_text:
        yesterday = today - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')
    
    # "그제" 패턴
    if "그제" in date_text:
        day_before_yesterday = today - timedelta(days=2)
        return day_before_yesterday.strftime('%Y-%m-%d')
    
    # "이번 주" 패턴
    if "이번 주" in date_text:
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        return monday.strftime('%Y-%m-%d')
    
    # "지난 주" 패턴
    if "지난 주" in date_text:
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday + 7)
        return last_monday.strftime('%Y-%m-%d')
    
    # "이번 달" 패턴
    if "이번 달" in date_text:
        return today.replace(day=1).strftime('%Y-%m-%d')
    
    # "지난 달" 패턴
    if "지난 달" in date_text:
        if today.month == 1:
            last_month = today.replace(year=today.year-1, month=12, day=1)
        else:
            last_month = today.replace(month=today.month-1, day=1)
        return last_month.strftime('%Y-%m-%d')
    
    # "올해" 패턴
    if "올해" in date_text:
        return today.replace(month=1, day=1).strftime('%Y-%m-%d')
    
    # "작년" 패턴
    if "작년" in date_text:
        return today.replace(year=today.year-1, month=1, day=1).strftime('%Y-%m-%d')
    
    # YYYY.MM.DD 형식을 YYYY-MM-DD로 변환
    if re.match(r'\d{4}\.\d{1,2}\.\d{1,2}', date_text):
        return date_text.replace('.', '-')
    
    # YYYY-MM-DD 형식이면 그대로 반환
    if re.match(r'\d{4}-\d{1,2}-\d{1,2}', date_text):
        return date_text
    
    # 파싱 실패 시 None 반환 (날짜 정보 없음)
    return None

def extract_article_details(element, site_type):
    """기사 요소에서 상세 정보 추출"""
    selectors = get_article_selectors(site_type)
    
    # 언론사명 먼저 추출 (제목 검증에 사용)
    press = "매체명 없음"
    try:
        profile_info = element.find_element(By.CSS_SELECTOR, "div.sds-comps-profile-info")
        press_elem = profile_info.find_element(By.CSS_SELECTOR, "span.sds-comps-text.sds-comps-text-ellipsis.sds-comps-text-ellipsis-1.sds-comps-text-type-body2.sds-comps-text-weight-sm")
        press = press_elem.text.strip()
    except Exception:
        pass
        
    if press == "매체명 없음":
        for press_selector in selectors['press'].split(', '):
            try:
                press_elem = element.find_element(By.CSS_SELECTOR, press_selector.strip())
                press_text = press_elem.text.strip()
                if press_text and len(press_text) > 1:
                    press = press_text
                    break
            except Exception:
                continue
    
    # 제목 추출
    title = "제목 없음"
    invalid_titles = ["네이버뉴스", "네이버 뉴스", "NAVER", press]  # 유효하지 않은 제목들
    
    for title_selector in selectors['title'].split(', '):
        try:
            title_elem = element.find_element(By.CSS_SELECTOR, title_selector.strip())
            title_text = title_elem.text.strip()
            # 제목이 있고, 3글자 이상이며, 유효하지 않은 제목이 아닌 경우만 사용
            if title_text and len(title_text) > 3 and title_text not in invalid_titles:
                title = title_text
                break
        except Exception:
            continue
    
    # 링크 추출
    link = "#"
    try:
        # 1. 새로운 네이버 구조에서 링크 추출 시도
        title_link_elem = element.find_element(By.CSS_SELECTOR, "a[href*='http'] span.sds-comps-text.sds-comps-text-ellipsis.sds-comps-text-ellipsis-1.sds-comps-text-type-headline1")
        parent_link = title_link_elem.find_element(By.XPATH, "..")
        link = parent_link.get_attribute('href')
    except Exception:
        pass
        
    if link == "#" or not link.startswith('http'):
        for link_selector in selectors['link'].split(', '):
            try:
                link_elem = element.find_element(By.CSS_SELECTOR, link_selector.strip())
                link = link_elem.get_attribute('href')
                if link and link.startswith('http'):
                    break
            except Exception:
                continue
    
    
    # 날짜 추출
    date = None
    try:
        # 새로운 네이버 구조에서 날짜 추출
        profile_info = element.find_element(By.CSS_SELECTOR, "div.sds-comps-profile-info")
        date_elem = profile_info.find_element(By.CSS_SELECTOR, "span.sds-comps-text.sds-comps-text-type-body2.sds-comps-text-weight-sm")
        date_text = date_elem.text.strip()
        if date_text:
            date = parse_relative_date(date_text)
    except Exception:
        pass
    
    if not date or date == "날짜 없음":
        for date_selector in selectors['date'].split(', '):
            try:
                date_elem = element.find_element(By.CSS_SELECTOR, date_selector.strip())
                date_text = date_elem.text.strip()
                if date_text and len(date_text) > 0:
                    date = parse_relative_date(date_text)
                    if date and date != "날짜 없음":
                        break
            except Exception:
                continue
    
    # 날짜가 여전히 없으면 None으로 설정 (현재 날짜 사용하지 않음)
    if not date or date == "날짜 없음":
        date = None
    
    # 불필요한 요소 필터링
    filter_keywords = ["이 정보가 표시된 이유", "정보가 표시된 이유", "표시된 이유"]
    if any(keyword in title for keyword in filter_keywords):
        return None
    
    # 날짜가 없는 기사는 제외
    if not date:
        return None
    
    return {
        'title': title,
        'link': link,
        'press': press,
        'date': date
    }

def count_news_articles(url, start_date=None, end_date=None):
    """뉴스 기사 수 카운팅"""
    driver = None
    try:
        driver = setup_driver()
        driver.get(url)
        time.sleep(3)
        
        # 무한 스크롤
        scroll_count = 0
        last_height = driver.execute_script("return document.body.scrollHeight")
        no_change_count = 0
        max_scrolls = 100  # Increased from 30 to 100 for better coverage
        
        while scroll_count < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                no_change_count += 1
                if no_change_count >= 3:
                    break
            else:
                no_change_count = 0
            
            last_height = new_height
            scroll_count += 1
        
        # 더보기 버튼 (Simplified logic)
        try:
            more_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), '더보기')]")
            for button in more_buttons[:2]:
                driver.execute_script("arguments[0].click();", button)
                time.sleep(2)
        except:
            pass

        site_type = detect_news_site(url)
        selectors = get_article_selectors(site_type)
        article_elements = []
        
        for selector in selectors['articles'].split(', '):
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector.strip())
                if elements:
                    article_elements.extend(elements)
            except:
                continue
        
        article_details = []
        seen_links = set()
        
        for element in article_elements:
            try:
                details = extract_article_details(element, site_type)
                
                # None이면 건너뛰기 (필터링된 항목)
                if not details:
                    continue
                
                # 중복 체크
                if details['link'] in seen_links:
                    continue
                    
                # 날짜 필터링 (선택적)
                if start_date and end_date:
                     try:
                        article_date = datetime.strptime(details['date'], '%Y-%m-%d').date()
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                        if not (start_dt <= article_date <= end_dt):
                            continue
                     except:
                         pass
                
                seen_links.add(details['link'])
                article_details.append(details)
            except:
                continue
                
        return {
            'success': True,
            'total_articles': len(article_details),
            'article_details': article_details
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if driver:
            driver.quit()

def search_naver_news(keyword, start_date, end_date, time_range='all'):
    """네이버 뉴스 검색 및 기사 카운팅"""
    try:
        # 공백이 있는 키워드는 AND 검색으로 처리 (공백을 & 로 변환)
        # 예: "RSV 바이러스" -> "RSV & 바이러스"
        if ' ' in keyword:
            # 공백을 & 로 변환하여 AND 검색
            search_keyword = keyword.replace(' ', ' & ')
        else:
            # 단일 키워드는 그대로 사용
            search_keyword = keyword
        
        # URL 인코딩
        encoded_keyword = urllib.parse.quote(search_keyword)
        
        # 네이버 뉴스 상세검색 URL (사용자 제공 형식)
        # nso 파라미터: so:r (정확도순), p:from...to... (기간), a:all (전체)
        nso_param = f"so:r,p:from{start_date.replace('-', '')}to{end_date.replace('-', '')},a:all"
        encoded_nso = urllib.parse.quote(nso_param, safe=':,')
        
        search_url = (
            f"https://search.naver.com/search.naver?"
            f"ssc=tab.news.all&"
            f"where=news&"
            f"query={encoded_keyword}&"
            f"sm=tab_dgs&"
            f"sort=0&"
            f"pd=3&"
            f"ds={start_date.replace('-', '.')}&"
            f"de={end_date.replace('-', '.')}&"
            f"nso={encoded_nso}&"
            f"qdt=1"
        )
        
        # DEBUG: URL 출력
        print(f"\n=== 네이버 검색 URL ===")
        print(f"원본 키워드: {keyword}")
        print(f"검색 키워드: {search_keyword}")
        print(f"인코딩된 키워드: {encoded_keyword}")
        print(f"전체 URL: {search_url}")
        print("=" * 50 + "\n")
        
        return count_news_articles(search_url, start_date, end_date)
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
