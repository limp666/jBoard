"""
Stock screening utilities with multi-tier universe selection.
Tier 1: Curated growth stocks (~200)
Tier 2: Major indices by sector (~1,500)
Tier 3: Full market scan (~3,000+)
"""

import yfinance as yf
from typing import List, Dict, Any, Optional
import pandas as pd


# TIER 1: CURATED GROWTH STOCKS (~200)
CURATED_GROWTH_STOCKS = [
    # Technology - High Growth
    "PLTR", "SNOW", "CRWD", "ZS", "DDOG", "NET", "MDB", "OKTA", "TEAM", "SHOP",
    "SQ", "PYPL", "COIN", "RBLX", "U", "PATH", "DOCN", "FROG", "S", "TWLO",
    "ZM", "ASAN", "PD", "BILL", "WIX", "ROKU", "SPOT", "UBER", "LYFT", "DASH",
    "ABNB", "RIVN", "LCID", "CHPT", "BLNK", "STEM", "ENPH", "SEDG", "RUN",
    
    # Cybersecurity & Cloud
    "PANW", "FTNT", "CYBR", "TENB", "VRNS", "QLYS",
    
    # Semiconductors - Mid Cap
    "MRVL", "LRCX", "KLAC", "AMAT", "MU", "SWKS", "QRVO", "MCHP", "MPWR", "ON",
    
    # Software & SaaS
    "NOW", "WDAY", "VEEV", "ZI", "PAYC", "SMAR", "COUP", "HUB",
    
    # E-commerce & Digital
    "MELI", "SE", "ETSY", "W", "CHWY", "PINS", "SNAP",
    
    # FinTech
    "AFRM", "UPST", "SOFI", "LC", "NU", "HOOD",
    
    # Healthcare & Biotech
    "MRNA", "BNTX", "NVAX", "REGN", "VRTX", "ILMN", "EXAS", "TDOC", "DXCM",
    "ALGN", "ISRG", "IONS", "CRSP", "EDIT", "NTLA", "BEAM",
    
    # Clean Energy & EV
    "TSLA", "NIO", "XPEV", "LI", "PLUG", "FCEL", "BE", "QS",
    
    # Consumer Growth
    "LULU", "DECK", "CROX", "BYND",
    
    # Gaming & Entertainment
    "EA", "TTWO", "DKNG", "PENN",
    
    # Other Growth
    "Z", "RDFN", "OPEN", "BKNG"
]


# TIER 2: MAJOR INDEX CONSTITUENTS
# S&P indices provide good coverage of mid/small caps
MAJOR_INDICES = {
    "sp500": "^GSPC",
    "sp400": "^MID",  # S&P MidCap 400
    "sp600": "^SML",  # S&P SmallCap 600
    "nasdaq100": "^NDX",
    "russell2000": "^RUT"
}


def get_sp500_tickers() -> List[str]:
    """Get S&P 500 constituents from Wikipedia."""
    try:
        import requests
        from io import StringIO
        
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        sp500_table = tables[0]
        return sp500_table['Symbol'].str.replace('.', '-').tolist()
    except Exception as e:
        print(f"Warning: Could not fetch S&P 500 list: {e}")
        return []


def get_nasdaq100_tickers() -> List[str]:
    """Get NASDAQ 100 constituents."""
    try:
        import requests
        from io import StringIO
        
        url = "https://en.wikipedia.org/wiki/NASDAQ-100"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        nasdaq_table = tables[4]
        return nasdaq_table['Ticker'].tolist()
    except Exception as e:
        print(f"Warning: Could not fetch NASDAQ 100 list: {e}")
        return []


def get_index_based_universe(sector_filter: Optional[str] = None) -> List[str]:
    """
    Get stock universe from major indices.
    
    Args:
        sector_filter: Optional sector to filter (e.g., "Technology")
        
    Returns:
        List of tickers from S&P 500, NASDAQ 100, etc.
    """
    all_tickers = set()
    
    # Get S&P 500
    print("[DEBUG] Fetching S&P 500...")
    sp500 = get_sp500_tickers()
    print(f"[DEBUG] S&P 500 returned: {len(sp500)} stocks")
    all_tickers.update(sp500)
    
    # Get NASDAQ 100
    print("[DEBUG] Fetching NASDAQ 100...")
    nasdaq100 = get_nasdaq100_tickers()
    print(f"[DEBUG] NASDAQ 100 returned: {len(nasdaq100)} stocks")
    all_tickers.update(nasdaq100)
    
    # Add curated list
    print(f"[DEBUG] Adding curated list: {len(CURATED_GROWTH_STOCKS)} stocks")
    all_tickers.update(CURATED_GROWTH_STOCKS)
    
    tickers_list = list(all_tickers)
    print(f"[DEBUG] Total unique stocks: {len(tickers_list)}")
    
    # Filter by sector if specified
    if sector_filter:
        filtered = []
        print(f"Filtering by sector: {sector_filter}")
        for ticker in tickers_list:
            try:
                info = yf.Ticker(ticker).info
                if info.get("sector") == sector_filter:
                    filtered.append(ticker)
            except:
                continue
        return filtered
    
    return tickers_list


def get_full_market_scan() -> List[str]:
    """
    Get comprehensive list of all tradable US stocks.
    WARNING: This is SLOW (3,000+ tickers)
    
    Returns:
        List of all US stock tickers
    """
    # This would require a screener API or comprehensive ticker list
    # For now, combine all available sources
    all_tickers = set()
    
    # Add major indices
    all_tickers.update(get_index_based_universe())
    
    # TODO: Add Russell 2000, Russell 3000 if available
    # For full implementation, would need:
    # - FMP API screener
    # - NASDAQ/NYSE ticker lists
    # - Or paid data provider
    
    return list(all_tickers)


def get_stock_universe(
    mode: str = "curated",
    min_market_cap: float = 200e6,
    max_market_cap: float = 50e9,
    sector_filter: Optional[str] = None
) -> List[str]:
    """
    Get stock universe based on selected mode.
    
    Args:
        mode: "curated" | "index" | "full"
        min_market_cap: Minimum market cap filter
        max_market_cap: Maximum market cap filter
        sector_filter: Optional sector filter
        
    Returns:
        List of ticker symbols
    """
    if mode == "curated":
        print(f"📋 Using curated list ({len(CURATED_GROWTH_STOCKS)} stocks)")
        tickers = CURATED_GROWTH_STOCKS.copy()
        
    elif mode == "index":
        print("📊 Fetching major index constituents...")
        tickers = get_index_based_universe(sector_filter)
        print(f"Found {len(tickers)} stocks from indices")
        
    elif mode == "full":
        print("🌐 WARNING: Full market scan will take 30-60 minutes")
        tickers = get_full_market_scan()
        print(f"Found {len(tickers)} stocks for full scan")
        
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    # No market cap filtering for index/full modes
    return tickers


def fetch_stock_data(ticker: str) -> Dict[str, Any]:
    """
    Fetch comprehensive stock data for screening.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get historical data
        hist = stock.history(period="2y")
        
        # Basic info
        current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        market_cap = info.get("marketCap", 0)
        
        # Growth metrics
        revenue_growth = info.get("revenueGrowth", 0) * 100 if info.get("revenueGrowth") else 0
        earnings_growth = info.get("earningsGrowth", 0) * 100 if info.get("earningsGrowth") else 0
        
        # Valuation
        pe_ratio = info.get("trailingPE", 0)
        pb_ratio = info.get("priceToBook", 0)
        peg_ratio = info.get("pegRatio", 0)
        
        if not peg_ratio and pe_ratio and earnings_growth and earnings_growth > 0:
            peg_ratio = pe_ratio / earnings_growth
        
        # Profitability
        roe = info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else 0
        profit_margin = info.get("profitMargins", 0) * 100 if info.get("profitMargins") else 0
        
        # Financial health
        debt_to_equity = info.get("debtToEquity", 0) / 100 if info.get("debtToEquity") else 0
        current_ratio = info.get("currentRatio", 0)
        
        # Momentum
        if len(hist) >= 126:
            price_6m_ago = hist['Close'].iloc[-126]
            price_change_6m = ((current_price - price_6m_ago) / price_6m_ago) * 100
        else:
            price_change_6m = 0
        
        # 52-week metrics
        fifty_two_week_high = info.get("fiftyTwoWeekHigh", current_price)
        if fifty_two_week_high > 0:
            distance_from_high = ((current_price - fifty_two_week_high) / fifty_two_week_high) * 100
        else:
            distance_from_high = -100
        
        institutional_ownership = info.get("heldPercentInstitutions", 0) * 100 if info.get("heldPercentInstitutions") else 0
        
        return {
            "ticker": ticker,
            "name": info.get("shortName", ticker),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "price": current_price,
            "market_cap": market_cap,
            "avg_volume": info.get("averageVolume", 0),
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "peg_ratio": peg_ratio,
            "roe": roe,
            "profit_margin": profit_margin,
            "debt_to_equity": debt_to_equity,
            "current_ratio": current_ratio,
            "price_change_6m": price_change_6m,
            "distance_from_52w_high": distance_from_high,
            "institutional_ownership": institutional_ownership,
            "raw_info": info
        }
        
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


def screen_stocks(
    tickers: List[str],
    min_revenue_growth: float = 0,
    min_earnings_growth: float = 0,
    max_peg_ratio: float = 10,
    min_roe: float = 0,
    max_debt_to_equity: float = 10,
    progress_callback=None
) -> pd.DataFrame:
    """
    Screen stocks with optional progress callback.
    
    Args:
        tickers: List of tickers to screen
        ...filters...
        progress_callback: Optional function(current, total) for progress updates
        
    Returns:
        DataFrame with screened stocks
    """
    results = []
    total = len(tickers)
    
    for i, ticker in enumerate(tickers):
        if progress_callback:
            progress_callback(i + 1, total)
        
        data = fetch_stock_data(ticker)
        if data and data["market_cap"] > 0:
            if (data["revenue_growth"] >= min_revenue_growth and
                data["earnings_growth"] >= min_earnings_growth and
                (data["peg_ratio"] <= max_peg_ratio if data["peg_ratio"] > 0 else True) and
                data["roe"] >= min_roe and
                data["debt_to_equity"] <= max_debt_to_equity):
                
                results.append(data)
    
    return pd.DataFrame(results) if results else pd.DataFrame()


def get_sector_list() -> List[str]:
    """Get list of sectors."""
    return [
        "Technology",
        "Healthcare",
        "Financial Services",
        "Consumer Cyclical",
        "Consumer Defensive",
        "Industrials",
        "Energy",
        "Real Estate",
        "Basic Materials",
        "Utilities",
        "Communication Services"
    ]
