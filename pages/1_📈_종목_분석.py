import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from services import yfinance_client

st.set_page_config(page_title="종목 분석", page_icon="📈", layout="wide")

def calculate_technicals(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate SMA 20, SMA 60, RSI 14, and Volume MA 20."""
    df = df.copy()
    # SMA
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["SMA_60"] = df["Close"].rolling(window=60).mean()
    
    # Volume MA
    df["Vol_MA_20"] = df["Volume"].rolling(window=20).mean()
    
    # RSI
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    
    return df

def analyze_buy_timing(df: pd.DataFrame, current_price: float) -> dict:
    """
    Analyze buy timing based on User's Custom Strategy.
    
    Buy Conditions:
    1. MA20 > MA60 (Up Trend)
    2. Price > MA20 (Momentum)
    3. RSI < 65 (Not Overbought)
    4. Volume > 1.2 * Vol_MA20 (Volume Spike)
    
    Position Size:
    - (MA20 - MA60) / MA60 * 100 (%)
    
    Sell Conditions:
    - MA20 < MA60 OR RSI > 70 OR Price < MA20
    """
    if len(df) < 60:
        return {"status": "데이터 부족", "color": "gray", "message": "분석을 위한 데이터가 충분하지 않습니다."}
    
    last_row = df.iloc[-1]
    sma_20 = last_row["SMA_20"]
    sma_60 = last_row["SMA_60"]
    rsi = last_row["RSI"]
    vol = last_row["Volume"]
    vol_ma_20 = last_row["Vol_MA_20"]
    
    # Conditions
    cond_trend_up = sma_20 > sma_60
    cond_price_above_ma20 = current_price > sma_20
    cond_rsi_safe = rsi < 65
    cond_vol_spike = vol > (vol_ma_20 * 1.2)
    
    cond_rsi_overbought = rsi > 70
    cond_trend_down = sma_20 < sma_60
    cond_price_below_ma20 = current_price < sma_20
    
    # Position Sizing Calculation
    # (MA20 - MA60) / MA60 * 100
    position_pct = 0.0
    if sma_60 > 0:
        position_pct = ((sma_20 - sma_60) / sma_60) * 100
    
    # Logic
    result = {
        "sma_20": sma_20,
        "sma_60": sma_60,
        "rsi": rsi,
        "vol_ratio": vol / vol_ma_20 if vol_ma_20 > 0 else 0,
        "position_pct": max(0, position_pct), # Ensure non-negative
        "checks": {
            "MA20 > MA60 (추세)": cond_trend_up,
            "주가 > MA20 (모멘텀)": cond_price_above_ma20,
            "RSI < 65 (건전)": cond_rsi_safe,
            "거래량 > 1.2배 (수급)": cond_vol_spike
        }
    }
    
    # Sell Signal Check First
    if cond_trend_down or cond_rsi_overbought or cond_price_below_ma20:
        reasons = []
        if cond_trend_down: reasons.append("역배열 (MA20 < MA60)")
        if cond_rsi_overbought: reasons.append("과열 (RSI > 70)")
        if cond_price_below_ma20: reasons.append("추세 이탈 (주가 < MA20)")
        
        result["status"] = "매도 / 관망 (Sell)"
        result["color"] = "red"
        result["message"] = f"매도 조건이 발생했습니다: {', '.join(reasons)}. 신규 진입을 자제하고 리스크를 관리하세요."
        return result

    # Buy Signal Check
    if cond_trend_up and cond_price_above_ma20 and cond_rsi_safe and cond_vol_spike:
        result["status"] = "매수 (Buy)"
        result["color"] = "green"
        result["message"] = (
            f"모든 매수 조건이 충족되었습니다! 강력한 상승 모멘텀이 확인됩니다.\n"
            f"**추천 비중: {result['position_pct']:.1f}%** (추세 강도 기반)"
        )
        return result
        
    # Mixed / Hold
    result["status"] = "보유 / 대기 (Hold)"
    result["color"] = "orange"
    
    failed_conds = [k for k, v in result["checks"].items() if not v]
    result["message"] = (
        f"상승 추세이나 일부 조건이 미충족되었습니다.\n"
        f"미충족 조건: {', '.join(failed_conds)}\n"
        "조건이 완성될 때까지 기다리거나 소량만 접근하세요."
    )
    return result

def render_chart(df: pd.DataFrame, ticker: str):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, row_heights=[0.7, 0.3])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name='OHLC'
    ), row=1, col=1)
    
    # SMAs
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='green', width=1.5), name='SMA 20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_60'], line=dict(color='orange', width=1.5), name='SMA 60'), row=1, col=1)
    
    # Volume
    colors = ['red' if row['Open'] - row['Close'] >= 0 else 'green' for index, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)
    
    # Volume MA
    fig.add_trace(go.Scatter(x=df.index, y=df['Vol_MA_20'], line=dict(color='gray', width=1, dash='dot'), name='Vol MA 20'), row=2, col=1)
    
    fig.update_layout(
        title=f"{ticker} 주가 차트 (Daily)",
        xaxis_rangeslider_visible=False,
        height=600,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("📈 종목 분석 및 매수 타이밍")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input("티커 입력 (예: AAPL, TSLA, NVDA)", value="AAPL").upper()
    with col2:
        st.write("") # Spacer
        st.write("")
        if st.button("분석하기", type="primary"):
            pass # Just triggers rerun
            
    if ticker:
        with st.spinner(f"{ticker} 데이터 분석 중..."):
            # Fetch Data
            info = yfinance_client.get_stock_info(ticker)
            df = yfinance_client.get_stock_history(ticker, period="1y")
            
            if df.empty:
                st.error("데이터를 찾을 수 없습니다. 티커를 확인해주세요.")
                return
                
            # Process Data
            df = calculate_technicals(df)
            current_price = df["Close"].iloc[-1]
            
            # Header Info
            st.subheader(f"{info.get('shortName', ticker)} ({ticker})")
            metric_cols = st.columns(4)
            metric_cols[0].metric("현재가", f"${current_price:,.2f}")
            
            change = current_price - df["Close"].iloc[-2]
            change_pct = (change / df["Close"].iloc[-2]) * 100
            metric_cols[1].metric("전일 대비", f"{change:+.2f}", f"{change_pct:+.2f}%")
            
            metric_cols[2].metric("52주 최고", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")
            metric_cols[3].metric("52주 최저", f"${info.get('fiftyTwoWeekLow', 0):,.2f}")
            
            # Analysis
            analysis = analyze_buy_timing(df, current_price)
            
            st.divider()
            
            # Trading Plan Card
            st.markdown(f"### 🧠 AI 매수 타이밍 분석")
            with st.container(border=True):
                st.markdown(f"**판단**: :{analysis['color']}[**{analysis['status']}**]")
                st.info(analysis['message'], icon="💡")
                
                if analysis['status'] == "매수 (Buy)":
                     st.success(f"💰 **추천 비중**: 자산의 **{analysis['position_pct']:.1f}%** (추세 강도: {analysis['position_pct']:.1f})")
                
                st.markdown("#### 📋 조건 체크리스트")
                check_cols = st.columns(4)
                checks = analysis.get("checks", {})
                idx = 0
                for cond, met in checks.items():
                    icon = "✅" if met else "❌"
                    check_cols[idx % 4].markdown(f"{icon} {cond}")
                    idx += 1
                
                st.divider()
                st.markdown("#### 📊 주요 지표")
                kpi_cols = st.columns(4)
                kpi_cols[0].metric("SMA 20", f"${analysis['sma_20']:.2f}")
                kpi_cols[1].metric("SMA 60", f"${analysis['sma_60']:.2f}")
                kpi_cols[2].metric("RSI (14)", f"{analysis['rsi']:.1f}")
                kpi_cols[3].metric("거래량 비율", f"{analysis['vol_ratio']:.1f}배")

            # Chart
            render_chart(df, ticker)
            
            st.caption("본 분석은 사용자가 설정한 알고리즘에 기반한 참고용 자료이며, 투자 권유가 아닙니다.")

if __name__ == "__main__":
    main()
