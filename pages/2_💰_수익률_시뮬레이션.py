import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="수익률 시뮬레이션", page_icon="💰", layout="wide")

def fetch_data(ticker, start_date):
    """Fetch historical data from start_date to today."""
    try:
        df = yf.download(ticker, start=start_date, progress=False)
        if df.empty:
            return None
        # Ensure we have a single level column index if multi-index (yfinance update)
        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs(ticker, axis=1, level=1, drop_level=True)
        return df
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None

def calculate_lump_sum(df, amount):
    """Calculate Lump-sum investment returns."""
    df = df.copy()
    start_price = df["Close"].iloc[0]
    shares = amount / start_price
    
    df["Portfolio_Value"] = df["Close"] * shares
    df["Invested_Capital"] = amount
    
    return df, shares

def calculate_dca(df, monthly_amount):
    """Calculate DCA (Dollar Cost Averaging) returns."""
    df = df.copy()
    df["Portfolio_Value"] = 0.0
    df["Invested_Capital"] = 0.0
    df["Shares_Owned"] = 0.0
    
    # Resample to monthly to find buying dates (start of month)
    # We'll iterate through the daily dataframe to be precise
    
    total_shares = 0.0
    total_invested = 0.0
    next_buy_month = df.index[0].month
    
    # Lists to construct new columns efficiently
    portfolio_values = []
    invested_capitals = []
    
    for date, row in df.iterrows():
        # Buy condition: First trading day of the month
        if date.month == next_buy_month:
            price = row["Close"]
            purchased = monthly_amount / price
            total_shares += purchased
            total_invested += monthly_amount
            
            # Update next buy month
            next_buy_month = (next_buy_month % 12) + 1
            
        # Calculate daily value
        current_value = total_shares * row["Close"]
        
        portfolio_values.append(current_value)
        invested_capitals.append(total_invested)
        
    df["Portfolio_Value"] = portfolio_values
    df["Invested_Capital"] = invested_capitals
    
    return df, total_shares

def main():
    st.title("💰 수익률 시뮬레이션 (백테스트)")
    st.markdown("과거 시점에 투자했다면 현재 얼마가 되었을지 시뮬레이션해 보세요.")
    
    # --- Sidebar Inputs ---
    with st.sidebar:
        st.header("설정")
        ticker = st.text_input("티커 (예: SPY, QQQ, AAPL)", value="SPY").upper()
        
        strategy = st.radio(
            "투자 방식",
            ["거치식 (한 번에 투자)", "적립식 (매월 투자)"],
            index=0
        )
        
        # Date Input (Default: 3 years ago)
        default_start = datetime.now() - timedelta(days=365*3)
        start_date = st.date_input("시작 날짜", value=default_start)
        
        amount_label = "투자 금액 ($)" if strategy.startswith("거치식") else "월 적립 금액 ($)"
        amount = st.number_input(amount_label, min_value=100, value=10000, step=100)
        
        run_btn = st.button("시뮬레이션 실행", type="primary")

    # --- Main Logic ---
    if run_btn and ticker:
        with st.spinner("데이터 분석 중..."):
            df = fetch_data(ticker, start_date)
            
            if df is None or df.empty:
                st.error("데이터가 없습니다. 날짜나 티커를 확인해주세요.")
                return
                
            # Calculate based on strategy
            if strategy.startswith("거치식"):
                result_df, final_shares = calculate_lump_sum(df, amount)
                mode = "Lump-sum"
            else:
                result_df, final_shares = calculate_dca(df, amount)
                mode = "DCA"
                
            # Final Metrics
            final_value = result_df["Portfolio_Value"].iloc[-1]
            total_invested = result_df["Invested_Capital"].iloc[-1]
            profit = final_value - total_invested
            roi = (profit / total_invested) * 100 if total_invested > 0 else 0
            
            # --- Display Results ---
            
            # 1. Summary Metrics
            st.subheader("📊 시뮬레이션 결과")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("총 투자 원금", f"${total_invested:,.0f}")
            c2.metric("최종 평가금액", f"${final_value:,.0f}")
            c3.metric("수익금", f"${profit:,.0f}", delta_color="normal" if profit > 0 else "inverse")
            c4.metric("수익률 (ROI)", f"{roi:,.2f}%", delta=f"{roi:,.2f}%")
            
            # 2. Chart
            st.subheader("📈 자산 성장 그래프")
            fig = go.Figure()
            
            # Portfolio Value Line
            fig.add_trace(go.Scatter(
                x=result_df.index, 
                y=result_df["Portfolio_Value"],
                mode='lines',
                name='평가 금액',
                line=dict(color='#00CC96', width=2),
                fill='tozeroy', # Fill area below
                fillcolor='rgba(0, 204, 150, 0.1)'
            ))
            
            # Invested Capital Line
            fig.add_trace(go.Scatter(
                x=result_df.index, 
                y=result_df["Invested_Capital"],
                mode='lines',
                name='투자 원금',
                line=dict(color='#EF553B', width=2, dash='dash')
            ))
            
            fig.update_layout(
                template="plotly_dark",
                hovermode="x unified",
                height=500,
                xaxis_title="날짜",
                yaxis_title="금액 ($)",
                legend=dict(orientation="h", y=1.02, yanchor="bottom", x=1, xanchor="right")
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 3. Data Table (Optional)
            with st.expander("상세 데이터 보기"):
                st.dataframe(
                    result_df[["Close", "Invested_Capital", "Portfolio_Value"]]
                    .rename(columns={"Close": "주가", "Invested_Capital": "원금", "Portfolio_Value": "평가금"})
                    .sort_index(ascending=False)
                    .style.format("${:,.2f}")
                )

if __name__ == "__main__":
    main()
