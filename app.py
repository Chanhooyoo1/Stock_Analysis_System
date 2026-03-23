import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import threading
import matplotlib

# 한글 폰트 설정 (그래프 깨짐 방지)
matplotlib.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class StockApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("실시간 국내-해외 주가 일람 프로그람")
        self.geometry("850x1000")

        # 1. 종목 데이터 정의
        self.stock_list = [
            ["삼성전자", "005930", "KR", tk.BooleanVar(value=True)],
            ["현대자동차", "005380", "KR", tk.BooleanVar()],
            ["알파벳(구글)", "GOOG", "US", tk.BooleanVar(value=True)],
            ["맥도날드", "MCD", "US", tk.BooleanVar()],
        ]

        # 2. 기간 매핑 (화면 표시 : yfinance 파라미터)
        self.period_map = {"1일": "1d", "1주일": "7d", "1개월": "1mo", "3개월": "3mo", "1년": "1y"}
        
        # 자동 업데이트 간격 설정 (30초 = 30000ms) - 30초 이하 설정 방지
        self.update_interval = 30000 
        self.is_updating = False

        self.setup_ui()

    def setup_ui(self):

        # --- [추가] 0. 메인 제목 (Main Title) ---
        self.main_title = ctk.CTkLabel(
            self, 
            text="실시간 내ㆍ외국 주가분석 일람 시스템", 
            font=("맑은 고딕", 28, "bold"),
            text_color="#FFFFFF" # 네온 그린 컬러로 강조
        )
        self.main_title.pack(pady=(20, 10))

        self.sub_title = ctk.CTkLabel(
            self, 
            text="𝕽𝖊𝖆𝖑-𝖙𝖎𝖒𝖊 𝕯𝖔𝖒𝖊𝖘𝖙𝖎𝖈 𝕱𝖔𝖗𝖊𝖎𝖌𝖓 𝕾𝖙𝖔𝖈𝖐 𝕸𝖔𝖓𝖎𝖙𝖔𝖗𝖎𝖓𝖌 𝕾𝖞𝖘𝖙𝖊𝖒", 
            font=("Arial", 20, "italic"),
            text_color="gray"
            
        )
        self.sub_title.pack(pady=(0, 15))

        # --- 상단 컨트롤 영역 ---
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(self.control_frame, text="모니터링 설정", font=("맑은 고딕", 14, "bold")).pack(anchor="w", padx=10, pady=5)
        
        # 종목 체크박스
        self.cb_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.cb_frame.pack(fill="x", padx=10)
        for name, _, _, var in self.stock_list:
            ctk.CTkCheckBox(self.cb_frame, text=name, variable=var).pack(side="left", padx=10)
        # 기간 선택 (Lookup)
        self.lookup_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.lookup_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(self.lookup_frame, text="조회 기간:").pack(side="left", padx=(0, 10))
        self.period_dropdown = ctk.CTkOptionMenu(self.lookup_frame, values=list(self.period_map.keys()))
        self.period_dropdown.set("1주일")
        self.period_dropdown.pack(side="left")

        # --- 중간 메모 영역 ---
        self.memo_frame = ctk.CTkFrame(self)
        self.memo_frame.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(self.memo_frame, text="메모장", font=("맑은 고딕", 12)).pack(pady=(5, 0))
        self.memo_box = ctk.CTkTextbox(self.memo_frame, height=80, corner_radius=10)
        self.memo_box.pack(pady=10, padx=10, fill="x")

        # --- 실시간 가격 표시 라벨 ---
        self.price_label = ctk.CTkLabel(self, text="", font=("맑은 고딕", 15, "bold"), text_color="white")
        self.price_label.pack(pady=10)

        # --- 그래프 스크롤 영역 ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="주가 그래프")
        self.scroll_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # --- 하단 버튼 ---
        self.btn_update = ctk.CTkButton(self, text="수동 새로고침", command=self.manual_update, height=45)
        self.btn_update.pack(pady=15)

    def get_korean_stock_price(self, ticker):
        try:
            url = f"https://finance.naver.com/item/main.naver?code={ticker}"
            res = requests.get(url, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            price = int(soup.select_one(".no_today .blind").text.replace(',', ''))
            
            exday = soup.select_one(".no_exday .blind")
            yesterday = int(exday.find_all("span")[0].text.replace(',', '')) if exday else price
            return price, yesterday
        except: return None, None

    def manual_update(self):
        """사용자가 버튼을 눌렀을 때 실행"""
        self.start_update_process()

    def start_update_process(self):
        """실제 업데이트 로직 및 30초 예약"""
        if self.is_updating: return
        
        self.is_updating = True
        self.btn_update.configure(state="disabled", text="데이터를 갱신 중입니다...")
        
        # 백그라운드 스레드에서 데이터 호출
        threading.Thread(target=self.update_process, daemon=True).start()
        
        # 중요: 30초(30000ms) 미만으로 설정되지 않도록 고정된 예약 시스템
        # 만약 간격을 변수로 쓰더라도 max(30000, value) 처리를 통해 보호할 수 있습니다.
        self.after(max(30000, self.update_interval), self.start_update_process)

    def update_process(self):
        selected_period_text = self.period_dropdown.get()
        api_period = self.period_map[selected_period_text]
        
        # 기간별 정밀도(Interval) 설정
        interval = "1m" if api_period == "1d" else "30m" if api_period == "7d" else "1d"
        
        display_text = f"마지막 업데이트 시각: {datetime.now().strftime('%H:%M:%S')}\n"
        graph_data_list = []

        for name, ticker, stock_type, var in self.stock_list:
            if var.get():
                # 가격 정보 호출
                if stock_type == "KR":
                    current, yesterday = self.get_korean_stock_price(ticker)
                    y_ticker = ticker + ".KS"
                else:
                    s = yf.Ticker(ticker)
                    d2 = s.history(period="2d")
                    current = round(d2['Close'].iloc[-1], 2) if not d2.empty else None
                    yesterday = round(d2['Close'].iloc[-2], 2) if len(d2) > 1 else current
                    y_ticker = ticker
                
                if current:
                    diff = current - yesterday
                    perc = (diff / yesterday * 100) if yesterday else 0
                    sign = "▲" if diff > 0 else "▼" if diff < 0 else "-"
                    unit = "원" if stock_type == "KR" else "$"
                    display_text += f"{name}: {current:,.2f}{unit} ({sign} {perc:+.2f}%)\n"
                
                # 그래프 데이터 호출
                try:
                    hist = yf.Ticker(y_ticker).history(period=api_period, interval=interval)
                    if not hist.empty:
                        graph_data_list.append((name, hist))
                except: pass

        # 메인 스레드에서 UI 업데이트
        self.after(0, lambda: self.update_ui(display_text, graph_data_list, selected_period_text))

    def update_ui(self, text, graphs, period_text):
        self.price_label.configure(text=text)
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for name, data in graphs:
            fig, ax = plt.subplots(figsize=(6, 3.5))
            fig.patch.set_facecolor('#2b2b2b')
            
            # 촘촘한 정밀 그래프 스타일
            ax.plot(data.index, data['Close'], color="#FF0000", linewidth=1)
            ax.fill_between(data.index, data['Close'], min(data['Close']), color="#FF0000", alpha=0.1)
            
            ax.set_title(f"{name} ({period_text})", color='white', fontsize=11, fontweight='bold')
            ax.set_facecolor('#141414')
            ax.grid(True, alpha=0.1, linestyle='--')
            ax.tick_params(colors='white', labelsize=8)
            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=self.scroll_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(pady=10, padx=10)
            plt.close(fig)

        self.btn_update.configure(state="normal", text="새로고침🔄")
        self.is_updating = False

if __name__ == "__main__":
    app = StockApp()
    # 실행 시 즉시 업데이트 프로세스 시작
    app.start_update_process()
    app.mainloop()
