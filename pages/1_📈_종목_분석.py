import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from services import yfinance_client
from services import yfinance_client

st.set_page_config(page_title="종목 분석", page_icon="📈", layout="wide")

def display_corporate_analysis(info: dict):
    """Display fundamental data and company info."""
    st.subheader("🏢 기업 분석 (Corporate Analysis)")
    
    # prevent errors if keys are missing
    currency = info.get('currency', 'USD')
    
    # 1. Company Summary
    with st.expander("기업 개요 및 섹터 정보", expanded=True):
        c1, c2 = st.columns([1, 3])
        with c1:
            st.metric("섹터 (Sector)", info.get('sector', 'N/A'))
        with c2:
            st.metric("산업 (Industry)", info.get('industry', 'N/A'))
        st.write(info.get('longBusinessSummary', '기업 설명 정보가 없습니다.'))

    # 2. Key Fundamentals
    st.markdown("#### 🔑 핵심 재무 지표 (Fundamentals)")
    
    f1, f2, f3, f4, f5 = st.columns(5)
    
    # Helper to safe format
    def safe_fmt(val, fmt="{:,.2f}", suffix=""):
        if val is None: return "N/A"
        return fmt.format(val) + suffix

    def human_format(num):
        if num is None: return "N/A"
        num = float('{:.3g}'.format(num))
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

    # Determine currency symbol
    currency_symbol = "$" if currency == "USD" else "₩" if currency == "KRW" else currency + " "

    f1.metric("시가총액 (Market Cap)", f"{currency_symbol}{human_format(info.get('marketCap'))}")
    f1.caption(f"통화: {currency}")
    
    f2.metric("PER (주가수익비율)", safe_fmt(info.get('trailingPE')), help="낮을수록 저평가 가능성")
    f2.caption(f"Forward PER: {safe_fmt(info.get('forwardPE'))}")
    
    f3.metric("PBR (주가순자산비율)", safe_fmt(info.get('priceToBook')), help="1 미만이면 자산가치 대비 저평가")
    
    roe = info.get('returnOnEquity')
    f4.metric("ROE (자기자본이익률)", safe_fmt(roe * 100 if roe else None, "{:.2f}", "%"), help="높을수록 자본 효율성 좋음")
    
    div_yield = info.get('dividendYield')
    f5.metric("배당수익률", safe_fmt(div_yield * 100 if div_yield else None, "{:.2f}", "%"))

    # Growth & Margins
    st.markdown("#### 📈 성장성 및 수익성")
    g1, g2, g3, g4 = st.columns(4)
    
    g1.metric("매출 성장률 (YoY)", safe_fmt((info.get('revenueGrowth') or 0) * 100, "{:+.2f}", "%"))
    g2.metric("이익 성장률 (YoY)", safe_fmt((info.get('earningsGrowth') or 0) * 100, "{:+.2f}", "%"))
    g3.metric("영업이익률", safe_fmt((info.get('operatingMargins') or 0) * 100, "{:.2f}", "%"))
    g4.metric("순이익률", safe_fmt((info.get('profitMargins') or 0) * 100, "{:.2f}", "%"))

    st.divider()

def calculate_indicators(df: pd.DataFrame, macd_fast=12, macd_slow=26, macd_sig=9):
    """Calculate MAs, RSI, MACD, Volume MA for the dataframe."""
    df = df.copy()
    
    # 1. Moving Averages
    for ma in [20, 60, 120, 200]:
        df[f'SMA_{ma}'] = df['Close'].rolling(window=ma).mean()
        
    # 2. RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 3. MACD
    ema_fast = df['Close'].ewm(span=macd_fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=macd_slow, adjust=False).mean()
    df['MACD'] = ema_fast - ema_slow
    df['MACD_Signal'] = df['MACD'].ewm(span=macd_sig, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # 4. Volume MA (20)
    df['Vol_MA_20'] = df['Volume'].rolling(window=20).mean()
    
    return df

def render_chart(df: pd.DataFrame, ticker: str):
    """Draw candlestick chart with selectable indicators."""
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])

    # 1. Candlestick & MA
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name='OHLC'
    ), row=1, col=1)
    
    # Add MAs
    colors = {20: 'green', 60: 'orange', 120: 'purple', 200: 'red'}
    for ma, color in colors.items():
        if f'SMA_{ma}' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[f'SMA_{ma}'], 
                                     line=dict(color=color, width=1), name=f'SMA {ma}'), row=1, col=1)

    # 2. Volume
    vol_colors = ['red' if row['Open'] - row['Close'] >= 0 else 'green' for index, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=vol_colors, name='Volume'), row=2, col=1)
    
    # 3. MACD
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='blue', width=1), name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='orange', width=1), name='Signal'), row=3, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color='gray', name='Histogram'), row=3, col=1)

    fig.update_layout(
        title=f"{ticker} 기술적 분석 차트",
        xaxis_rangeslider_visible=False,
        height=800,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    st.plotly_chart(fig, width='stretch')

def main():
    st.title("📈 종목 분석 (Advanced)")
    
    # --- Sidebar Input ---
    with st.sidebar:
        st.header("🔍 설정 (Settings)")
        
        # Ticker Search UI
        search_query = st.text_input("종목 검색 (티커/회사명)", placeholder="예: Apple, Tesla, NVDA")
        
        # Default to a safe value
        ticker = "BTC-USD" 
        
        if search_query:
            results = yfinance_client.search_symbols(search_query)
            if results:
                # Create a list of display strings
                options = [r['display'] for r in results]
                selected_option = st.selectbox("검색 결과 선택", options)
                
                # Find the symbol for the selected option
                for r in results:
                    if r['display'] == selected_option:
                        ticker = r['symbol']
                        break
            else:
                st.warning("경고: 검색 결과가 없습니다. 정확한 티커를 입력해보세요.")
                ticker = search_query.upper() # Fallback to manual input
        else:
             st.info("👆 위 검색창에 종목을 입력하세요.")
             ticker = None # Don't analyze yet if empty
             
        
        st.divider()
        st.markdown("### ⚙️ 매수/매도 조건 설정")
        
        # MA Conditions (Uptrend)
        st.markdown("**🟢 상승/지지 조건 (Uptrend)**")
        check_ma20_up = st.checkbox("가격 > MA 20", value=True)
        check_ma60_up = st.checkbox("가격 > MA 60", value=True)
        check_ma200_up = st.checkbox("가격 > MA 200 (장기 상승)", value=False)
        check_goldencross = st.checkbox("골든크로스 (MA20 > MA60)", value=True)
        
        # MA Conditions (Downtrend)
        st.markdown("**🔴 하락/저항 조건 (Downtrend)**")
        check_ma20_down = st.checkbox("가격 < MA 20", value=False)
        check_ma60_down = st.checkbox("가격 < MA 60", value=False)
        check_ma120_down = st.checkbox("가격 < MA 120", value=False)
        check_ma200_down = st.checkbox("가격 < MA 200 (장기 하락)", value=False)
        check_deadcross = st.checkbox("데드크로스 (MA20 < MA60)", value=False)
        check_reverse_arr = st.checkbox("역배열 (20 < 60 < 120 < 200)", value=False)
        
        # MACD Conditions
        st.markdown("**MACD**")
        check_macd_bull = st.checkbox("MACD > Signal (상승 추세)", value=True)
        check_macd_pos = st.checkbox("MACD > 0 (0선 돌파)", value=False)
        
        # RSI Conditions
        st.markdown("**RSI (상대강도지수)**")
        rsi_buy_thresh = st.slider("매수 기준 (RSI < X)", 0, 100, 40)
        rsi_sell_thresh = st.slider("매도(과열) 기준 (RSI > X)", 0, 100, 70)
        
        # Volume Conditions
        st.markdown("**거래량 (Volume)**")
        vol_mul = st.number_input("평균 대비 급증 배수", value=1.5, step=0.1)
        check_vol_spike = st.checkbox(f"거래량 > {vol_mul}배 (Vol MA 20)", value=False)

    if not ticker:
        st.info("좌측 사이드바에서 티커를 입력해주세요.")
        return

    # --- Fetch Data ---
    with st.spinner(f"{ticker} 데이터 분석 중..."):
        # 1. Info
        info = yfinance_client.get_stock_info(ticker)
        if not info:
            st.error("티커 정보를 가져올 수 없습니다.")
            return

        # 2. History (Enough for 200 MA)
        df = yfinance_client.get_stock_history(ticker, period="2y")
        if df.empty:
            st.error("주가 데이터를 가져올 수 없습니다.")
            return
            
        # Calculate Indicators
        df = calculate_indicators(df)
        
        # Current Data Point
        last = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = last['Close']
        
        # --- Corporate Analysis Section ---
        display_corporate_analysis(info)
        
        # --- Technical Analysis Section ---
        st.subheader("🛠 매수/매도 타이밍 분석 (Timing Analysis)")
        
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.markdown("#### ⚡ 현재 상태 체크리스트")
            st.caption("설정한 조건 만족 여부")
            
            satisfied_count = 0
            total_conditions = 0
            
            def check_cond(label, is_met, value_text=""):
                icon = "✅" if is_met else "❌"
                color = "green" if is_met else "red"
                st.markdown(f"{icon} **{label}** : :{color}[{'만족' if is_met else '미충족'}] {value_text}")
                return 1 if is_met else 0
            
            # 1. MA (Uptrend)
            if check_ma20_up:
                total_conditions += 1
                satisfied_count += check_cond("가격 > MA 20", current_price > last['SMA_20'], f"(${last['SMA_20']:.2f})")
            
            if check_ma60_up:
                total_conditions += 1
                satisfied_count += check_cond("가격 > MA 60", current_price > last['SMA_60'], f"(${last['SMA_60']:.2f})")
                
            if check_ma200_up:
                total_conditions += 1
                satisfied_count += check_cond("가격 > MA 200", current_price > last['SMA_200'], f"(${last['SMA_200']:.2f})")
                
            if check_goldencross:
                total_conditions += 1
                satisfied_count += check_cond("골든크로스 (20>60)", last['SMA_20'] > last['SMA_60'])

            # 1. MA (Downtrend)
            if check_ma20_down:
                total_conditions += 1
                satisfied_count += check_cond("가격 < MA 20", current_price < last['SMA_20'], f"(${last['SMA_20']:.2f})")
                
            if check_ma60_down:
                total_conditions += 1
                satisfied_count += check_cond("가격 < MA 60", current_price < last['SMA_60'], f"(${last['SMA_60']:.2f})")
                
            if check_ma120_down:
                total_conditions += 1
                satisfied_count += check_cond("가격 < MA 120", current_price < last['SMA_120'], f"(${last['SMA_120']:.2f})")

            if check_ma200_down:
                total_conditions += 1
                satisfied_count += check_cond("가격 < MA 200", current_price < last['SMA_200'], f"(${last['SMA_200']:.2f})")
                
            if check_deadcross:
                total_conditions += 1
                satisfied_count += check_cond("데드크로스 (20<60)", last['SMA_20'] < last['SMA_60'])
                
            if check_reverse_arr:
                total_conditions += 1
                is_reverse = (last['SMA_20'] < last['SMA_60']) and (last['SMA_60'] < last['SMA_120']) and (last['SMA_120'] < last['SMA_200'])
                satisfied_count += check_cond("역배열 (20<60<120<200)", is_reverse)
            
            # 2. MACD
            if check_macd_bull:
                total_conditions += 1
                satisfied_count += check_cond("MACD > Signal", last['MACD'] > last['MACD_Signal'])
            
            if check_macd_pos:
                total_conditions += 1
                satisfied_count += check_cond("MACD > 0", last['MACD'] > 0)
                
            # 3. RSI
            # RSI is special; usually Low is Buy signal, High is Sell signal.
            # We show both status.
            st.markdown("---")
            st.markdown(f"**RSI (14):** {last['RSI']:.2f}")
            if last['RSI'] <= rsi_buy_thresh:
                st.success(f"🔵 과매도 구간 (매수 기회?): {rsi_buy_thresh} 이하")
            elif last['RSI'] >= rsi_sell_thresh:
                st.warning(f"🔴 과열 구간 (매도 고려?): {rsi_sell_thresh} 이상")
            else:
                st.info("⚪ 중립 구간")
                
            # 4. Volume
            if check_vol_spike:
                total_conditions += 1
                is_spike = last['Volume'] >= (last['Vol_MA_20'] * vol_mul)
                satisfied_count += check_cond(f"거래량 폭발 (>{vol_mul}배)", is_spike)

            st.markdown("---")
            if total_conditions > 0:
                score = (satisfied_count / total_conditions) * 100
                st.metric("조건 만족도", f"{score:.0f}%", f"{satisfied_count}/{total_conditions}")
            else:
                st.caption("선택된 조건이 없습니다.")

        with c2:
            render_chart(df, ticker)

if __name__ == "__main__":
    main()
