import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh

# --- [추가] 수페 API 연동 함수 ---
def get_soopeh_nvda():
    """수페 서버에서 엔비디아 실시간 데이터를 가져옵니다."""
    url = "https://api.soopeh.com/economy/stocks/quotes"
    params = {"symbols": "NVDA"}
    
    # 찬후님이 찾으신 '마법의 열쇠' (쿠키)
    headers = {
        "cookie": "_ga=GA1.1.836760262.1774343435; soopeh_auth=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0ZmY0MjNmNS1iY2JlLTQzYWMtODFmNy1jOWUwYzg1YjdlMmUiLCJlbWFpbCI6bnVsbCwibG9naW5JZCI6InlkNjAxMDYiLCJuaWNrbmFtZSI6IuycoOywrO2bhCIsInJvbGUiOiJTVFVERU5UIiwidG9rZW5WZXJzaW9uIjozLCJ0b2tlblR5cGUiOiJhY2Nlc3MiLCJwYXNzd29yZENoYW5nZVJlcXVpcmVkIjpmYWxzZSwiaWF0IjoxNzc0MzQ2MzA0LCJleHAiOjE3NzQzNDcyMDR9.Dd59MK6rvsCsms6OGXOXrDd0C50L0ln4lKJeYSjXncQ; soopeh_csrf_v2=oIBBbLImBKAQcXYuc7IFLFIoRY1JT-GU",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "referer": "https://www.soopeh.com/",
        "origin": "https://www.soopeh.com"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0] # 첫 번째 종목(NVDA) 정보 반환
    except:
        pass
    return None

# --- 1. 페이지 설정 및 디자인 (기존 CSS 유지) ---
st.set_page_config(page_title="수페-해외 주식 실시간 모니터링", page_icon="📈", layout="wide")

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
    div.stButton > button:active { transform: translateY(1px) scale(0.95); box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2); }
    [data-testid="stMetric"] { background-color: #1e1e1e; padding: 20px; border-radius: 15px; box-shadow: inset 0 0 10px rgba(255,255,255,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 30초 자동 새로고침
st_autorefresh(interval=30000, key="auto_refresh_key")

# --- 2. 사이드바 (설정 메뉴) ---
with st.sidebar:
    st.header("모니터링 설정")
    st.info("💡 엔비디아는 수페 API와 실시간 연동됩니다.")
    stock_dict = {
        "삼성전자 (Samsung)": {"id": "005930", "type": "KR", "y": "005930.KS"},
        "현대자동차 (Hyundai)": {"id": "005380", "type": "KR", "y": "005380.KS"},
        "알파벳(구글) (GOOG)": {"id": "GOOG", "type": "US", "y": "GOOG"},
        "엔비디아 (NVDA)": {"id": "NVDA", "type": "SOOPEH", "y": "NVDA"}, # 타입을 SOOPEH로 변경
        "SK 하이닉스 (Hynix)": {"id": "000660", "type": "KR", "y": "000660.KS"},
        "넷플릭스(NFLX)": {"id": "NFLX", "type": "US", "y": "NFLX"}
    }
    selected_names = st.multiselect("종목 선택", list(stock_dict.keys()), default=["엔비디아 (NVDA)", "삼성전자 (Samsung)"])
    
    st.divider()
    if st.button("수동 새로고침", use_container_width=True):
        st.rerun()

# --- 3. 메인 화면 ---
st.markdown('<p class="main-title">찬후의 실시간 통합 모니터</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">𝕾𝖔𝖔𝖕𝖊𝖍 𝕬𝕻𝕴 & 𝖄𝖋𝖎𝖓𝖆𝖓𝖈𝖊 𝕳𝖞𝖇𝖗𝖎𝖉 𝕾𝖞𝖘𝖙𝖊𝖒</p>', unsafe_allow_html=True)

if selected_names:
    cols = st.columns(len(selected_names))
    for i, name in enumerate(selected_names):
        info = stock_dict[name]
        
        with cols[i]:
            # [조건부 로직] 엔비디아면 수페 API 호출, 아니면 yfinance 호출
            if info["type"] == "SOOPEH":
                soopeh_data = get_soopeh_nvda()
                if soopeh_data:
                    curr = soopeh_data.get('price', 0)
                    # 수페는 실시간 데이터이므로 그래프용 과거 데이터는 yfinance에서 빌려옴
                    hist_data = yf.Ticker("NVDA").history(period="1d", interval="1m")
                    perc = soopeh_data.get('changeRate', 0)
                    st.metric(label=f"{name} (Soopeh)", value=f"${curr:,.2f}", delta=f"{perc:+.2f}%")
                    data = hist_data # 그래프용
                else:
                    st.error("수페 토큰 만료!")
                    data = pd.DataFrame()
            else:
                ticker_obj = yf.Ticker(info["y"])
                data = ticker_obj.history(period="1d", interval="1m")
                if not data.empty:
                    curr = data['Close'].iloc[-1]
                    prev = data['Open'].iloc[0]
                    perc = (curr - prev) / prev * 100
                    st.metric(label=name, value=f"{curr:,.2f}", delta=f"{perc:+.2f}%")

            # 그래프 그리기
            if not data.empty:
                diff = data['Close'].iloc[-1] - data['Close'].iloc[0]
                m_color = "#FF4B4B" if diff >= 0 else "#0072ff"
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['Close'], fill='tozeroy', mode='lines',
                    line=dict(width=4, color=m_color),
                    fillcolor=f'rgba({255 if diff >= 0 else 0}, 75, 255, 0.1)'
                ))
                fig.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0), height=250, template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333', side="right")
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

st.divider()
memo = st.text_area("🗒️ 퀵 메모 (유찬후 전용)", placeholder="오늘의 투자 전략을 적어보세요..", height=100)
