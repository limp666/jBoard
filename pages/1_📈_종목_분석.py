import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from services import yfinance_client

st.set_page_config(page_title="종목 분석", page_icon="📈", layout="wide")

def calculate_technicals(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate SMA, RSI, Volume MA, Slopes, Candle patterns, and Highs."""
    df = df.copy()
    # SMA
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["SMA_60"] = df["Close"].rolling(window=60).mean()
    
    # Slopes (Change in SMA over 1 day)
    df["Slope_20"] = df["SMA_20"].diff()
    df["Slope_60"] = df["SMA_60"].diff()
    
    # Volume MA
    df["Vol_MA_20"] = df["Volume"].rolling(window=20).mean()
    
    # RSI
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    
    # Candle Patterns
    # Upper Shadow: High - max(Open, Close)
    # Body: abs(Open - Close)
    df["Upper_Shadow"] = df["High"] - df[["Open", "Close"]].max(axis=1)
    df["Body"] = (df["Open"] - df["Close"]).abs()
    
    # Breakout (20-day High)
    df["High_20"] = df["High"].rolling(window=20).max()
    
    return df

def analyze_buy_timing(df: pd.DataFrame, current_price: float) -> dict:
    """
    Advanced Analysis with Mandatory vs Bonus Conditions.
    """
    if len(df) < 60:
        return {"status": "데이터 부족", "color": "gray", "message": "분석을 위한 데이터가 충분하지 않습니다."}
    
    # Get last 3 rows
    recent = df.iloc[-3:]
    last = recent.iloc[-1]
    
    sma_20 = last["SMA_20"]
    sma_60 = last["SMA_60"]
    slope_20 = last["Slope_20"]
    slope_60 = last["Slope_60"]
    rsi = last["RSI"]
    vol = last["Volume"]
    vol_ma_20 = last["Vol_MA_20"]
    high_20 = last["High_20"]
    
    # --- 1. Conditions ---
    
    # Mandatory (Essential)
    cond_trend = sma_20 > sma_60
    cond_price = current_price >= sma_20
    cond_rsi = rsi <= 65
    
    # Bonus (Preferred)
    cond_vol = vol >= (vol_ma_20 * 1.5) # Increased to 1.5x
    cond_breakout = current_price >= high_20 # Near 20-day high
    
    # --- 2. Sell Logic (Tiered) ---
    sell_reasons = []
    sell_level = 0 # 0: None, 1: Warning, 2: Exit
    
    # Tier 1: Warning
    if rsi >= 70:
        sell_reasons.append("RSI 과열(≥70)")
        sell_level = max(sell_level, 1)
    
    # Vol Spike + Long Upper Shadow (Shooting Star-ish)
    # Condition: Upper Shadow > 2 * Body AND Volume Spike
    if cond_vol and (last["Upper_Shadow"] > 2 * last["Body"]) and (last["Body"] > 0):
        sell_reasons.append("거래량 급증 + 윗꼬리")
        sell_level = max(sell_level, 1)
        
    if current_price < sma_20:
        sell_reasons.append("종가 MA20 이탈")
        sell_level = max(sell_level, 1)

    # Tier 2: Exit
    # Death Cross with Downward Slopes
    if (sma_20 <= sma_60) and (slope_20 < 0) and (slope_60 < 0):
        sell_reasons.append("역배열 확정")
        sell_level = 2
        
    # 3 days below MA20 (Failure to Reclaim)
    days_below_ma20 = (recent["Close"] < recent["SMA_20"]).sum()
    if days_below_ma20 == 3:
        sell_reasons.append("3일 연속 MA20 하회")
        sell_level = 2
        
    # RSI Breakdown (High -> Low) - Simplified: RSI < 50 while Price < MA20
    if rsi < 50 and current_price < sma_20:
        sell_reasons.append("RSI 50 이탈")
        sell_level = 2

    # --- 3. Position Sizing ---
    # Base: Trend Strength * K
    trend_strength = 0.0
    if sma_60 > 0:
        trend_strength = (sma_20 - sma_60) / sma_60
        
    # Formula: min(100, max(0, Trend * K))
    # K = 2000 (Trend 0.05 -> 100%)
    K = 2000
    base_weight = min(100, max(0, trend_strength * K))
    
    # Bonus Boost
    if cond_vol: base_weight += 10
    if cond_breakout: base_weight += 10
    
    # Penalties
    if rsi >= 60: base_weight -= 30 # Reduce exposure if getting hot
    if rsi >= 70: base_weight = 0 # No new entry allowed
        
    rec_weight = min(100, max(0, base_weight))
    
    # --- 4. Risk Level ---
    risk_score = 0
    if rsi > 60: risk_score += 1
    if rsi > 70: risk_score += 2
    if not cond_price: risk_score += 1
    if trend_strength < 0: risk_score += 2
    
    risk_label = "보통"
    risk_color = "green"
    if risk_score >= 2:
        risk_label = "높음"
        risk_color = "orange"
    if risk_score >= 4:
        risk_label = "매우 높음"
        risk_color = "red"

    # --- 5. Result ---
    result = {
        "sma_20": sma_20,
        "sma_60": sma_60,
        "rsi": rsi,
        "vol_ratio": vol / vol_ma_20 if vol_ma_20 > 0 else 0,
        "trend_strength": trend_strength,
        "rec_weight": rec_weight,
        "risk_label": risk_label,
        "risk_color": risk_color,
        "mandatory": {
            "추세 정배열 (MA20 > MA60)": cond_trend,
            "가격 모멘텀 (종가 ≥ MA20)": cond_price,
            "RSI 건전 (RSI ≤ 65)": cond_rsi,
        },
        "bonus": {
            "수급 폭발 (Vol ≥ 1.5배)": cond_vol,
            "전고점 돌파 (20일 신고가)": cond_breakout
        }
    }
    
    # Status Determination
    if sell_level == 2:
        result["status"] = "최종 청산 (Exit)"
        result["color"] = "red"
        result["message"] = f"⛔ **전량 매도 권장**: {', '.join(sell_reasons)}"
    elif sell_level == 1:
        result["status"] = "경고 / 비중 축소 (Warning)"
        result["color"] = "orange"
        result["message"] = f"⚠️ **부분 매도(30~50%) 권장**: {', '.join(sell_reasons)}"
    elif all(result["mandatory"].values()):
        result["status"] = "매수 (Buy)"
        result["color"] = "green"
        msg = "✅ **필수 조건 모두 충족**: 강력한 매수 신호입니다."
        if any(result["bonus"].values()):
            msg += f"\n🔥 **우대 조건 충족**: 추가 상승 모멘텀이 확인됩니다."
        result["message"] = msg
    else:
        result["status"] = "관망 (Wait)"
        result["color"] = "gray"
        failed = [k for k, v in result["mandatory"].items() if not v]
        result["message"] = f"필수 조건 미충족: {', '.join(failed)}"
        
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
            st.markdown(f"### 🧠 AI 정밀 분석")
            with st.container(border=True):
                # Top Row: Status & Risk
                c1, c2 = st.columns([2, 1])
                c1.markdown(f"**판단**: :{analysis['color']}[**{analysis['status']}**]")
                c2.markdown(f"**리스크**: :{analysis['risk_color']}[{analysis['risk_label']}]")
                
                st.info(analysis['message'], icon="💡")
                
                # Middle Row: Metrics
                st.markdown("#### 📊 핵심 지표")
                m1, m2, m3 = st.columns(3)
                m1.metric("추세 강도", f"{analysis['trend_strength']*100:.2f}%")
                m2.metric("권장 비중", f"{analysis['rec_weight']:.0f}%")
                m3.metric("RSI (14)", f"{analysis['rsi']:.1f}")
                
                # Bottom Row: Checklist
                st.markdown("#### ✅ 조건 체크리스트")
                
                # Mandatory
                st.caption("필수 조건 (Mandatory)")
                check_cols_m = st.columns(3)
                idx = 0
                for cond, met in analysis["mandatory"].items():
                    icon = "✅" if met else "❌"
                    text = cond if met else f":grey[{cond}]"
                    check_cols_m[idx % 3].markdown(f"{icon} {text}")
                    idx += 1
                    
                # Bonus
                st.caption("우대 조건 (Bonus)")
                check_cols_b = st.columns(2)
                idx = 0
                for cond, met in analysis["bonus"].items():
                    icon = "🔥" if met else "⚪"
                    text = cond if met else f":grey[{cond}]"
                    check_cols_b[idx % 2].markdown(f"{icon} {text}")
                    idx += 1
                
                st.divider()
                st.caption("※ 권장 비중은 추세 강도와 RSI 과열도를 반영한 알고리즘 산출값입니다.")

            # Chart
            render_chart(df, ticker)
            
            st.caption("본 분석은 사용자가 설정한 알고리즘에 기반한 참고용 자료이며, 투자 권유가 아닙니다.")

if __name__ == "__main__":
    main()
