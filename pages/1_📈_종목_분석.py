import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from services import yfinance_client
from services.yfinance_client import (
    get_stock_info,
    get_stock_history,
    get_stock_financials,
    calculate_advanced_metrics,
    get_historical_metrics,
    search_symbols,
    calculate_sector_averages  # NEW: Sector comparison
)

st.set_page_config(page_title="종목 분석", page_icon="📈", layout="wide")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def safe_fmt(val, fmt="{:,.2f}", suffix=""):
    """Safely format numeric values"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "N/A"
    try:
        return fmt.format(val) + suffix
    except:
        return "N/A"

def human_format(num):
    """Format large numbers in human-readable format (K, M, B, T)"""
    if num is None or pd.isna(num):
        return "N/A"
    try:
        num = float('{:.3g}'.format(num))
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])
    except:
        return "N/A"

def create_trend_chart(data: pd.Series, title: str, y_label: str, color: str = "blue", format_as_billions: bool = False):
    """Create a line chart for time-series data"""
    if data.empty:
        return None
    
    # Sort by index (date)
    data = data.sort_index()
    
    # Format values for display
    if format_as_billions:
        y_values = data / 1e9  # Convert to billions
        y_label = f"{y_label} (Billions)"
    else:
        y_values = data
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data.index,
        y=y_values,
        mode='lines+markers',
        line=dict(color=color, width=2),
        marker=dict(size=8),
        name=title
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Period",
        yaxis_title=y_label,
        template="plotly_dark",
        height=350,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

# ============================================================================
# DISPLAY FUNCTIONS FOR TABS
# ============================================================================

def display_valuation_tab(info: dict, advanced_metrics: dict, sector_avg: dict = None):
    """Tab 1: Core valuation metrics with sector comparison"""
    
    # Sector comparison banner
    sector = info.get('sector')
    if sector and sector_avg:
        st.info(f"📊 Comparing to **{sector}** sector average (median of industry leaders)")
    
    st.subheader("💰 Valuation Metrics (밸류에이션)")
    
    # Currency handling
    currency = info.get('currency', 'USD')
    currency_symbol = "$" if currency == "USD" else "₩" if currency == "KRW" else currency + " "
    
    # Row 1: Core valuation
    c1, c2, c3, c4, c5 = st.columns(5)
    
    c1.metric(
        "Market Cap", 
        f"{currency_symbol}{human_format(info.get('marketCap'))}",
        help="기업의 총 가치. 주가 × 발행주식수. 기업 규모의 기준"
    )
    c1.caption(f"Currency: {currency}")
    
    stock_pe = info.get('trailingPE')
    c2.metric(
        "PER (Trailing)", 
        safe_fmt(stock_pe),
        help="주가수익비율. 주가 / 주당순이익(EPS). 낮을수록 저평가. 업종별 차이 큼"
    )
    if sector_avg and sector_avg.get('trailing_pe'):
        sector_pe = sector_avg.get('trailing_pe')
        diff = ((stock_pe - sector_pe) / sector_pe * 100) if stock_pe and sector_pe else None
        c2.caption(f"Sector: {safe_fmt(sector_pe)} ({diff:+.1f}% vs sector)" if diff else f"Sector: {safe_fmt(sector_pe)}")
    else:
        c2.caption(f"Forward: {safe_fmt(info.get('forwardPE'))}")
    
    peg = advanced_metrics.get('peg_ratio')
    c3.metric("PEG Ratio", safe_fmt(peg), help="PER / Earnings Growth. <1은 저평가")
    
    psr = advanced_metrics.get('price_to_sales')
    c4.metric("PSR (Price/Sales)", safe_fmt(psr), help="시총 / 매출")
    
    stock_pbr = info.get('priceToBook')
    c5.metric(
        "PBR (Price/Book)", 
        safe_fmt(stock_pbr),
        help="주가순자산비율. 주가 / 주당순자산(BPS). <1이면 청산가치 이하"
    )
    if sector_avg and sector_avg.get('price_to_book'):
        sector_pbr = sector_avg.get('price_to_book')
        diff = ((stock_pbr - sector_pbr) / sector_pbr * 100) if stock_pbr and sector_pbr else None
        c5.caption(f"Sector: {safe_fmt(sector_pbr)} ({diff:+.1f}%)" if diff else f"Sector: {safe_fmt(sector_pbr)}")
    
    st.divider()
    
    # Row 2: Enterprise Value metrics
    st.markdown("#### 🏢 Enterprise Value Metrics")
    ev1, ev2, ev3, ev4 = st.columns(4)
    
    ev = info.get('enterpriseValue')
    ev1.metric(
        "Enterprise Value", 
        f"{currency_symbol}{human_format(ev)}",
        help="시가총액 + 순부채. 인수 시 필요한 실제 금액"
    )
    
    ev_rev = advanced_metrics.get('ev_to_revenue')
    ev2.metric(
        "EV / Revenue", 
        safe_fmt(ev_rev),
        help="기업가치 / 매출. PSR과 유사하나 부채 고려. 성장주 평가에 유용"
    )
    
    ev_ebitda = advanced_metrics.get('ev_to_ebitda')
    ev3.metric(
        "EV / EBITDA", 
        safe_fmt(ev_ebitda),
        help="기업가치 / EBITDA. 업종 간 비교에 유용. <10 저평가, >15 고평가 경향"
    )
    
    fcf_yield = advanced_metrics.get('fcf_yield')
    ev4.metric("FCF Yield", safe_fmt(fcf_yield, "{:.2f}", "%"), help="Free Cash Flow / Market Cap")
    
    st.divider()
    
    # Row 3: Profitability
    st.markdown("#### 📊 Profitability & Efficiency (수익성 & 효율성)")
    p1, p2, p3, p4, p5 = st.columns(5)
    
    roe = info.get('returnOnEquity')
    p1.metric("ROE", safe_fmt(roe * 100 if roe else None, "{:.2f}", "%"), help="자기자본이익률")
    if sector_avg and sector_avg.get('return_on_equity'):
        sector_roe = sector_avg.get('return_on_equity') * 100
        diff = ((roe * 100 - sector_roe) if roe else None)
        p1.caption(f"Sector: {sector_roe:.2f}% ({diff:+.1f}pp)" if diff else f"Sector: {sector_roe:.2f}%")
    
    roa = advanced_metrics.get('roa')
    p2.metric("ROA", safe_fmt(roa * 100 if roa else None, "{:.2f}", "%"), help="총자산이익률")
    
    gross_margin = advanced_metrics.get('gross_margins')
    p3.metric(
        "Gross Margin", 
        safe_fmt(gross_margin * 100 if gross_margin else None, "{:.2f}", "%"),
        help="(매출 - 매출원가) / 매출. 40%+ 우수. 제품 경쟁력 지표"
    )
    
    op_margin = info.get('operatingMargins')
    p4.metric(
        "Operating Margin", 
        safe_fmt(op_margin * 100 if op_margin else None, "{:.2f}", "%"),
        help="영업이익 / 매출. 본업 수익성. 15%+ 우수"
    )
    
    net_margin = info.get('profitMargins')
    p5.metric(
        "Net Margin", 
        safe_fmt(net_margin * 100 if net_margin else None, "{:.2f}", "%"),
        help="순이익 / 매출. 최종 수익성. 10%+ 우수"
    )
    
    # Row 4: EBITDA and FCF margins
    m1, m2, m3 = st.columns(3)
    
    ebitda_margin = advanced_metrics.get('ebitda_margins')
    m1.metric(
        "EBITDA Margin", 
        safe_fmt(ebitda_margin * 100 if ebitda_margin else None, "{:.2f}", "%"),
        help="EBITDA / 매출. 현금창출 능력. 감가상각 제외한 순수 영업력"
    )
    
    fcf_margin = advanced_metrics.get('fcf_margin')
    m2.metric("FCF Margin", safe_fmt(fcf_margin, "{:.2f}", "%"), help="Free Cash Flow / Revenue")
    
    m3.metric(
        "EBITDA", 
        f"{currency_symbol}{human_format(info.get('ebitda'))}",
        help="영업이익 + 감가상각비. Earnings Before Interest, Taxes, Depreciation, Amortization"
    )
    
    st.divider()
    
    # Row 5: Financial Health
    st.markdown("#### 🏦 Financial Health (재무 건전성)")
    f1, f2, f3, f4 = st.columns(4)
    
    net_debt_ebitda = advanced_metrics.get('net_debt_to_ebitda')
    f1.metric("Net Debt / EBITDA", safe_fmt(net_debt_ebitda, "{:.2f}", "x"), help="< 3x 건전")
    
    debt_equity = info.get('debtToEquity')
    f2.metric(
        "Debt / Equity", 
        safe_fmt(debt_equity, "{:.2f}", "%"),
        help="총부채 / 자기자본 × 100. <100% 안정, >200% 위험"
    )
    if sector_avg and sector_avg.get('debt_to_equity'):
        sector_de = sector_avg.get('debt_to_equity')
        f2.caption(f"Sector: {safe_fmt(sector_de, '{:.2f}', '%')}")
    
    current_ratio = info.get('currentRatio')
    f3.metric("Current Ratio", safe_fmt(current_ratio), help="> 1.0 건전")
    
    quick_ratio = info.get('quickRatio')
    f4.metric("Quick Ratio", safe_fmt(quick_ratio), help="> 1.0 건전")
    
    # Row 6: Cash position
    cash1, cash2, cash3 = st.columns(3)
    
    total_cash = info.get('totalCash')
    cash1.metric(
        "Total Cash", 
        f"{currency_symbol}{human_format(total_cash)}",
        help="즉시 사용 가능한 현금 + 단기투자자산. 유동성의 핵심"
    )
    
    total_debt = info.get('totalDebt')
    cash2.metric(
        "Total Debt", 
        f"{currency_symbol}{human_format(total_debt)}",
        help="단기부채 + 장기부채. 상환 의무가 있는 모든 부채"
    )
    
    cash_to_mcap = advanced_metrics.get('cash_to_market_cap')
    cash3.metric(
        "Cash / Market Cap", 
        safe_fmt(cash_to_mcap, "{:.2f}", "%"),
        help="현금성자산 / 시가총액 × 100. >20% 우량, 기업 안전성 지표"
    )
    
    st.divider()
    
    # Row 7: Growth & Shareholder Returns
    st.markdown("#### 📈 Growth & Returns")
    g1, g2, g3, g4 = st.columns(4)
    
    rev_growth = info.get('revenueGrowth')
    g1.metric(
        "Revenue Growth (YoY)", 
        safe_fmt(rev_growth * 100 if rev_growth else None, "{:+.2f}", "%"),
        help="전년 대비 매출 증가율. >10% 고성장, <0% 매출 감소"
    )
    
    earn_growth = info.get('earningsGrowth')
    g2.metric(
        "Earnings Growth (YoY)", 
        safe_fmt(earn_growth * 100 if earn_growth else None, "{:+.2f}", "%"),
        help="전년 대비 순이익 증가율. 수익성 개선 추세 확인"
    )
    
    div_yield = info.get('dividendYield')
    g3.metric(
        "Dividend Yield", 
        safe_fmt(div_yield * 100 if div_yield else None, "{:.2f}", "%"),
        help="연간 배당금 / 주가 × 100. 3%+ 고배당주"
    )
    
    payout_ratio = info.get('payoutRatio')
    g4.metric(
        "Payout Ratio", 
        safe_fmt(payout_ratio * 100 if payout_ratio else None, "{:.2f}", "%"),
        help="배당금 / 순이익 × 100. 40-60% 적정, >80% 지속가능성 의문"
    )


def display_growth_analysis_tab(historical_metrics: dict):
    """Tab 2: Growth trends and margin analysis"""
    st.subheader("📈 Growth Analysis (성장 분석)")
    
    # Revenue trends
    st.markdown("#### 💵 Revenue Trends")
    col1, col2 = st.columns(2)
    
    with col1:
        if 'revenue_quarterly' in historical_metrics and not historical_metrics['revenue_quarterly'].empty:
            fig = create_trend_chart(
                historical_metrics['revenue_quarterly'],
                "Quarterly Revenue Trend",
                "Revenue (USD)",
                color="green",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        elif 'revenue_annual' in historical_metrics:
            # Fallback to annual if quarterly not available
            fig = create_trend_chart(
                historical_metrics['revenue_annual'],
                "Annual Revenue Trend",
                "Revenue (USD)",
                color="green",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Revenue data not available")
    
    with col2:
        if 'revenue_quarterly' in historical_metrics and not historical_metrics['revenue_quarterly'].empty:
            # Show quarterly growth rate chart
            quarterly_data = historical_metrics['revenue_quarterly']
            if len(quarterly_data) >= 2:
                growth_rates = quarterly_data.pct_change() * 100
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=growth_rates.index,
                    y=growth_rates.values,
                    marker_color=['green' if x >= 0 else 'red' for x in growth_rates.values],
                    name='QoQ Growth %'
                ))
                fig.update_layout(
                    title="Quarterly Revenue Growth (QoQ)",
                    xaxis_title="Period",
                    yaxis_title="Growth (%)",
                    template="plotly_dark",
                    height=350,
                    margin=dict(l=20, r=20, t=50, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Insufficient data for growth calculation")
        else:
            st.info("Quarterly data not available")
    
    st.divider()
    
    # Profitability trends
    st.markdown("#### 💰 Profitability Trends")
    
    pcol1, pcol2 = st.columns(2)
    
    with pcol1:
        if 'ebitda_quarterly' in historical_metrics and not historical_metrics['ebitda_quarterly'].empty:
            fig = create_trend_chart(
                historical_metrics['ebitda_quarterly'],
                "Quarterly EBITDA Trend",
                "EBITDA (USD)",
                color="blue",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        elif 'ebitda_annual' in historical_metrics:
            # Fallback to annual
            fig = create_trend_chart(
                historical_metrics['ebitda_annual'],
                "Annual EBITDA Trend",
                "EBITDA (USD)",
                color="blue",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("EBITDA data not available")
    
    with pcol2:
        if 'net_income_annual' in historical_metrics:
            fig = create_trend_chart(
                historical_metrics['net_income_annual'],
                "Annual Net Income Trend",
                "Net Income (USD)",
                color="purple",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Net income data not available")


def display_cashflow_tab(historical_metrics: dict, info: dict):
    """Tab 3: Cash flow analysis"""
    st.subheader("💰 Cash Flow Analysis (현금 흐름 분석)")
    
    currency = info.get('currency', 'USD')
    currency_symbol = "$" if currency == "USD" else "₩" if currency == "KRW" else currency + " "
    
    # Current cash flow metrics
    st.markdown("#### 📊 Current Metrics")
    c1, c2, c3 = st.columns(3)
    
    fcf = info.get('freeCashflow')
    c1.metric("Free Cash Flow (TTM)", f"{currency_symbol}{human_format(fcf)}")
    
    op_cf = info.get('operatingCashflow')
    c2.metric("Operating Cash Flow (TTM)", f"{currency_symbol}{human_format(op_cf)}")
    
    if fcf and op_cf and op_cf > 0:
        fcf_conversion = (fcf / op_cf) * 100
        c3.metric("FCF Conversion", f"{fcf_conversion:.1f}%", help="FCF / Operating CF")
    else:
        c3.metric("FCF Conversion", "N/A")
    
    st.divider()
    
    # Historical cash flow trends
    st.markdown("#### 📈 Cash Flow Trends")
    
    cf1, cf2 = st.columns(2)
    
    with cf1:
        if 'fcf_quarterly' in historical_metrics and not historical_metrics['fcf_quarterly'].empty:
            fig = create_trend_chart(
                historical_metrics['fcf_quarterly'],
                "Free Cash Flow Trend (Quarterly)",
                "FCF (USD)",
                color="green",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        elif 'fcf_annual' in historical_metrics:
            # Fallback to annual
            fig = create_trend_chart(
                historical_metrics['fcf_annual'],
                "Free Cash Flow Trend (Annual)",
                "FCF (USD)",
                color="green",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("FCF data not available")
    
    with cf2:
        if 'operating_cf_quarterly' in historical_metrics and not historical_metrics['operating_cf_quarterly'].empty:
            fig = create_trend_chart(
                historical_metrics['operating_cf_quarterly'],
                "Operating Cash Flow Trend (Quarterly)",
                "Operating CF (USD)",
                color="blue",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        elif 'operating_cf_annual' in historical_metrics:
            # Fallback to annual
            fig = create_trend_chart(
                historical_metrics['operating_cf_annual'],
                "Operating Cash Flow Trend (Annual)",
                "Operating CF (USD)",
                color="blue",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Operating CF data not available")
    
    st.divider()
    
    # Capital Allocation
    st.markdown("#### 💸 Capital Allocation")
    
    ca1, ca2 = st.columns(2)
    
    with ca1:
        if 'capex_annual' in historical_metrics:
            # Make CapEx positive for display (it's usually negative)
            capex_data = -historical_metrics['capex_annual']
            fig = create_trend_chart(
                capex_data,
                "Capital Expenditure Trend",
                "CapEx (USD)",
                color="orange",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("CapEx data not available")
    
    with ca2:
        if 'buybacks_annual' in historical_metrics:
            # Make buybacks positive
            buybacks_data = -historical_metrics['buybacks_annual']
            fig = create_trend_chart(
                buybacks_data,
                "Share Buybacks Trend",
                "Buybacks (USD)",
                color="red",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Buyback data not available")


def display_balance_sheet_tab(historical_metrics: dict, info: dict):
    """Tab 4: Balance sheet trends"""
    st.subheader("🏦 Balance Sheet (재무상태)")
    
    currency = info.get('currency', 'USD')
    currency_symbol = "$" if currency == "USD" else "₩" if currency == "KRW" else currency + " "
    
    # Assets & Cash
    st.markdown("#### 💵 Assets & Cash Position")
    
    a1, a2 = st.columns(2)
    
    with a1:
        if 'total_assets_quarterly' in historical_metrics and not historical_metrics['total_assets_quarterly'].empty:
            fig = create_trend_chart(
                historical_metrics['total_assets_quarterly'],
                "Total Assets Trend (Quarterly)",
                "Assets (USD)",
                color="green",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        elif 'total_assets_annual' in historical_metrics:
            # Fallback to annual
            fig = create_trend_chart(
                historical_metrics['total_assets_annual'],
                "Total Assets Trend (Annual)",
                "Assets (USD)",
                color="green",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Assets data not available")
    
    with a2:
        if 'cash_quarterly' in historical_metrics and not historical_metrics['cash_quarterly'].empty:
            fig = create_trend_chart(
                historical_metrics['cash_quarterly'],
                "Cash & Equivalents Trend (Quarterly)",
                "Cash (USD)",
                color="blue",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        elif 'cash_annual' in historical_metrics:
            # Fallback to annual
            fig = create_trend_chart(
                historical_metrics['cash_annual'],
                "Cash & Equivalents Trend (Annual)",
                "Cash (USD)",
                color="blue",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Cash data not available")
    
    st.divider()
    
    # Debt Position
    st.markdown("#### 📊 Debt Position")
    
    d1, d2 = st.columns(2)
    
    with d1:
        if 'total_debt_quarterly' in historical_metrics and not historical_metrics['total_debt_quarterly'].empty:
            fig = create_trend_chart(
                historical_metrics['total_debt_quarterly'],
                "Total Debt Trend (Quarterly)",
                "Debt (USD)",
                color="red",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        elif 'total_debt_annual' in historical_metrics:
            # Fallback to annual
            fig = create_trend_chart(
                historical_metrics['total_debt_annual'],
                "Total Debt Trend (Annual)",
                "Debt (USD)",
                color="red",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Debt data not available")
    
    with d2:
        if 'net_debt_annual' in historical_metrics:
            fig = create_trend_chart(
                historical_metrics['net_debt_annual'],
                "Net Debt Trend",
                "Net Debt (USD)",
                color="orange",
                format_as_billions=True
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Net debt data not available")


def display_technical_analysis_tab(df: pd.DataFrame, ticker: str):
    """Tab 5: Technical analysis (existing functionality)"""
    st.subheader("📊 Technical Analysis (기술적 분석)")
    
    if df.empty:
        st.warning("No price data available for technical analysis")
        return
    
    # Create chart
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
        title=f"{ticker} Technical Analysis",
        xaxis_rangeslider_visible=False,
        height=800,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Technical indicators summary
    if not df.empty:
        last = df.iloc[-1]
        current_price = last['Close']
        
        st.markdown("#### 📊 Current Technical Indicators")
        t1, t2, t3, t4 = st.columns(4)
        
        t1.metric("Current Price", f"${current_price:.2f}")
        t1.caption(f"MA 20: ${last.get('SMA_20', 0):.2f}")
        
        if 'RSI' in df.columns:
            rsi = last['RSI']
            t2.metric("RSI (14)", f"{rsi:.1f}")
            if rsi < 30:
                t2.caption("🔵 Oversold")
            elif rsi > 70:
                t2.caption("🔴 Overbought")
            else:
                t2.caption("⚪ Neutral")
        
        if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            macd = last['MACD']
            signal = last['MACD_Signal']
            t3.metric("MACD", f"{macd:.2f}")
            if macd > signal:
                t3.caption("🟢 Bullish")
            else:
                t3.caption("🔴 Bearish")
        
        volume = last['Volume']
        avg_vol = df['Volume'].tail(20).mean()
        t4.metric("Volume", human_format(volume))
        vol_ratio = (volume / avg_vol) if avg_vol > 0 else 0
        t4.caption(f"{vol_ratio:.1f}x vs 20D avg")

# ============================================================================
# TECHNICAL INDICATOR CALCULATIONS
# ============================================================================

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

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.title("📈 Advanced Stock Analysis (고급 종목 분석)")
    st.caption("Comprehensive financial analysis with institutional-grade metrics")
    
    # --- Sidebar Input ---
    with st.sidebar:
        st.header("🔍 Stock Search")
        
        # Ticker Search UI
        search_query = st.text_input("Search (Ticker/Company)", placeholder="e.g., Apple, Tesla, NVDA")
        
        ticker = None
        
        if search_query:
            results = search_symbols(search_query)
            if results:
                options = [r['display'] for r in results]
                selected_option = st.selectbox("Select from results", options)
                
                for r in results:
                    if r['display'] == selected_option:
                        ticker = r['symbol']
                        break
            else:
                st.warning("No results found. Try exact ticker.")
                ticker = search_query.upper()
        else:
            st.info("👆 Enter a ticker or company name above")
            ticker = None

    if not ticker:
        # Show welcome screen with instructions
        st.info("📌 Use the sidebar to search for a stock to analyze")
        st.markdown("""
        ### Features:
        - **📊 Core Metrics**: Comprehensive valuation, profitability, and financial health
        - **📈 Growth Analysis**: Revenue and profitability trends over time
        - **💰 Cash Flow**: FCF, operating cash flow, and capital allocation
        - **🏦 Balance Sheet**: Assets, debt, and financial position trends
        - **📉 Technical Analysis**: Charts with indicators (MA, RSI, MACD)
        """)
        return

    # --- Fetch Data ---
    with st.spinner(f"Analyzing {ticker}..."):
        # 1. Basic Info
        info = get_stock_info(ticker)
        if not info or len(info) < 5:
            st.error("Unable to fetch stock data. Please check the ticker.")
            return

        # 2. Price History (for technical analysis)
        df = get_stock_history(ticker, period="2y")
        if not df.empty:
            df = calculate_indicators(df)
        
        # 3. Financial Statements
        financials = get_stock_financials(ticker)
        
        # 4. Calculate Advanced Metrics
        advanced_metrics = calculate_advanced_metrics(info, financials)
        
        # 5. Extract Historical Metrics
        historical_metrics = get_historical_metrics(financials)
        
    # Display company header
    st.markdown(f"## {info.get('longName', ticker)} ({ticker})")
    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        st.caption(f"**Sector**: {info.get('sector', 'N/A')} | **Industry**: {info.get('industry', 'N/A')}")
    with col_b:
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        if current_price:
            st.metric("Current Price", f"${current_price:.2f}")
    with col_c:
        prev_close = info.get('previousClose')
        if current_price and prev_close:
            change_pct = ((current_price - prev_close) / prev_close) * 100
            st.metric("Change", f"{change_pct:+.2f}%")
    
    st.divider()
    
    # --- Tabbed Interface ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Core Metrics",
        "📈 Growth Analysis",
        "💰 Cash Flow",
        "🏦 Balance Sheet",
        "📉 Technical"
    ])
    
    with tab1:
        # Fetch sector averages with caching
        sector = info.get('sector')
        sector_avg = {}
        if sector:
            with st.spinner(f"Loading {sector} sector benchmarks..."):
                try:
                    sector_avg = st.cache_data(ttl=3600)(calculate_sector_averages)(sector)
                except Exception as e:
                    st.warning(f"Could not load sector averages: {e}")
        
        display_valuation_tab(info, advanced_metrics, sector_avg)
    
    with tab2:
        display_growth_analysis_tab(historical_metrics)
    
    with tab3:
        display_cashflow_tab(historical_metrics, info)
    
    with tab4:
        display_balance_sheet_tab(historical_metrics, info)
    
    with tab5:
        display_technical_analysis_tab(df, ticker)
    
    # Company description at bottom
    with st.expander("📋 Company Description", expanded=False):
        st.write(info.get('longBusinessSummary', 'No description available'))

if __name__ == "__main__":
    main()
