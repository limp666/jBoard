"""
Stock screening utilities with multi-tier universe selection.
Tier 1: Curated growth stocks (~200)
Tier 2: Major indices by sector (~500-1500)
Tier 3: Full market scan (~3,000+)
"""

import yfinance as yf
from typing import List, Dict, Any, Optional
import pandas as pd
import requests
from io import StringIO


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


# FALLBACK LISTS (for when Wikipedia is blocked, e.g., on Streamlit Cloud)
SP500_FALLBACK = [
    # Top holdings by market cap (covers ~80% of S&P 500 market cap)
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "BRK.B",
    "LLY", "AVGO", "JPM", "UNH", "V", "XOM", "WMT", "MA", "JNJ", "PG",
    "COST", "ORCL", "HD", "NFLX", "BAC", "ABBV", "CVX", "KO", "CRM", "MRK",
    "AMD", "ADBE", "PEP", "ACN", "LIN", "TMO", "MCD", "CSCO", "ABT", "DHR",
    "WFC", "GE", "INTU", "TXN", "VZ", "QCOM", "CMCSA", "PM", "IBM", "AMGN",
    "DIS", "ISRG", "AMAT", "HON", "CAT", "NEE", "SPGI", "UBER", "PFE", "SYK",
    "GS", "BKNG", "AXP", "LOW", "BSX", "T", "PGR", "DE", "TJX", "VRTX",
    "SBUX", "BLK", "ADP", "GILD", "MDT", "LMT", "C", "MMC", "ETN", "REGN",
    "CB", "ADI", "SCHW", "BX", "PLD", "TMUS", "ANET", "CVS", "MU", "SLB",
    "PANW", "FI", "AMT", "LRCX", "MDLZ", "SO", "BMY", "CI", "KLAC", "ICE",
    "SNPS", "EOG", "NOW", "WM", "MSI", "ZTS", "DUK", "EQIX", "APH", "CMG",
    "USB", "NOC", "PH", "ITW", "PNC", "APO", "CDNS", "SHW", "GD", "TT",
    "CL", "MCO", "TDG", "MMM", "CARR", "EMR", "AON", "FCX", "ROP", "WELL",
    "ORLY", "COF", "MAR", "HCA", "ECL", "GM", "CEG", "FDX", "AFL", "AJG",
    "NSC", "AIG", "PSA", "AZO", "MCHP", "TFC", "NXPI", "ADSK", "SRE", "TRV",
    "MPC", "FICO", "AMP", "PCAR", "NEM", "JCI", "HLT", "MET", "O", "PAYX",
    "AEP", "CPRT", "MNST", "ROST", "COR", "KMB", "ALL", "FTNT", "HUM", "FAST",
    "D", "CME", "DHI", "SPG", "KMI", "MSCI", "ODFL", "PRU", "CCI", "GWW",
    "TEL", "CTVA", "LHX", "YUM", "KVUE", "EA", "BK", "DD", "STZ", "KDP",
    "VMC", "RSG", "PCG", "CTAS", "VRSK", "URI", "EXC", "KR", "FIS", "GEHC",
    "GIS", "IT", "A", "F", "DXCM", "ACGL", "IDXX", "XEL", "HSY", "DAL",
    # Additional coverage from different sectors
    "NKE", "DOW", "MTD", "EW", "PWR", "RMD", "ON", "DVN", "GLW", "IR",
    "HWM", "CBRE", "AME", "EDR", "ANSS", "EFX", "BIIB", "MPWR", "DLR", "WAB",
    "MLM", "EXR", "VICI", "K", "CDW", "ROK", "AVB", "OKE", "HPQ", "TTWO",
    "EBAY", "FANG", "CHD", "TSCO", "DOV", "KEYS", "PPG", "XYL", "IQV", "EIX",
    "AXON", "HBAN", "MTB", "VTR", "RJF", "FTS", "ALGN", "TROW", "SBAC", "AWK",
    "SYY", "ETR", "WBD", "DFS", "INVH", "NTRS", "TYL", "GEN", "WY", "IP"
]

NASDAQ100_FALLBACK = [
    # Complete NASDAQ-100 major components
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "AVGO",
    "COST", "NFLX", "AMD", "ADBE", "PEP", "CSCO", "CMCSA", "INTC", "INTU",
    "TXN", "QCOM", "TMUS", "AMAT", "ISRG", "BKNG",  "AMGN", "HON", "VRTX",
    "ADP", "PANW", "GILD", "SBUX", "ADI", "MU", "LRCX", "MDLZ", "REGN",
    "KLAC", "SNPS", "MELI", "CDNS", "PYPL", "CRWD", "MAR", "ORLY", "MRVL",
    "CSX", "FTNT", "NXPI", "ADSK", "ABNB", "WDAY", "DASH", "ROP", "PCAR",
    "CPRT", "MNST", "ROST", "AEP", "ODFL", "PAYX", "FAST", "EA", "KDP",
    "CTAS", "VRSK", "DXCM", "IDXX", "KHC", "EXC", "XEL", "CTSH", "GEHC",
    "CCEP", "TEAM", "LULU", "ON", "CSGP", "ANSS", "TTWO", "ZS", "DDOG",
    "BIIB", "MRNA", "CDW", "ILMN", "WBD", "MDB", "GFS", "SMCI", "ARM"
]


def get_sp500_tickers() -> List[str]:
    """Get S&P 500 constituents from Wikipedia with improved error handling."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        sp500_table = tables[0]
        tickers = sp500_table['Symbol'].str.replace('.', '-', regex=False).tolist()
        print(f"✓ Successfully fetched {len(tickers)} S&P 500 tickers")
        return tickers
    except Exception as e:
        print(f"⚠️ Warning: Could not fetch S&P 500 list: {e}")
        print(f"→ Using fallback S&P 500 list ({len(SP500_FALLBACK)} tickers)")
        return SP500_FALLBACK


def get_nasdaq100_tickers() -> List[str]:
    """Get NASDAQ 100 constituents with improved error handling."""
    try:
        url = "https://en.wikipedia.org/wiki/NASDAQ-100"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        # NASDAQ-100 table is usually the 4th or 5th table
        for i, table in enumerate(tables):
            if 'Ticker' in table.columns or 'Symbol' in table.columns:
                ticker_col = 'Ticker' if 'Ticker' in table.columns else 'Symbol'
                tickers = table[ticker_col].tolist()
                # Filter out non-ticker entries
                tickers = [t for t in tickers if isinstance(t, str) and len(t) <= 5 and t.isupper()]
                if len(tickers) > 50:  # Sanity check
                    print(f"✓ Successfully fetched {len(tickers)} NASDAQ-100 tickers")
                    return tickers
        
        print("⚠️ Could not find NASDAQ-100 table in Wikipedia")
        print(f"→ Using fallback NASDAQ-100 list ({len(NASDAQ100_FALLBACK)} tickers)")
        return NASDAQ100_FALLBACK
    except Exception as e:
        print(f"⚠️ Warning: Could not fetch NASDAQ 100 list: {e}")
        print(f"→ Using fallback NASDAQ-100 list ({len(NASDAQ100_FALLBACK)} tickers)")
        return NASDAQ100_FALLBACK


def get_nasdaq_listed_tickers() -> List[str]:
    """
    Get comprehensive NASDAQ listed stocks from NASDAQ FTP server.
    This is the most reliable source for full market data.
    """
    try:
        print("📡 Fetching NASDAQ listed stocks from official FTP...")
        
        # NASDAQ provides official lists via FTP
        nasdaq_url = "ftp://ftp.nasdaqtrader.com/symboldirectory/nasdaqlisted.txt"
        other_url = "ftp://ftp.nasdaqtrader.com/symboldirectory/otherlisted.txt"
        
        all_tickers = set()
        
        # Get NASDAQ listed
        try:
            nasdaq_df = pd.read_csv(nasdaq_url, sep='|')
            nasdaq_tickers = nasdaq_df['Symbol'].dropna().tolist()
            # Filter out test symbols and special cases
            nasdaq_tickers = [t for t in nasdaq_tickers if not t.endswith('$') and len(t) <= 5]
            all_tickers.update(nasdaq_tickers)
            print(f"  ✓ NASDAQ listed: {len(nasdaq_tickers)} tickers")
        except Exception as e:
            print(f"  ⚠️ Could not fetch NASDAQ listed: {e}")
        
        # Get other exchanges (NYSE, AMEX, etc.)
        try:
            other_df = pd.read_csv(other_url, sep='|')
            # Filter for common exchanges
            other_df = other_df[other_df['Exchange'].isin(['N', 'A', 'P'])]  # NYSE, AMEX, ARCA
            other_tickers = other_df['ACT Symbol'].dropna().tolist()
            other_tickers = [t for t in other_tickers if not t.endswith('$') and len(t) <= 5]
            all_tickers.update(other_tickers)
            print(f"  ✓ Other exchanges: {len(other_tickers)} tickers")
        except Exception as e:
            print(f"  ⚠️ Could not fetch other exchanges: {e}")
        
        tickers_list = sorted(list(all_tickers))
        print(f"✓ Total NASDAQ FTP tickers: {len(tickers_list)}")
        return tickers_list
        
    except Exception as e:
        print(f"⚠️ Error fetching from NASDAQ FTP: {e}")
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
    print("📊 Fetching S&P 500...")
    sp500 = get_sp500_tickers()
    all_tickers.update(sp500)
    
    # Get NASDAQ 100
    print("📊 Fetching NASDAQ 100...")
    nasdaq100 = get_nasdaq100_tickers()
    all_tickers.update(nasdaq100)
    
    # Always include curated list
    print(f"📋 Adding curated growth stocks ({len(CURATED_GROWTH_STOCKS)})...")
    all_tickers.update(CURATED_GROWTH_STOCKS)
    
    tickers_list = sorted(list(all_tickers))
    print(f"✅ Total unique stocks: {len(tickers_list)}")
    
    # Note: Sector filtering is now done AFTER fetching basic data
    # to avoid making too many API calls upfront
    return tickers_list


def get_full_market_scan() -> List[str]:
    """
    Get comprehensive list of all tradable US stocks.
    Uses NASDAQ FTP server for official, complete data.
    WARNING: This returns 3,000+ tickers and will be SLOW to screen
    
    Returns:
        List of all US stock tickers
    """
    print("🌐 Initiating FULL MARKET SCAN...")
    print("⚠️  This will return 3,000+ tickers - screening will take 1-2 hours!")
    
    # Try NASDAQ FTP (most comprehensive)
    all_tickers = set()
    nasdaq_tickers = get_nasdaq_listed_tickers()
    
    if nasdaq_tickers:
        all_tickers.update(nasdaq_tickers)
    else:
        # Fallback: use index-based universe
        print("→ NASDAQ FTP failed, falling back to index-based universe")
        all_tickers.update(get_index_based_universe())
    
    tickers_list = sorted(list(all_tickers))
    print(f"✅ Full market: {len(tickers_list)} total tickers")
    
    return tickers_list


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
        min_market_cap: Minimum market cap filter (applied during screening, not here)
        max_market_cap: Maximum market cap filter (applied during screening, not here)
        sector_filter: Optional sector filter (applied during screening, not here)
        
    Returns:
        List of ticker symbols
    """
    if mode == "curated":
        print(f"📋 Using curated list ({len(CURATED_GROWTH_STOCKS)} stocks)")
        tickers = CURATED_GROWTH_STOCKS.copy()
        
    elif mode == "index":
        print("📊 Fetching major index constituents...")
        tickers = get_index_based_universe(sector_filter)
        print(f"→ Found {len(tickers)} stocks from indices")
        
    elif mode == "full":
        print("🌐 WARNING: Full market scan will take 1-2 hours")
        tickers = get_full_market_scan()
        print(f"→ Found {len(tickers)} stocks for full scan")
        
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    return tickers


def fetch_stock_data(ticker: str) -> Dict[str, Any]:
    """
    Fetch comprehensive stock data for screening.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Skip if no valid data
        if not info or 'symbol' not in info:
            return None
        
        # Get historical data
        hist = stock.history(period="2y")
        
        # Basic info
        current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        market_cap = info.get("marketCap", 0)
        
        # Skip penny stocks and invalid data
        if current_price < 1 or market_cap == 0:
            return None
        
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
        # Silently skip errors for individual stocks
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
        progress_callback: Optional function(current, total, ticker, company_name) for progress updates
        
    Returns:
        DataFrame with screened stocks
    """
    results = []
    total = len(tickers)
    
    for i, ticker in enumerate(tickers):
        # Fetch data first to get company name
        data = fetch_stock_data(ticker)
        
        # Update progress with ticker and company name info
        if progress_callback:
            company_name = data.get("name", ticker) if data else ticker
            progress_callback(i + 1, total, ticker, company_name)
        
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
