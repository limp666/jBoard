import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from services import yfinance_client

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

def calculate_technicals(df):
    """Calculate SMA, RSI for backtesting."""
    df = df.copy()
    # SMA
    for ma in [20, 60, 120, 200]:
        df[f"SMA_{ma}"] = df["Close"].rolling(window=ma).mean()
        
    # RSI
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def calculate_smart_dca(df, monthly_amount, weights, rsi_threshold):
    """
    Calculate Smart DCA returns.
    Buys only when RSI condition AND MA conditions are met.
    """
    df = df.copy()
    # Pre-calculate indicators
    df = calculate_technicals(df)
    
    df["Portfolio_Value"] = 0.0
    df["Invested_Capital"] = 0.0
    
    total_shares = 0.0
    total_invested = 0.0
    next_buy_month = df.index[0].month
    
    portfolio_values = []
    invested_capitals = []
    
    for date, row in df.iterrows():
        # Buy condition: First trading day of the month
        if date.month == next_buy_month:
            # Determine Buy Amount based on conditions
            current_price = row["Close"]
            allocation_ratio = 0.0
            
            # Base Condition: RSI must be low
            if row["RSI"] < rsi_threshold:
                # If RSI is satisfied, check MA levels
                if current_price < row["SMA_20"]: allocation_ratio += weights['ma20']
                if current_price < row["SMA_60"]: allocation_ratio += weights['ma60']
                if current_price < row["SMA_120"]: allocation_ratio += weights['ma120']
                if current_price < row["SMA_200"]: allocation_ratio += weights['ma200']
            
            # Execute Buy
            buy_amount = monthly_amount * (allocation_ratio / 100.0)
            
            if buy_amount > 0:
                purchased = buy_amount / current_price
                total_shares += purchased
                total_invested += buy_amount
            
            next_buy_month = (next_buy_month % 12) + 1
            
        current_value = total_shares * row["Close"]
        portfolio_values.append(current_value)
        invested_capitals.append(total_invested)
        
    df["Portfolio_Value"] = portfolio_values
    df["Invested_Capital"] = invested_capitals
    
    return df, total_shares

def get_exchange_rate():
    """Fetch current USD/KRW exchange rate."""
    try:
        ticker = yf.Ticker("KRW=X")
        # Get fast info or history
        price = ticker.history(period="1d")["Close"].iloc[-1]
        return price
    except:
        return 1400.0 # Fallback

def main():
    st.title("💰 수익률 시뮬레이션 (백테스트)")
    st.markdown("과거 시점에 투자했다면 현재 얼마가 되었을지 시뮬레이션해 보세요.")
    
    with st.sidebar:
        st.header("설정")
        
        # Ticker Search UI
        search_query = st.text_input("종목 검색 (티커/회사명)", placeholder="예: Apple, Tesla, NVDA")
        
        # Default logic
        ticker = None
        
        if search_query:
            results = yfinance_client.search_symbols(search_query)
            if results:
                options = [r['display'] for r in results]
                selected_option = st.selectbox("검색 결과 선택", options)
                for r in results:
                    if r['display'] == selected_option:
                        ticker = r['symbol']
                        break
            else:
                st.warning("경고: 검색 결과가 없습니다. 정확한 티커를 입력해보세요.")
                ticker = search_query.upper()
        else:
            st.info("👆 위 검색창에 종목을 입력하세요.")
        
        strategy = st.radio(
            "투자 방식",
            ["거치식 (한 번에 투자)", "정액 적립식 (매월 일정액)", "스마트 적립식 (조건부 매수)"],
            index=1
        )
        
        # Smart DCA Settings
        weights = {}
        rsi_threshold = 40
        if strategy.startswith("스마트"):
            with st.expander("🛠 스마트 적립 옵션 설정", expanded=True):
                st.info("💡 **전제 조건**: RSI가 기준값보다 낮아야 매수가 실행됩니다.")
                rsi_threshold = st.slider("RSI 기준값 (이 값보다 낮아야 매수 시작)", 10, 80, 40)
                
                st.markdown("---")
                st.caption(f"**RSI < {rsi_threshold}** 만족 시 추가 매수 비중 설정:")
                
                w_ma20 = st.number_input("RSI 조건 & (가격 < MA 20) 시 (%)", 0, 100, 20)
                w_ma60 = st.number_input("RSI 조건 & (가격 < MA 60) 시 (%)", 0, 100, 20)
                w_ma120 = st.number_input("RSI 조건 & (가격 < MA 120) 시 (%)", 0, 100, 30)
                w_ma200 = st.number_input("RSI 조건 & (가격 < MA 200) 시 (%)", 0, 100, 50)
                
                weights = {
                    'ma20': w_ma20, 'ma60': w_ma60, 'ma120': w_ma120, 
                    'ma200': w_ma200
                }
                
                total_max = sum(weights.values())
                st.success(f"최대 매수 비중: 월 {total_max}% (조건 모두 만족 시)")
        
        # Date Input (Default: 3 years ago)
        default_start = datetime.now() - timedelta(days=365*3)
        start_date = st.date_input("시작 날짜", value=default_start)
        
        amount_label = "투자 금액 ($)" if strategy.startswith("거치식") else "월 기준 적립금 ($)"
        amount = st.number_input(amount_label, min_value=100, value=10000, step=100)
        
        run_btn = st.button("시뮬레이션 실행", type="primary")

    # --- Main Logic ---
    if run_btn and ticker:
        with st.spinner("데이터 분석 및 환율 조회 중..."):
            df = fetch_data(ticker, start_date)
            exchange_rate = get_exchange_rate()
            
            if df is None or df.empty:
                st.error("데이터가 없습니다. 날짜나 티커를 확인해주세요.")
                return
                
            # Calculate based on strategy
            if strategy.startswith("거치식"):
                result_df, final_shares = calculate_lump_sum(df, amount)
            elif strategy.startswith("정액"):
                result_df, final_shares = calculate_dca(df, amount)
            else: # Smart DCA
                result_df, final_shares = calculate_smart_dca(df, amount, weights, rsi_threshold)

                
            # Final Metrics (USD)
            final_value = result_df["Portfolio_Value"].iloc[-1]
            total_invested = result_df["Invested_Capital"].iloc[-1]
            profit = final_value - total_invested
            roi = (profit / total_invested) * 100 if total_invested > 0 else 0
            
            # Final Metrics (KRW)
            final_value_krw = final_value * exchange_rate
            total_invested_krw = total_invested * exchange_rate
            profit_krw = profit * exchange_rate
            
            # --- Display Results ---
            
            # 1. Summary Metrics
            st.subheader("📊 시뮬레이션 결과")
            st.caption(f"적용 환율: 1 USD = {exchange_rate:,.2f} KRW (실시간)")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("총 투자 원금", f"${total_invested:,.0f}", f"{total_invested_krw/10000:,.0f}만원")
            c2.metric("최종 평가금액", f"${final_value:,.0f}", f"{final_value_krw/10000:,.0f}만원")
            c3.metric("수익금", f"${profit:,.0f}", f"{profit_krw/10000:,.0f}만원", delta_color="normal" if profit > 0 else "inverse")
            c4.metric("수익률 (ROI)", f"{roi:,.2f}%", delta=f"{roi:,.2f}%")
            
            # 2. Chart
            st.subheader("📈 자산 성장 & 주가 흐름")
            
            # Create Subplots: Row 1 = Portfolio, Row 2 = Price & MAs
            fig = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True,
                vertical_spacing=0.1,
                subplot_titles=("💰 자산 가치 변화", f"📉 {ticker} 주가 및 이평선"),
                row_heights=[0.5, 0.5]
            )
            
            # --- Row 1: Portfolio ---
            # Portfolio Value Line
            fig.add_trace(go.Scatter(
                x=result_df.index, 
                y=result_df["Portfolio_Value"],
                mode='lines',
                name='평가 금액 ($)',
                line=dict(color='#00CC96', width=2),
                fill='tozeroy', 
                fillcolor='rgba(0, 204, 150, 0.1)'
            ), row=1, col=1)
            
            # Invested Capital Line
            fig.add_trace(go.Scatter(
                x=result_df.index, 
                y=result_df["Invested_Capital"],
                mode='lines',
                name='투자 원금 ($)',
                line=dict(color='#EF553B', width=2, dash='dash')
            ), row=1, col=1)
            
            # --- Row 2: Price & MAs ---
            # Ensure MAs are calculated (Smart DCA does it, others might not)
            if "SMA_20" not in result_df.columns:
                result_df = calculate_technicals(result_df)
                
            # Stock Price
            fig.add_trace(go.Scatter(
                x=result_df.index,
                y=result_df["Close"],
                mode='lines',
                name='주가 ($)',
                line=dict(color='white', width=1)
            ), row=2, col=1)
            
            # MAs
            ma_colors = {20: '#FFFF00', 60: '#FFA500', 120: '#FF00FF', 200: '#FF0000'}
            for ma, color in ma_colors.items():
                if f"SMA_{ma}" in result_df.columns:
                    fig.add_trace(go.Scatter(
                        x=result_df.index,
                        y=result_df[f"SMA_{ma}"],
                        mode='lines',
                        name=f'MA {ma}',
                        line=dict(color=color, width=1),
                        opacity=0.7
                    ), row=2, col=1)
            
            # RSI Markers (Optional Visual Aid - Buy Points)
            # If Smart DCA, we can mark buy points? (Maybe too crowded, skip for now)
            
            fig.update_layout(
                template="plotly_dark",
                hovermode="x unified",
                height=800,
                legend=dict(orientation="h", y=1.01, x=0.5, xanchor="center")
            )
            
            # Update axes
            fig.update_yaxes(title_text="금액 ($)", row=1, col=1)
            fig.update_yaxes(title_text="주가 ($)", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 3. Data Table (Optional)
            
            # 3. Data Table
            with st.expander("상세 데이터 보기", expanded=False):
                # Calculate Daily ROI
                # Handle division by zero for the very first row or before investment
                result_df["ROI"] = result_df.apply(
                    lambda x: ((x["Portfolio_Value"] - x["Invested_Capital"]) / x["Invested_Capital"] * 100) 
                    if x["Invested_Capital"] > 0 else 0.0, axis=1
                )
                
                # Filter columns to display
                display_cols = ["Close", "Invested_Capital", "Portfolio_Value", "ROI"]
                
                # Rename for display
                display_df = result_df[display_cols].rename(columns={
                    "Close": "주가 ($)", 
                    "Invested_Capital": "총 매수 원금 ($)", 
                    "Portfolio_Value": "총 평가 금액 ($)",
                    "ROI": "수익률 (%)"
                }).sort_index(ascending=False)
                
                st.dataframe(
                    display_df.style.format({
                        "주가 ($)": "${:,.2f}",
                        "총 매수 원금 ($)": "${:,.2f}",
                        "총 평가 금액 ($)": "${:,.2f}",
                        "수익률 (%)": "{:+.2f}%"
                    })
                )

if __name__ == "__main__":
    main()
