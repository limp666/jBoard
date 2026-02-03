"""
🚀 Tenbagger Lab - Find 10x Return Potential Stocks

A systematic approach to finding high-growth stocks based on expert methodologies
from Peter Lynch, William O'Neil (CAN SLIM), and modern growth metrics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services import stock_screener, tenbagger_scorer
import yfinance as yf

st.set_page_config(
    page_title="Tenbagger Lab",
    page_icon="🚀",
    layout="wide",
)

st.title("🚀 Tenbagger Lab")
st.markdown(
    "체계적인 종목 스크리닝으로 10배 수익 가능성이 있는 성장주를 발굴합니다. "
    "피터 린치, 윌리엄 오닐(CAN SLIM) 등전문가 방법론 기반."
)

# Sidebar - Filters
st.sidebar.header("⚙️ 스크리닝 설정")

# SCAN MODE SELECTION
st.sidebar.subheader("🔍 스캔 범위")
scan_mode = st.sidebar.radio(
    "종목 범위 선택",
    options=["curated", "index", "full"],
    format_func=lambda x: {
        "curated": "📋 핵심 리스트 (~200개, 빠름 2-5분)",
        "index": "📊 주요 인덱스 (500-1500개, 중간 10-20분)",
        "full": "🌐 전체 시장 (3000+개, 느림 1-2시간)"
    }[x],
    index=0
)

if scan_mode == "full":
    st.sidebar.warning("⚠️ 전체 스캔은 1-2시간 소요됩니다!")
elif scan_mode == "index":
    st.sidebar.info("💡 S&P 500, NASDAQ 100 등 스캔")

sector_filter_universe = None
if scan_mode in ["index", "full"]:
    sector_for_scan = st.sidebar.selectbox(
        "스캔 대상 섹터",
        options=["전체"] + stock_screener.get_sector_list(),
        index=0
    )
    if sector_for_scan != "전체":
        sector_filter_universe = sector_for_scan

st.sidebar.markdown("---")


# Market Cap Filter
st.sidebar.subheader("시가총액")
market_cap_range = st.sidebar.select_slider(
    "범위 (억 달러)",
    options=[0.2, 0.5, 1, 2, 5, 10, 20, 50, 100],
    value=(0.5, 5),
    format_func=lambda x: f"${x}B"
)
min_market_cap = market_cap_range[0] * 1e9
max_market_cap = market_cap_range[1] * 1e9

# Growth Filters
st.sidebar.subheader("성장률 기준")
min_revenue_growth = st.sidebar.slider(
    "최소 매출 성장률 (%)",
    min_value=0,
    max_value=100,
    value=15,
    step=5
)

min_earnings_growth = st.sidebar.slider(
    "최소 이익 성장률 (%)",
    min_value=0,
    max_value=100,
    value=15,
    step=5
)

# Valuation Filter
max_peg_ratio = st.sidebar.slider(
    "최대 PEG Ratio",
    min_value=0.5,
    max_value=3.0,
    value=2.0,
    step=0.1
)

# Profitability Filter
min_roe = st.sidebar.slider(
    "최소 ROE (%)",
    min_value=0,
    max_value=50,
    value=10,
    step=5
)

# Financial Health Filter
max_debt_to_equity = st.sidebar.slider(
    "최대 부채비율 (D/E)",
    min_value=0.0,
    max_value=2.0,
    value=1.0,
    step=0.1
)

# Sector Filter
st.sidebar.subheader("섹터 필터")
all_sectors = stock_screener.get_sector_list()
selected_sectors = st.sidebar.multiselect(
    "섹터 선택 (전체 선택 = 필터 없음)",
    options=all_sectors,
    default=[]
)

st.sidebar.markdown("---")
run_screen = st.sidebar.button("🔍 스크리닝 실행", type="primary", use_container_width=True)

# Scoring Weight Customization (Advanced)
with st.sidebar.expander("⚖️ 고급: 점수 가중치 조정"):
    st.markdown("각 지표의 중요도를 조정하세요 (기본값: 1.0)")
    
    weight_revenue = st.slider("매출 성장", 0.0, 2.0, 1.0, 0.1, key="w_rev")
    weight_earnings = st.slider("이익 성장", 0.0, 2.0, 1.0, 0.1, key="w_earn")
    weight_peg = st.slider("PEG Ratio", 0.0, 2.0, 1.0, 0.1, key="w_peg")
    weight_roe = st.slider("ROE", 0.0, 2.0, 1.0, 0.1, key="w_roe")
    weight_momentum = st.slider("모멘텀", 0.0, 2.0, 1.0, 0.1, key="w_mom")
    
    custom_weights = {
        "revenue_growth": weight_revenue,
        "earnings_growth": weight_earnings,
        "peg_ratio": weight_peg,
        "roe": weight_roe,
        "momentum": weight_momentum,
    }

# Main Content
if run_screen:
    with st.spinner(f"🔍 종목 스크리닝 중... ({scan_mode} 모드)"):
        # Get stock universe
        tickers = stock_screener.get_stock_universe(
            mode=scan_mode,
            min_market_cap=min_market_cap,
            max_market_cap=max_market_cap,
            sector_filter=sector_filter_universe
        )
        
        st.info(f"📊 {len(tickers)}개 종목을 스캔합니다...")
        
        # Progress bar
        progress_bar = st.progress(0)
        progress_text = st.empty()
        
        def update_progress(current, total, ticker="", company_name=""):
            progress = current / total
            progress_bar.progress(progress)
            progress_text.text(f"진행: {current}/{total} ({progress*100:.1f}%) | 분석 중: {ticker} - {company_name}")
        
        # Screen stocks
        screened_df = stock_screener.screen_stocks(
            tickers=tickers,
            min_revenue_growth=min_revenue_growth,
            min_earnings_growth=min_earnings_growth,
            max_peg_ratio=max_peg_ratio,
            min_roe=min_roe,
            max_debt_to_equity=max_debt_to_equity,
            progress_callback=update_progress
        )
        
        progress_bar.empty()
        progress_text.empty()
        
        if screened_df.empty:
            st.warning("⚠️ 선택한 조건에 맞는 종목이 없습니다. 필터를 조정해보세요.")
        else:
            # Apply sector filter if selected
            if selected_sectors:
                screened_df = screened_df[screened_df["sector"].isin(selected_sectors)]
            
            # Calculate Tenbagger Scores
            with st.spinner("📊 텐배거 점수 계산 중..."):
                scored_df = tenbagger_scorer.score_stocks_dataframe(screened_df, custom_weights)
            
            # Sort by score
            scored_df = scored_df.sort_values("tenbagger_score", ascending=False)
            
            # Store in session state
            st.session_state["screened_stocks"] = scored_df
            
            st.success(f"✅ {len(scored_df)}개 종목을 발견했습니다!")

# Display Results
if "screened_stocks" in st.session_state:
    df = st.session_state["screened_stocks"]
    
    # Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("발견된 종목", f"{len(df)}개")
    with col2:
        avg_score = df["tenbagger_score"].mean()
        st.metric("평균 점수", f"{avg_score:.1f}")
    with col3:
        top_score = df["tenbagger_score"].max()
        st.metric("최고 점수", f"{top_score:.1f}")
    with col4:
        high_scorers = len(df[df["tenbagger_score"] >= 70])
        st.metric("70점 이상", f"{high_scorers}개")
    
    st.markdown("---")
    
    # Top Picks Section
    st.subheader("🏆 Top 10 Tenbagger 후보")
    
    top10 = df.head(10)
    
    # Display table
    display_cols = {
        "ticker": "티커",
        "name": "회사명",
        "sector": "섹터",
        "tenbagger_score": "점수",
        "risk_level": "리스크",
        "price": "현재가",
        "market_cap": "시가총액",
        "revenue_growth": "매출성장",
        "earnings_growth": "이익성장",
        "peg_ratio": "PEG",
        "roe": "ROE",
    }
    
    display_df = top10[list(display_cols.keys())].copy()
    display_df.columns = list(display_cols.values())
    
    # Format columns
    display_df["현재가"] = display_df["현재가"].apply(lambda x: f"${x:,.2f}")
    display_df["시가총액"] = display_df["시가총액"].apply(lambda x: f"${x/1e9:.2f}B")
    display_df["매출성장"] = display_df["매출성장"].apply(lambda x: f"{x:+.1f}%")
    display_df["이익성장"] = display_df["이익성장"].apply(lambda x: f"{x:+.1f}%")
    display_df["PEG"] = display_df["PEG"].apply(lambda x: f"{x:.2f}" if x > 0 else "N/A")
    display_df["ROE"] = display_df["ROE"].apply(lambda x: f"{x:.1f}%")
    
    # Color code scores
    def color_score(val):
        if val >= 80:
            return f'background-color: #d4edda; color: #155724'  # Green
        elif val >= 70:
            return f'background-color: #d1ecf1; color: #0c5460'  # Blue
        elif val >= 60:
            return f'background-color: #fff3cd; color: #856404'  # Yellow
        else:
            return ''
    
    styled_df = display_df.style.applymap(
        color_score,
        subset=["점수"]
    )
    
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # Score distribution chart
    st.subheader("📊 점수 분포")
    fig_hist = px.histogram(
        df,
        x="tenbagger_score",
        nbins=20,
        labels={"tenbagger_score": "Tenbagger 점수", "count": "종목 수"},
        title="전체 종목 점수 분포",
        color_discrete_sequence=["#1f77b4"]
    )
    fig_hist.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        height=300
    )
    st.plotly_chart(fig_hist, width='stretch')
    
    # Sector breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏭 섹터별 분포")
        sector_counts = df["sector"].value_counts().head(10)
        fig_sector = px.bar(
            sector_counts,
            orientation='h',
            labels={"value": "종목 수", "index": "섹터"},
            color_discrete_sequence=["#2ca02c"]
        )
        fig_sector.update_layout(showlegend=False, height=350, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_sector, width='stretch')
    
    with col2:
        st.subheader("⚠️ 리스크 분포")
        risk_counts = df["risk_level"].value_counts()
        fig_risk = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            color=risk_counts.index,
            color_discrete_map={"Low": "#28a745", "Medium": "#ffc107", "High": "#dc3545"}
        )
        fig_risk.update_layout(height=350)
        st.plotly_chart(fig_risk, width='stretch')
    
    # Detailed Analysis Section
    st.markdown("---")
    st.subheader("🔬 종목 상세 분석")
    
    selected_ticker = st.selectbox(
        "분석할 종목 선택",
        options=top10["ticker"].tolist(),
        format_func=lambda x: f"{x} - {top10[top10['ticker']==x]['name'].iloc[0]}"
    )
    
    if selected_ticker:
        stock_data = df[df["ticker"] == selected_ticker].iloc[0]
        
        # Key Metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Tenbagger 점수", f"{stock_data['tenbagger_score']:.1f}/100")
        with col2:
            st.metric("매출 성장률", f"{stock_data['revenue_growth']:+.1f}%")
        with col3:
            st.metric("이익 성장률", f"{stock_data['earnings_growth']:+.1f}%")
        with col4:
            st.metric("PEG Ratio", f"{stock_data['peg_ratio']:.2f}")
        with col5:
            st.metric("ROE", f"{stock_data['roe']:.1f}%")
        
        # Score Breakdown
        st.markdown("**점수 세부 내역**")
        score_breakdown = {
            "매출 성장": stock_data["score_revenue_growth"],
            "이익 성장": stock_data["score_earnings_growth"],
            "PEG": stock_data["score_peg_ratio"],
            "ROE": stock_data["score_roe"],
            "수익성": stock_data["score_profit_margin"],
            "재무 건전성": stock_data["score_financial_health"],
            "모멘텀": stock_data["score_momentum"],
            "상대 강도": stock_data["score_relative_strength"],
            "기관 보유":stock_data["score_institutional_ownership"],
            "시총 적정성": stock_data["score_market_cap"]
        }
        
        fig_breakdown = go.Figure(go.Bar(
            x=list(score_breakdown.values()),
            y=list(score_breakdown.keys()),
            orientation='h',
            marker=dict(
                color=list(score_breakdown.values()),
                colorscale='RdYlGn',
                cmin=0,
                cmax=10
            ),
            text=[f"{v:.1f}" for v in score_breakdown.values()],
            textposition='auto',
        ))
        fig_breakdown.update_layout(
            title=f"{selected_ticker} 점수 세부 분석 (각 항목 0-10점)",
            xaxis_title="점수",
            yaxis_title="",
            height=400,
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_breakdown, width='stretch')
        
        # Price Chart
        st.markdown("**주가 차트 (1년)**")
        try:
            ticker_obj = yf.Ticker(selected_ticker)
            hist = ticker_obj.history(period="1y")
            
            fig_price = go.Figure()
            fig_price.add_trace(go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close'],
                name="Price"
            ))
            fig_price.update_layout(
                title=f"{selected_ticker} 주가 추이",
                yaxis_title="Price ($)",
                height=400,
                xaxis_rangeslider_visible=False,
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_price, width='stretch')
        except Exception as e:
            st.error(f"차트 로드 실패: {e}")

    # Download option
    st.markdown("---")
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 전체 결과 CSV 다운로드",
        data=csv,
        file_name="tenbagger_candidates.csv",
        mime="text/csv"
    )

else:
    # Initial state - show instructions
    st.info(
        "👈 왼쪽 사이드바에서 스크리닝 조건을 설정하고 '스크리닝 실행' 버튼을 클릭하세요."
    )
    
    st.markdown("### 📚 사용법")
    st.markdown("""
    1. **필터 설정**: 시가총액, 성장률, 밸류에이션, 재무 건전성 기준을 설정합니다.
    2. **스크리닝**: 조건에 맞는 종목을 찾습니다.
    3. **점수 확인**: 0-100점 Tenbagger 점수로 순위가 매겨집니다.
    4. **상세 분석**: 관심 종목의 세부 지표와 차트를 확인합니다.
    """)
    
    st.markdown("### 🎯 점수 시스템")
    st.markdown("""
    **총 100점** - 10개 지표 × 각 10점
    
    - **성장성** (30점): 매출/이익 성장률, PEG
    - **수익성** (20점): ROE, 이익률
    - **재무 건전성** (10점): 부채비율, 유동성
    - **모멘텀** (20점): 6개월 수익률, 52주 신고가 근접도
    - **펀더멘털** (20점): 기관 보유, 시총 적정성
    """)
    
    st.markdown("### ⚠️ 유의사항")
    st.markdown("""
    - 이 도구는 참고용이며, 투자 결정은 본인의 판단과 책임입니다.
    - 높은 점수가 반드시 수익을 보장하지 않습니다.
    - 추가적인 리서치와 리스크 관리가 필수입니다.
    """)

st.caption("데이터 출처: Yahoo Finance (15분 지연)")
