import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import feedparser
from streamlit_autorefresh import st_autorefresh

# --- [1. 함수 정의 구역 (에러 방지를 위해 맨 위로 배치)] ---

def get_naver_stock(code):
    """네이버 파이낸스 실시간 주가 크롤링"""
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        price_tag = soup.select_one(".today .no_today .blind")
        curr_price = int(price_tag.text.replace(",", ""))
        diff_tag = soup.select_one(".today .no_exday .blind")
        diff_val = int(diff_tag.text.replace(",", ""))
        direction = soup.select_one(".today .no_exday .ico")
        if direction and "하락" in direction.text:
            diff_val = -diff_val
        prev_close = curr_price - diff_val
        perc = (diff_val / prev_close) * 100
        return {'curr': curr_price, 'perc': perc}
    except: return None

def get_stock_news(limit=6):
    """주식/증권 전용 RSS 뉴스 (매일경제 증권 카테고리)"""
    # 주식 관련 기사만 모아주는 전용 RSS 주소입니다.
    rss_url = "https://www.mk.co.kr/rss/30200001/" 
    try:
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            # 대안: 한국경제 증권 RSS
            feed = feedparser.parse("https://www.hankyung.com/feed/stock")
        
        return [{"title": entry.title, "link": entry.link} for entry in feed.entries[:limit]]
    except: return []

# --- [2. 페이지 설정 및 디자인] ---
st.set_page_config(page_title="주식 실시간 모니터링", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .main-title { font-size: 35px; font-weight: 800; color: white; text-align: center; margin-bottom: 20px; }
    div.stButton > button {
        width: 100%; border-radius: 10px; background: linear-gradient(135deg, #FF4B4B, #764BA2);
        color: white; font-weight: 700; border: none; padding: 10px;
    }
    [data-testid="stMetric"] { background-color: #1e1e1e; padding: 15px; border-radius: 12px; }
    .news-item { font-size: 13px; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 5px; }
    .news-link { color: #FF4B4B; text-decoration: none; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=60000, key="auto_refresh")

# --- [3. 사이드바 (설정 & 주식 뉴스)] ---
with st.sidebar:
    st.header("📊 설정")
    stock_dict = {
        "삼성전자 (Samsung)": {"id": "005930", "y": "005930.KS"},
        "SK 하이닉스 (Hynix)": {"id": "000660", "y": "000660.KS"},
        "엔비디아 (NVDA)": {"id": "NVDA", "y": "NVDA"},
        "애플 (AAPL)": {"id": "AAPL", "y": "AAPL"}
    }
    selected_names = st.multiselect("종목 선택", list(stock_dict.keys()),
