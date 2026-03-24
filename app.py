import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from streamlit_autorefresh import st_autorefresh

# --- [1. 자동 토큰 갱신 시스템] ---
def refresh_soopeh_token():
    """토큰이 만료되면 몰래 브라우저를 띄워 다시 로그인하고 새 쿠키를 가져옵니다."""
    options = Options()
    options.add_argument("--headless")  # 서버 환경을 위해 창 안 띄움
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        # 크롬 드라이버 자동 설정
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.soopeh.com/login")
        time.sleep(3) # 페이지 로딩 대기
        
        # 1. 아이디 입력 (찬후님 ID)
        driver.find_element(By.ID, "login-identifier").send_keys("yd60106")
        
        # 2. 비밀번호 입력 (관심술사가 맞춘 그 위치!)
        try:
            pw_field = driver.find_element(By.ID, "login-password")
        except:
            # ID가 다를 경우 대비해 타입으로 찾기
            pw_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
        # ★★★ 여기에 실제 비밀번호를 입력하세요 ★★★
        pw_field.send_keys("실제비밀번호입력") 
        pw_field.send_keys(Keys.ENTER)
        
        time.sleep(7) # 로그인 처리 및 쿠키 생성 대기 (넉넉하게)
        
        cookies = driver.get_cookies()
        driver.quit()
        
        # 새 쿠키 문자열 조립
        if cookies:
            new_cookie = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            return new_cookie
    except Exception as e:
        print(f"로그인 자동 갱신 실패: {e}")
        return None

# --- [2. 데이터 호출 로직 (수페 API + yfinance 백업)] ---
def get_soopeh_nvda():
    """수페 API를 우선 호출하고, 실패하면 yfinance로 자동 전환합니다."""
    # 세션에 쿠키 저장소 만들기
    if 'soopeh_cookie' not in st.session_state:
        # 초기값 (찬후님이 아까 찾았던 값)
        st.session_state.soopeh_cookie = "_ga=GA1.1.836760262.1774343435; soopeh_auth=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0ZmY0MjNmNS1iY2JlLTQzYWMtODFmNy1jOWUwYzg1YjdlMmUiLCJlbWFpbCI6bnVsbCwibG9naW5JZCI6InlkNjAxMDYiLCJuaWNrbmFtZSI6IuycoOywrO2bhCIsInJvbGUiOiJTVFVERU5UIiwidG9rZW5WZXJzaW9uIjozLCJ0b2tlblR5cGUiOiJhY2Nlc3MiLCJwYXNzd29yZENoYW5nZVJlcXVpcmVkIjpmYWxzZSwiaWF0IjoxNzc0MzQ2MzA0LCJleHAiOjE3NzQzNDcyMDR9.Dd59MK6rvsCsms6OGXOXrDd0C50L0ln4lKJeYSjXncQ"

    url = "https://api.soopeh.com/economy/stocks/quotes?symbols=NVDA"
    headers = {
        "cookie": st.session_state.soopeh_cookie,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "referer": "https://www.soopeh.com/",
        "origin": "https://www.soopeh.com"
    }

    try:
        res = requests.get(url, headers=headers, timeout=5)
        # 토큰 만료 시 자동 갱신
        if res.status_code != 200:
            new_c = refresh_soopeh_token()
            if new_c:
                st.session_state.soopeh_cookie = new_c
                headers["cookie"] = new_c
                res = requests.get(url, headers=headers, timeout=5)
        
        if res.status_code == 200:
            data = res.json()[0]
            return {'curr': data.get('price', 0), 'perc': data.get('changeRate', 0)}
    except:
        pass

    # [안전장치] 수페가 죽으면 yfinance 데이터 반환
    try:
        nvda_yf = yf.Ticker("NVDA").history(period="1d")
        if not nvda_yf.empty:
            return {'curr': nvda_yf['Close'].iloc[-1], 'perc': 0.0} # 백업용
    except:
        return None

# --- [3. 페이지 설정 및 디자인 (찬후님 원본 100% 동일)] ---
st.set_page_config(page_title="국내-해외 주식 현황 모니터링", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .main-title { font-size: 40px !important; font-weight: 800; color: #FFFFFF; text-align: center; margin-bottom: 5px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
    .sub-title { font-size: 18px; color: #888888; text-align: center; font-style: italic; margin-bottom: 30px; }
    div.stButton > button {
        width: 100%; border-radius: 12px; border: none; padding: 12px 20px;
        background: linear-gradient(135deg, #FF4B4B 0%, #764BA2 100%); 
        color: white !important; font-weight: 700; font-size: 16px;
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.4); 
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer;
    }
    div.stButton > button:hover { transform: translateY(-3px) scale(1.02); box-shadow: 0 8px 25px rgba(118, 75, 162, 0.6); background: linear-gradient(135deg, #FF6B6B 0%, #8A54C9 100%); }
    [data-testid="stMetric"] { background-color: #1e1e1e; padding: 20px; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=30000, key="auto_refresh_key")

# --- [4. 레이아웃 및 출력] ---
with st.sidebar:
    st.header("모니터링 설정")
    stock_dict = {
        "삼성전자 (Samsung)": {"id": "005930", "y": "005930.KS"},
        "엔비디아 (NVDA)": {"id": "NVDA", "y": "NVDA"},
        "알파벳(구글) (GOOG)": {"id": "GOOG", "y": "GOOG"}
    }
    selected_names = st.multiselect("종목 선택", list(stock_dict.keys()), default=["엔비디아 (NVDA)"])
    if st.button("새로고침 (수동)", use_container_width=True):
        st.rerun()

st.markdown('<p class="main-title">주식 추세 일람 그래프</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">𝕽𝖊𝖆𝖑-𝖙𝖎𝖒𝖊 𝕱𝖎𝖓𝖆𝖓𝖈𝖎𝖆𝖑 𝕸𝖔𝖓𝖎𝖙𝖔𝖗𝖎𝖓𝖌 𝕾𝖞𝖘𝖙𝖊𝖒</p>', unsafe_allow_html=True)

if selected_names:
    cols = st.columns(len(selected_names))
    for i, name in enumerate(selected_names):
        info = stock_dict[name]
        with cols[i]:
            # 엔비디아는 수페 API 사용
            if info["id"] == "NVDA":
                s_data = get_soopeh_nvda()
                if s_data:
                    st.metric(label=name, value=f"${s_data['curr']:,.2f}", delta=f"{s_data['perc']:+.2f}%")
            else:
                # 다른 종목은 기존 방식
                data_yf = yf.Ticker(info["y"]).history(period="1d", interval="1m")
                if not data_yf.empty:
                    curr = data_yf['Close'].iloc[-1]
                    st.metric(label=name, value=f"{curr:,.2f}")

            # 그래프 그리기 (기존 찬후님 로직 동일)
            ticker_obj = yf.Ticker(info["y"])
            data = ticker_obj.history(period="1d", interval="1m")
            if not data.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=data.index, y=data['Close'], fill='tozeroy', mode='lines', line=dict(color="#FF4B4B")))
                fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

st.divider()
st.text_area("메모장", placeholder="텍스트 입력..", height=120)
