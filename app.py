import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh

# --- 1. 페이지 설정 및 디자인 (CSS) ---
st.set_page_config(page_title="국내-해외 주식 현황 모니터링", page_icon="📈", layout="wide")

st.markdown("""
   <style>
    /* 폰트 설정 (Pretendard) */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    
    /* 메인 타이틀 스타일 */
    .main-title { 
        font-size: 40px !important; 
        font-weight: 800; 
        color: #FFFFFF; 
        text-align: center; 
        margin-bottom: 5px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    .sub-title { font-size: 18px; color: #888888; text-align: center; font-style: italic; margin-bottom: 30px; }

    /* ★ 버튼 애니메이션 & 그라데이션 그림자 (Red-Purple 테마) ★ */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        border: none;
        padding: 12px 20px;
        /* 빨강 -> 보라 그라데이션 */
        background: linear-gradient(135deg, #FF4B4B 0%, #764BA2 100%); 
        color: white !important;
        font-weight: 700;
        font-size: 16px;
        /* 은은한 보라색 그림자 */
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.4); 
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
    }

    /* 마우스 올렸을 때 (Hover) */
    div.stButton > button:hover {
        transform: translateY(-3px) scale(1.02); /* 살짝 떠오름 */
        /* 그림자 더 진해짐 (네온 광채) */
        box-shadow: 0 8px 25px rgba(118, 75, 162, 0.6); 
        /* 더 밝은 빨강-보라 그라데이션 */
        background: linear-gradient(135deg, #FF6B6B 0%, #8A54C9 100%); 
    }

    /* 클릭했을 때 (Active) - 쑥 들어가는 효과 */
    div.stButton > button:active {
        transform: translateY(1px) scale(0.95); /* 눌림 효과 */
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        transition: all 0.1s;
    }

    /* 종목 카드 스타일 개선 */
    [data-testid="stMetric"] {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 15px;
        box-shadow: inset 0 0 10px rgba(255,255,255,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 30초 자동 새로고침 설정
st_autorefresh(interval=30000, key="auto_refresh_key")

# --- 2. 강화된 데이터 크롤링 함수 ---
def get_korean_stock_price(ticker):
    try:
        # 네이버 금융 크롤링 (User-Agent 헤더 추가로 차단 방지)
        url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            # 가격 추출 경로 보강
            price_tag = soup.select_one(".no_today .blind")
            if price_tag:
                curr = int(price_tag.text.replace(',', ''))
                exday = soup.select_one(".no_exday .blind")
                # 전일비 계산
                diff_tag = soup.select_one(".no_exday .ico")
                diff_val = int(exday.find_all("span")[0].text.replace(',', '')) if exday else 0
                
                # 상승/하락 여부에 따른 전일가 계산
                if diff_tag and 'up' in diff_tag.get('class', []):
                    prev = curr - diff_val
                elif diff_tag and 'down' in diff_tag.get('class', []):
                    prev = curr + diff_val
                else:
                    prev = curr
                return curr, prev
        
        # 네이버 실패 시 yfinance로 2차 시도 (안전장치)
        yticker = yf.Ticker(f"{ticker}.KS")
        hist = yticker.history(period="2d")
        if not hist.empty:
            return int(hist['Close'].iloc[-1]), int(hist['Close'].iloc[-2])
            
    except Exception as e:
        print(f"Error: {e}")
    return None, None

# --- 3. 사이드바 (설정 메뉴) ---
with st.sidebar:
    st.header("모니터링 설정")
    stock_dict = {
        "삼성전자 (Samsung)": {"id": "005930", "type": "KR", "y": "005930.KS"},
        "현대자동차 (Hyundai)": {"id": "005380", "type": "KR", "y": "005380.KS"},
        "알파벳(구글) (GOOG)": {"id": "GOOG", "type": "US", "y": "GOOG"},
        "맥도날드 (MCD)": {"id": "MCD", "type": "US", "y": "MCD"}
    }
    selected_names = st.multiselect("종목 선택", list(stock_dict.keys()))
    period_map = {"1주일": "7d", "1개월": "1mo", "3개월": "3mo", "1년": "1y"}
    selected_period = st.selectbox("모니터링 기간", list(period_map.keys()), index=0)
    
    st.divider()
    if st.button("새로고침 (수동)", use_container_width=True):
        st.rerun()

# --- 4. 메인 화면 --- (이 아래부터 끝까지 덮어쓰세요)
st.markdown('<p class="main-title">주식 추세 일람 그래프</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">𝕽𝖊𝖆𝖑-𝖙𝖎𝖒𝖊 𝕱𝖎𝖓𝖆𝖓𝖈𝖎𝖆𝖑 𝕸𝖔𝖓𝖎𝖙𝖔𝖗𝖎𝖓𝖌 𝕾𝖞𝖘𝖙𝖊𝖒</p>', unsafe_allow_html=True)

# 검색창 섹션
search_q = st.text_input("", placeholder="알아보고 싶은 종목명을 입력해주세요.")
if search_q:
    refined_q = f"{search_q} 주가"
    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        st.link_button("🌐 Google", f"https://www.google.com/search?q={refined_q}", use_container_width=True)
    with s_col2:
        st.link_button("네이버", f"https://search.naver.com/search.naver?query={refined_q}", use_container_width=True)
    with s_col3:
        st.link_button("다음", f"https://search.daum.net/search?q={refined_q}", use_container_width=True)

st.divider()

# 종목 카드 및 그래프 레이아웃
# --- 드라마틱 풀 스팬 Plotly 차트 (수정본) ---
chart_data = yf.Ticker(info["y"]).history(period="1d", interval="1m") # 1분 단위로 촘촘하게

if not chart_data.empty:
    import plotly.graph_objects as go
    from datetime import datetime, time
    
    main_color = "#FF4B4B" if diff >= 0 else "#0072ff"
    fig = go.Figure()

    # 1. 부드러운 영역 차트
    fig.add_trace(go.Scatter(
        x=chart_data.index, y=chart_data['Close'],
        fill='tozeroy', mode='lines',
        line=dict(width=4, color=main_color), # 선을 좀 더 굵게!
        fillcolor=f'rgba({255 if diff >= 0 else 0}, {75 if diff >= 0 else 114}, {75 if diff >= 0 else 255}, 0.1)'
    ))

    # 2. X축 범위를 장 시간(09:00 ~ 15:30)으로 강제 고정 (국내주식 기준)
    # 미국 주식이라면 시간을 22:30 ~ 05:00 등으로 조절하면 됩니다.
    if info["type"] == "KR":
        start_time = chart_data.index[0].replace(hour=9, minute=0, second=0)
        end_time = chart_data.index[0].replace(hour=15, minute=30, second=0)
    else:
        start_time = chart_data.index[0] # 미국은 데이터 시작점 기준
        end_time = chart_data.index[-1]

    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=300, # 높이를 조금 더 키워서 시원하게!
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            range=[start_time, end_time], # 여기가 핵심! 폭을 넓게 고정
            showgrid=False,
            type='date'
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='#333',
            side="right" # 가격 수치를 오른쪽으로 보내서 이미지와 맞춤
        ),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

st.divider()
m_col1, m_col2 = st.columns([4, 1])
with m_col1:
    st.text_area("메모장", placeholder="텍스트 입력..", height=120)
with m_col2:
    st.write("") 
    st.write("") 
    if st.button("새로고침🔄", use_container_width=True):
        st.rerun()
