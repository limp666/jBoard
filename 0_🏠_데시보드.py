import os
# Force Deploy Update: Fixed KeyError issue
import importlib.util
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

from services import yfinance_client

# Avoid package import (`from data import ...`) to prevent Streamlit Cloud
# module-resolution edge cases. Always load sample data by explicit file path.
_sample_path = Path(__file__).parent / "data" / "sample_data.py"
_spec = importlib.util.spec_from_file_location("sample_data_fallback", _sample_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load sample_data fallback from {_sample_path}")
sample_data = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sample_data)

st.set_page_config(
    page_title="미국 증시 섹터 데시보드",
    page_icon="📈",
    layout="wide",
)

MARKET_SYMBOLS = {"SPY", "QQQ", "DIA", "IWM", "^GSPC", "^DJI", "^IXIC", "MARKET"}
SECTOR_ETF_SYMBOLS = set(yfinance_client.SECTOR_ETF_MAP.values())

CATEGORY_ORDER = [
    "시장/거시",
    "섹터 ETF",
    "개별 종목",
    "기업/산업",
    "기타",
]

CATEGORY_ICON = {
    "시장/거시": "🌎",
    "섹터 ETF": "📊",
    "개별 종목": "🏢",
    "기업/산업": "🏭",
    "기타": "📰",
}

MACRO_KEYWORDS = [
    "federal reserve",
    "inflation",
    "interest rate",
    "treasury",
    "cpi",
    "pce",
    "jobs report",
    "recession",
    "nasdaq",
    "s&p 500",
    "dow",
    "market",
]


def _normalize_change(value) -> float:
    """Convert percentage values that may be strings into floats."""

    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.replace("%", "").replace("+", "").strip()
        try:
            return float(stripped)
        except ValueError:
            return 0.0
    return 0.0


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_sector_performance():
    return yfinance_client.get_sector_performance()


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_sector_etf_quotes():
    return yfinance_client.get_sector_etf_quotes()


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_market_indices(symbols: Iterable[str]):
    return yfinance_client.get_market_indices(symbols)


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_news(tickers: Iterable[str], limit: int, include_general: bool):
    return yfinance_client.get_news(tickers, limit=limit, include_general=include_general)


def _load_sector_performance() -> Tuple[pd.DataFrame, str]:
    try:
        data = _fetch_sector_performance()
        if not data:  # Raise exception if empty to trigger fallback
            raise ValueError("No sector performance data returned from API")
        source = "live"
    except Exception as exc:  # noqa: BLE001
        st.warning(
            f"실시간 섹터 데이터를 불러오지 못했습니다. ({exc})\n"
            "샘플 데이터를 표시합니다."
        )
        data = sample_data.SECTOR_PERFORMANCE
        source = "sample"

    df = pd.DataFrame(data)
    if "changesPercentage" in df.columns:
        df["change_pct"] = df["changesPercentage"].apply(_normalize_change)
    elif "change" in df.columns:
        df["change_pct"] = df["change"].apply(_normalize_change)
    else:
        df["change_pct"] = 0.0
    return df, source


def _load_sector_etfs() -> Tuple[pd.DataFrame, str]:
    try:
        data = _fetch_sector_etf_quotes()
        if not data:  # Raise exception if empty to trigger fallback
            raise ValueError("No sector ETF data returned from API")
        source = "live"
    except Exception as exc:  # noqa: BLE001
        st.warning(
            f"섹터 ETF 정보를 불러오지 못했습니다. ({exc})\n"
            "샘플 데이터를 표시합니다."
        )
        data = sample_data.SECTOR_ETF_QUOTES
        source = "sample"
    df = pd.DataFrame(data)
    return df, source


def _load_market_overview() -> Tuple[pd.DataFrame, str]:
    indices = ["^GSPC", "^DJI", "^IXIC"]
    try:
        data = _fetch_market_indices(indices)
        if not data:  # Raise exception if empty to trigger fallback
            raise ValueError("No market index data returned from API")
        source = "live"
    except Exception as exc:  # noqa: BLE001
        st.warning(
            f"주요 지수 데이터를 불러오지 못했습니다. ({exc})\n"
            "샘플 데이터를 표시합니다."
        )
        data = [item for item in sample_data.MARKET_INDICES if item["symbol"] in indices]
        source = "sample"
    df = pd.DataFrame(data)
    
    # Handle empty case or missing columns
    if df.empty:
        return df, source
        
    if "changesPercentage" in df.columns:
        df["change_pct"] = df["changesPercentage"].apply(_normalize_change)
    elif "change" in df.columns:
        df["change_pct"] = df["change"].apply(_normalize_change)
    else:
        df["change_pct"] = 0.0
        
    return df, source


def _load_news(tickers: List[str], limit: int, include_general: bool) -> Tuple[pd.DataFrame, str]:
    try:
        data = _fetch_news(tickers, limit, include_general)
        source = "live"
    except Exception as exc:  # noqa: BLE001
        st.warning(
            f"뉴스 데이터를 불러오지 못했습니다. ({exc})\n"
            "샘플 데이터를 표시합니다."
        )
        data = sample_data.NEWS_ITEMS[:limit]
        source = "sample"
    df = pd.DataFrame(data)
    if "publishedDate" in df.columns:
        df["publishedDate"] = pd.to_datetime(df["publishedDate"], errors="coerce", utc=True).dt.tz_convert(None)
    return df, source


def _sector_to_ticker(sector_name: str) -> str:
    return yfinance_client.SECTOR_ETF_MAP.get(sector_name, "").upper()


def _truncate_text(text: str, max_len: int = 260) -> str:
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return f"{text[:max_len].rstrip()}..."


def _categorize_news_item(row: pd.Series) -> str:
    symbol = str(row.get("symbol", "") or "").upper()
    title = str(row.get("title", "") or "").lower()
    summary = str(row.get("summary", "") or row.get("text", "") or "").lower()
    content = f"{title} {summary}"

    if symbol in MARKET_SYMBOLS:
        return "시장/거시"
    if symbol in SECTOR_ETF_SYMBOLS:
        return "섹터 ETF"
    if any(keyword in content for keyword in MACRO_KEYWORDS):
        return "시장/거시"
    if symbol and symbol.isalpha() and 1 <= len(symbol) <= 5:
        return "개별 종목"
    if any(word in content for word in ["earnings", "guidance", "acquisition", "merger", "downgrade", "upgrade"]):
        return "기업/산업"
    return "기타"


def _prepare_news_dataframe(news_df: pd.DataFrame) -> pd.DataFrame:
    if news_df.empty:
        return news_df

    df = news_df.copy()
    df["category"] = df.apply(_categorize_news_item, axis=1)
    if "publishedDate" in df.columns:
        df["publishedDate"] = pd.to_datetime(df["publishedDate"], errors="coerce")
    return df.sort_values("publishedDate", ascending=False)


def render_market_overview():
    st.subheader("📊 지수 및 섹터 현황")
    market_df, _ = _load_market_overview()
    
    # Handle empty DataFrame
    if market_df.empty:
        st.info("표시할 지수 데이터가 없습니다.")
        return
    
    cols = st.columns(len(market_df))
    for col, (_, row) in zip(cols, market_df.iterrows()):
        col.metric(
            label=row.get("name", row.get("symbol")),
            value=f"{row.get('price', 0):,.2f}",
            delta=f"{row.get('change_pct', 0):+.2f}%",
        )


def render_sector_performance():
    st.subheader("🏭 섹터 퍼포먼스")
    sector_df, source = _load_sector_performance()
    if sector_df.empty:
        st.info("표시할 섹터 데이터가 없습니다.")
        return

    display_df = sector_df.drop_duplicates(subset=["sector"]).sort_values("change_pct")
    fig = px.bar(
        display_df,
        x="change_pct",
        y="sector",
        orientation="h",
        color="change_pct",
        color_continuous_scale=["#d73027", "#fee08b", "#1a9850"],
        labels={"change_pct": "변동률 (%)", "sector": "섹터"},
        title="일간 기준 섹터 변동률",
        height=460,
    )
    fig.update_layout(coloraxis_showscale=False, plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width='stretch')

    top_gainers = display_df.nlargest(3, "change_pct")[["sector", "change_pct"]]
    laggards = display_df.nsmallest(3, "change_pct")[["sector", "change_pct"]]

    gainers_cols = st.columns(2)
    with gainers_cols[0]:
        st.markdown("**상승 상위 섹터**")
        for _, row in top_gainers.iterrows():
            st.write(f"{row['sector']}: {row['change_pct']:+.2f}%")
    with gainers_cols[1]:
        st.markdown("**하락 상위 섹터**")
        for _, row in laggards.iterrows():
            st.write(f"{row['sector']}: {row['change_pct']:+.2f}%")

    st.markdown("**전체 데이터**")
    st.dataframe(
        display_df.set_index("sector")[["change_pct"]],
        width='stretch',
        height=350,
    )

    if source == "sample":
        st.caption("샘플 데이터가 사용되었습니다.")

    return display_df


def render_sector_etfs():
    st.subheader("📈 섹터 ETF 스냅샷")
    etf_df, source = _load_sector_etfs()
    if etf_df.empty:
        st.info("표시할 ETF 데이터가 없습니다.")
        return

    display_cols = ["symbol", "name", "price", "changesPercentage", "change", "yearHigh", "yearLow", "volume"]
    available_cols = [col for col in display_cols if col in etf_df.columns]
    formatted_df = etf_df[available_cols].rename(
        columns={
            "symbol": "티커",
            "name": "ETF 이름",
            "price": "가격",
            "changesPercentage": "변동률 (%)",
            "change": "변동",
            "yearHigh": "52주 고점",
            "yearLow": "52주 저점",
            "volume": "거래량",
        }
    )
    st.dataframe(formatted_df, width='stretch', height=320)
    if source == "sample":
        st.caption("샘플 데이터가 사용되었습니다.")


def render_news_section(selected_tickers: List[str], limit: int, include_general: bool):
    st.subheader("📰 당일 주요 뉴스")
    news_df, source = _load_news(selected_tickers, limit, include_general)

    if news_df.empty:
        st.info("표시할 뉴스가 없습니다.")
        return

    news_df = _prepare_news_dataframe(news_df)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**헤드라인 바로가기**")
    with col2:
        unique_sources = news_df["site"].dropna().nunique() if "site" in news_df.columns else 0
        st.caption(f"기사 {len(news_df)}건 · 출처 {unique_sources}개")

    for _, row in news_df.head(12).iterrows():
        published = row.get("publishedDate")
        ts = published.strftime("%m-%d %H:%M") if isinstance(published, pd.Timestamp) else ""
        category = row.get("category", "기타")
        icon = CATEGORY_ICON.get(category, "📰")
        st.markdown(
            f"- {icon} [{row.get('title', '제목 없음')}]({row.get('url', '#')}) "
            f"`{category}` ({row.get('site', '출처 미상')} · {ts})"
        )

    st.markdown("---")

    available_categories = [c for c in CATEGORY_ORDER if (news_df["category"] == c).any()]
    tab_labels = [f"{CATEGORY_ICON.get(c, '📰')} {c} ({(news_df['category'] == c).sum()})" for c in available_categories]
    tabs = st.tabs(tab_labels)

    for tab, category in zip(tabs, available_categories):
        with tab:
            category_df = news_df[news_df["category"] == category]
            for _, row in category_df.iterrows():
                published = row.get("publishedDate")
                timestamp = published.strftime("%Y-%m-%d %H:%M") if isinstance(published, pd.Timestamp) else ""
                summary = _truncate_text(row.get("summary") or row.get("text", ""), 280)
                symbol = row.get("symbol", "")

                with st.container(border=True):
                    st.markdown(f"#### [{row.get('title', '제목 없음')}]({row.get('url', '#')})")
                    st.caption(f"{row.get('site', '출처 미상')} · {timestamp} · {symbol}")
                    if summary:
                        st.write(summary)

    if source == "sample":
        st.caption("샘플 뉴스가 사용되었습니다.")


def main():
    st.title("🇺🇸 미국 증시 섹터 데시보드")
    st.write(
        "섹터별 변동률, 대표 ETF 분석, 최신 뉴스를 한 화면에서 확인하고 "
        "간단한 인사이트를 얻을 수 있는 대시보드입니다."
    )

    st.sidebar.header("설정")
    # FMP API Key input removed as we use yfinance (free)
    
    news_limit = st.sidebar.slider("뉴스 기사 수", min_value=5, max_value=50, value=15, step=5)
    news_mode = st.sidebar.radio(
        "뉴스 범위",
        options=["혼합(추천)", "선택 섹터 중심", "시장 전체"],
        index=0,
    )
    st.sidebar.markdown("---")

    render_market_overview()

    sector_df = render_sector_performance()
    if sector_df is not None and not sector_df.empty:
        sector_names = sector_df["sector"].unique().tolist()
        st.sidebar.subheader("뉴스 필터")
        selected_sectors = st.sidebar.multiselect(
            "뉴스에 반영할 섹터 선택",
            options=sector_names,
            default=sector_names[:5],
        )
    else:
        selected_sectors = []

    render_sector_etfs()

    sector_tickers = [_sector_to_ticker(sector) for sector in selected_sectors]
    sector_tickers = [ticker for ticker in sector_tickers if ticker]
    market_tickers = ["SPY", "QQQ", "DIA", "IWM", "XLK", "XLF", "XLE", "XLV"]

    if news_mode == "선택 섹터 중심":
        news_tickers = sector_tickers or ["SPY", "QQQ"]
        include_general = False
    elif news_mode == "시장 전체":
        news_tickers = market_tickers
        include_general = True
    else:  # 혼합(추천)
        news_tickers = list(dict.fromkeys(sector_tickers + market_tickers))
        include_general = True

    render_news_section(news_tickers, news_limit, include_general)

    st.caption(
        "데이터 출처: Yahoo Finance (무료, 15분 지연 시세). "
    )


if __name__ == "__main__":
    main()
