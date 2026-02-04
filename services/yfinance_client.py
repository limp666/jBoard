"""
Helper utilities for working with Yahoo Finance (yfinance) API.
Replaces the FMP client to provide free, reliable market data.
"""

import pandas as pd
import yfinance as yf
from typing import List, Dict, Any, Iterable

# Sector ETF Map (Same as before, but we use these tickers to get data)
SECTOR_ETF_MAP = {
    "Energy": "XLE",
    "Materials": "XLB",
    "Industrials": "XLI",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Health Care": "XLV",
    "Financials": "XLF",
    "Technology": "XLK",
    "Communication Services": "XLC",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
}

# Reverse map for looking up sector name by ticker
TICKER_TO_SECTOR = {v: k for k, v in SECTOR_ETF_MAP.items()}

def get_sector_performance() -> List[Dict[str, Any]]:
    """
    Return the latest sector performance based on Sector ETF changes.
    """
    tickers = list(SECTOR_ETF_MAP.values())
    # threads=False to avoid 'database is locked' errors in Streamlit Cloud
    data = yf.download(tickers, period="1d", progress=False, threads=False)
    
    # yfinance returns a MultiIndex DataFrame if multiple tickers.
    # We want the percent change of the 'Close' price vs 'Open' or previous close.
    # Actually, for "1d" period, we can calculate change from the latest data.
    # Or simpler: use Ticker object info for real-time-ish change.
    
    # Using Tickers object is often cleaner for current stats
    result = []
    tickers_obj = yf.Tickers(" ".join(tickers))
    
    for ticker in tickers:
        try:
            info = tickers_obj.tickers[ticker].info
            # Calculate change %
            # currentPrice (or regularMarketPrice) vs previousClose
            current = info.get("currentPrice") or info.get("regularMarketPrice")
            prev_close = info.get("previousClose")
            
            change_pct = 0.0
            if current and prev_close:
                change_pct = ((current - prev_close) / prev_close) * 100
            
            sector_name = TICKER_TO_SECTOR.get(ticker, ticker)
            result.append({
                "sector": sector_name,
                "changesPercentage": change_pct
            })
        except Exception:
            continue
            
    return result

def get_sector_etf_quotes() -> List[Dict[str, Any]]:
    """
    Fetch snapshot quotes for the sector-tracking ETFs.
    """
    tickers = list(SECTOR_ETF_MAP.values())
    tickers_obj = yf.Tickers(" ".join(tickers))
    
    result = []
    for ticker in tickers:
        try:
            info = tickers_obj.tickers[ticker].info
            # Use regularMarketPrice as primary (currentPrice is often None)
            price = info.get("regularMarketPrice") or info.get("currentPrice")
            prev_close = info.get("previousClose")
            
            change = 0.0
            change_pct = 0.0
            if price and prev_close:
                change = price - prev_close
                change_pct = (change / prev_close) * 100
            
            result.append({
                "symbol": ticker,
                "name": info.get("shortName", ticker),
                "price": price,
                "changesPercentage": change_pct,
                "change": change,
                "yearHigh": info.get("fiftyTwoWeekHigh"),
                "yearLow": info.get("fiftyTwoWeekLow"),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
            })
        except Exception:
            continue
            
    return result

def get_market_indices(symbols: Iterable[str]) -> List[Dict[str, Any]]:
    """Fetch quote data for the supplied market index symbols."""
    # symbols like ^GSPC, ^DJI, ^IXIC
    tickers_obj = yf.Tickers(" ".join(symbols))
    
    result = []
    for ticker in symbols:
        try:
            info = tickers_obj.tickers[ticker].info
            # Indices sometimes have different field names or delayed data
            price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("ask") # Fallbacks
            prev_close = info.get("previousClose")
            
            change = 0.0
            change_pct = 0.0
            if price and prev_close:
                change = price - prev_close
                change_pct = (change / prev_close) * 100
                
            result.append({
                "symbol": ticker,
                "name": info.get("shortName", ticker),
                "price": price,
                "change": change,
                "changesPercentage": change_pct
            })
        except Exception:
            continue
            
    return result

def get_news(tickers: Iterable[str], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch recent news for the given tickers.
    """
    # yfinance news is per ticker. We can fetch for one or aggregate.
    # If tickers list is provided, we fetch news for the first few or all and merge.
    
    all_news = []
    seen_links = set()
    
    # If no tickers, default to SPY/QQQ for general market news
    target_tickers = list(tickers) if tickers else ["SPY", "QQQ"]
    
    # Limit to first 5 tickers to balance speed and variety
    # If we have very few results, we might want to try more, but start with 5.
    search_tickers = target_tickers[:5]
    
    for ticker in search_tickers:
        try:
            yf_ticker = yf.Ticker(ticker)
            news_items = yf_ticker.news
            
            for item in news_items:
                # Handle nested 'content' structure
                data = item.get("content", item)
                
                title = data.get("title")
                if not title:
                    continue
                    
                # Deduplication by title
                if title in seen_links:
                    continue
                seen_links.add(title)
                
                # URL extraction
                url = data.get("link")
                if not url and "clickThroughUrl" in data:
                    url = data["clickThroughUrl"].get("url")
                if not url and "canonicalUrl" in data:
                    url = data["canonicalUrl"].get("url")
                    
                # Site/Publisher
                site = data.get("publisher")
                if not site and "provider" in data:
                    site = data["provider"].get("displayName")
                    
                # Date
                pub_date = data.get("providerPublishTime")
                if not pub_date and "pubDate" in data:
                    pub_date = data["pubDate"]
                
                # Summary
                summary = data.get("summary") or data.get("description")
                
                # Thumbnail
                thumbnail_url = None
                if "thumbnail" in data:
                    thumbs = data["thumbnail"].get("resolutions")
                    if thumbs and isinstance(thumbs, list) and len(thumbs) > 0:
                        thumbnail_url = thumbs[-1].get("url")
                    elif "originalUrl" in data["thumbnail"]:
                        thumbnail_url = data["thumbnail"]["originalUrl"]

                all_news.append({
                    "symbol": ticker,
                    "title": title,
                    "url": url,
                    "site": site or "Yahoo Finance",
                    "publishedDate": pd.to_datetime(pub_date) if pub_date else pd.Timestamp.now(),
                    "summary": summary or "",
                    "thumbnail": thumbnail_url
                })
        except Exception:
            continue
            
    # Fallback: If no news found, try Market Indices
    if not all_news:
        try:
            for idx in ["^GSPC", "^IXIC"]:
                idx_ticker = yf.Ticker(idx)
                for item in idx_ticker.news:
                    data = item.get("content", item)
                    title = data.get("title")
                    if title and title not in seen_links:
                        seen_links.add(title)
                        # ... (Simplified extraction for fallback)
                        all_news.append({
                            "symbol": idx,
                            "title": title,
                            "url": data.get("link"),
                            "site": "Market News",
                            "publishedDate": pd.Timestamp.now(), # Approximate
                            "summary": data.get("summary", ""),
                            "thumbnail": None
                        })
        except Exception:
            pass

    # Sort by date desc
    all_news.sort(key=lambda x: x["publishedDate"], reverse=True)
    return all_news[:limit]


def get_stock_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Fetch historical OHLCV data for a ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        return df
    except Exception:
        return pd.DataFrame()


def get_stock_info(ticker: str) -> Dict[str, Any]:
    """
    Fetch basic profile info for a ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        return stock.info
    except Exception:
        return {}


def get_stock_financials(ticker: str) -> Dict[str, pd.DataFrame]:
    """
    Fetch comprehensive financial statements for advanced analysis.
    Uses new yfinance API methods for reliable data fetching.
    
    Returns:
        Dictionary with keys:
        - 'quarterly_income': Quarterly income statement
        - 'annual_income': Annual income statement
        - 'quarterly_balance': Quarterly balance sheet
        - 'annual_balance': Annual balance sheet
        - 'quarterly_cashflow': Quarterly cash flow statement
        - 'annual_cashflow': Annual cash flow statement
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Use new API methods (not deprecated attributes)
        return {
            'quarterly_income': stock.get_financials(freq='quarterly'),
            'annual_income': stock.get_financials(freq='yearly'),
            'quarterly_balance': stock.get_balance_sheet(freq='quarterly'),
            'annual_balance': stock.get_balance_sheet(freq='yearly'),
            'quarterly_cashflow': stock.get_cash_flow(freq='quarterly'),
            'annual_cashflow': stock.get_cash_flow(freq='yearly')
        }
    except Exception as e:
        print(f"Error fetching financials for {ticker}: {e}")
        return {
            'quarterly_income': pd.DataFrame(),
            'annual_income': pd.DataFrame(),
            'quarterly_balance': pd.DataFrame(),
            'annual_balance': pd.DataFrame(),
            'quarterly_cashflow': pd.DataFrame(),
            'annual_cashflow': pd.DataFrame()
        }


def calculate_advanced_metrics(info: Dict[str, Any], financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Calculate advanced/derived metrics from basic info and financials.
    
    Args:
        info: Basic stock info from get_stock_info()
        financials: Financial statements from get_stock_financials()
        
    Returns:
        Dictionary with calculated metrics
    """
    metrics = {}
    
    # Safe getters
    def safe_get(d, key, default=None):
        val = d.get(key, default)
        return val if val is not None else default
    
    # 1. Valuation Metrics
    trailing_pe = safe_get(info, 'trailingPE')
    forward_pe = safe_get(info, 'forwardPE')
    earnings_growth = safe_get(info, 'earningsGrowth')
    
    # PEG Ratio - Try multiple methods for better coverage
    peg_ratio = None
    
    # Method 1: Calculate from Trailing PER
    if trailing_pe and earnings_growth and earnings_growth > 0:
        peg_ratio = trailing_pe / (earnings_growth * 100)
    
    # Method 2: Calculate from Forward PER (if Method 1 failed)
    elif forward_pe and earnings_growth and earnings_growth > 0:
        peg_ratio = forward_pe / (earnings_growth * 100)
    
    # Method 3: Use pre-calculated value from yfinance
    elif safe_get(info, 'pegRatio'):
        peg_ratio = info['pegRatio']
    
    metrics['peg_ratio'] = peg_ratio
    
    # PSR (Price to Sales)
    metrics['price_to_sales'] = safe_get(info, 'priceToSalesTrailing12Months')
    
    # EV metrics
    metrics['ev_to_revenue'] = safe_get(info, 'enterpriseToRevenue')
    metrics['ev_to_ebitda'] = safe_get(info, 'enterpriseToEbitda')
    
    # FCF Yield
    fcf = safe_get(info, 'freeCashflow')
    market_cap = safe_get(info, 'marketCap')
    if fcf and market_cap and market_cap > 0:
        metrics['fcf_yield'] = (fcf / market_cap) * 100
    else:
        metrics['fcf_yield'] = None
    
    # 2. Financial Health
    total_cash = safe_get(info, 'totalCash', 0)
    total_debt = safe_get(info, 'totalDebt', 0)
    ebitda = safe_get(info, 'ebitda')
    
    # Net Debt
    net_debt = total_debt - total_cash
    metrics['net_debt'] = net_debt
    
    # Net Debt / EBITDA
    if ebitda and ebitda > 0:
        metrics['net_debt_to_ebitda'] = net_debt / ebitda
    else:
        metrics['net_debt_to_ebitda'] = None
    
    # Cash to Market Cap
    if market_cap and market_cap > 0:
        metrics['cash_to_market_cap'] = (total_cash / market_cap) * 100
    else:
        metrics['cash_to_market_cap'] = None
    
    # 3. Profitability
    metrics['roa'] = safe_get(info, 'returnOnAssets')
    metrics['roe'] = safe_get(info, 'returnOnEquity')
    metrics['gross_margins'] = safe_get(info, 'grossMargins')
    metrics['ebitda_margins'] = safe_get(info, 'ebitdaMargins')
    
    # FCF Margin
    total_revenue = safe_get(info, 'totalRevenue')
    if fcf and total_revenue and total_revenue > 0:
        metrics['fcf_margin'] = (fcf / total_revenue) * 100
    else:
        metrics['fcf_margin'] = None
    
    return metrics


def get_historical_metrics(financials: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Extract time-series metrics from financial statements for charting.
    
    Args:
        financials: Output from get_stock_financials()
        
    Returns:
        Dictionary with time-series DataFrames for various metrics
    """
    metrics = {}
    
    # Extract from annual income statement
    annual_income = financials.get('annual_income', pd.DataFrame())
    if not annual_income.empty:
        # Try to get key metrics (yfinance naming can vary)
        try:
            # Revenue
            if 'Total Revenue' in annual_income.index:
                metrics['revenue_annual'] = annual_income.loc['Total Revenue'].sort_index()
            
            # EBITDA
            if 'EBITDA' in annual_income.index:
                metrics['ebitda_annual'] = annual_income.loc['EBITDA'].sort_index()
            
            # Operating Income
            if 'Operating Income' in annual_income.index:
                metrics['operating_income_annual'] = annual_income.loc['Operating Income'].sort_index()
                
            # Net Income
            if 'Net Income' in annual_income.index:
                metrics['net_income_annual'] = annual_income.loc['Net Income'].sort_index()
        except Exception:
            pass
    
    # Extract from quarterly income statement
    quarterly_income = financials.get('quarterly_income', pd.DataFrame())
    if not quarterly_income.empty:
        try:
            if 'Total Revenue' in quarterly_income.index:
                metrics['revenue_quarterly'] = quarterly_income.loc['Total Revenue'].sort_index()
                
            if 'EBITDA' in quarterly_income.index:
                metrics['ebitda_quarterly'] = quarterly_income.loc['EBITDA'].sort_index()
        except Exception:
            pass
    
    # Extract from cash flow
    annual_cashflow = financials.get('annual_cashflow', pd.DataFrame())
    if not annual_cashflow.empty:
        try:
            if 'Free Cash Flow' in annual_cashflow.index:
                metrics['fcf_annual'] = annual_cashflow.loc['Free Cash Flow'].sort_index()
                
            if 'Operating Cash Flow' in annual_cashflow.index:
                metrics['operating_cf_annual'] = annual_cashflow.loc['Operating Cash Flow'].sort_index()
                
            if 'Capital Expenditure' in annual_cashflow.index:
                metrics['capex_annual'] = annual_cashflow.loc['Capital Expenditure'].sort_index()
                
            # Share buybacks
            if 'Repurchase Of Capital Stock' in annual_cashflow.index:
                metrics['buybacks_annual'] = annual_cashflow.loc['Repurchase Of Capital Stock'].sort_index()
        except Exception:
            pass
    
    # Extract from balance sheet
    annual_balance = financials.get('annual_balance', pd.DataFrame())
    if not annual_balance.empty:
        try:
            if 'Cash And Cash Equivalents' in annual_balance.index:
                metrics['cash_annual'] = annual_balance.loc['Cash And Cash Equivalents'].sort_index()
            elif 'Total Cash' in annual_balance.index:
                metrics['cash_annual'] = annual_balance.loc['Total Cash'].sort_index()
                
            if 'Total Debt' in annual_balance.index:
                metrics['total_debt_annual'] = annual_balance.loc['Total Debt'].sort_index()
                
            if 'Net Debt' in annual_balance.index:
                metrics['net_debt_annual'] = annual_balance.loc['Net Debt'].sort_index()
                
            if 'Total Assets' in annual_balance.index:
                metrics['total_assets_annual'] = annual_balance.loc['Total Assets'].sort_index()
        except Exception:
            pass
    #Extract from quarterly cash flow
    quarterly_cashflow = financials.get('quarterly_cashflow', pd.DataFrame())
    if not quarterly_cashflow.empty:
        try:
            if 'FreeCashFlow' in quarterly_cashflow.index:
                metrics['fcf_quarterly'] = quarterly_cashflow.loc['FreeCashFlow'].sort_index()
            elif 'Free Cash Flow' in quarterly_cashflow.index:
                metrics['fcf_quarterly'] = quarterly_cashflow.loc['Free Cash Flow'].sort_index()
                
            if 'OperatingCashFlow' in quarterly_cashflow.index:
                metrics['operating_cf_quarterly'] = quarterly_cashflow.loc['OperatingCashFlow'].sort_index()
            elif 'Operating Cash Flow' in quarterly_cashflow.index:
                metrics['operating_cf_quarterly'] = quarterly_cashflow.loc['Operating Cash Flow'].sort_index()
                
            if 'CapitalExpenditure' in quarterly_cashflow.index:
                metrics['capex_quarterly'] = quarterly_cashflow.loc['CapitalExpenditure'].sort_index()
            elif 'Capital Expenditure' in quarterly_cashflow.index:
                metrics['capex_quarterly'] = quarterly_cashflow.loc['Capital Expenditure'].sort_index()
        except Exception:
            pass
    
    # Extract from quarterly balance sheet
    quarterly_balance = financials.get('quarterly_balance', pd.DataFrame())
    if not quarterly_balance.empty:
        try:
            if 'CashAndCashEquivalents' in quarterly_balance.index:
                metrics['cash_quarterly'] = quarterly_balance.loc['CashAndCashEquivalents'].sort_index()
            elif 'Cash And Cash Equivalents' in quarterly_balance.index:
                metrics['cash_quarterly'] = quarterly_balance.loc['Cash And Cash Equivalents'].sort_index()
            elif 'Total Cash' in quarterly_balance.index:
                metrics['cash_quarterly'] = quarterly_balance.loc['Total Cash'].sort_index()
                
            if 'TotalDebt' in quarterly_balance.index:
                metrics['total_debt_quarterly'] = quarterly_balance.loc['TotalDebt'].sort_index()
            elif 'Total Debt' in quarterly_balance.index:
                metrics['total_debt_quarterly'] = quarterly_balance.loc['Total Debt'].sort_index()
                
            if 'TotalAssets' in quarterly_balance.index:
                metrics['total_assets_quarterly'] = quarterly_balance.loc['TotalAssets'].sort_index()
            elif 'Total Assets' in quarterly_balance.index:
                metrics['total_assets_quarterly'] = quarterly_balance.loc['Total Assets'].sort_index()
                
            if 'NetDebt' in quarterly_balance.index:
                metrics['net_debt_quarterly'] = quarterly_balance.loc['NetDebt'].sort_index()
            elif 'Net Debt' in quarterly_balance.index:
                metrics['net_debt_quarterly'] = quarterly_balance.loc['Net Debt'].sort_index()
        except Exception:
            pass
    
    return metrics
        
def search_symbols(query: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Search for symbols using Yahoo Finance Auto-complete API.
    """
    import requests
    
    if not query:
        return []
        
    # Switch to query1, sometimes more stable
    url = "https://query1.finance.yahoo.com/v1/finance/search"
    
    params = {
        "q": query,
        "quotesCount": limit,
        "newsCount": 0,
    }
    
    # Modern User-Agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=5)
        # Debug print
        print(f"[DEBUG] Search Status: {r.status_code}")
        
        data = r.json()
        
        results = []
        if "quotes" in data:
            for q in data["quotes"]:
                symbol = q.get("symbol")
                shortname = q.get("shortname", "")
                exch = q.get("exchange", "")
                type_disp = q.get("quoteType", "")
                
                # Exclude Option contracts or irrelevant stuff if needed
                # if type_disp == 'OPTION': continue
                
                results.append({
                    "symbol": symbol,
                    "name": shortname,
                    "exch": exch,
                    "type": type_disp,
                    "display": f"{shortname} ({symbol}) - {exch}" if shortname else f"{symbol} - {exch}"
                })
        else:
            print(f"[DEBUG] No 'quotes' in response: {data.keys()}")
            
        return results
    except Exception as e:
        print(f"Search API Error: {e}")
        return []


# ============================================================================
# SECTOR COMPARISON FUNCTIONS
# ============================================================================

# Curated list of top companies by market cap in each sector
# Using 5-10 representative stocks per sector for fast, meaningful comparison
SECTOR_PEERS = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "ORCL", "CSCO", "ADBE"],
    "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "TMO", "MRK", "LLY"],
    "Financials": ["JPM", "BAC", "WFC", "GS", "MS", "C", "BLK"],
    "Consumer Cyclical": ["AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX", "TGT"],
    "Communication Services": ["GOOGL", "META", "DIS", "NFLX", "CMCSA", "T", "VZ"],
    "Industrials": ["HON", "UNP", "CAT", "BA", "RTX", "LMT", "UPS"],
    "Consumer Defensive": ["PG", "KO", "PEP", "WMT", "COST", "MO", "CL"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC"],
    "Real Estate": ["PLD", "AMT", "EQIX", "PSA", "SPG", "O"],
    "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC"],
    "Basic Materials": ["LIN", "APD", "SHW", "ECL", "NEM", "FCX"],
}


def get_sector_peers(sector: str) -> List[str]:
    """
    Get list of peer company tickers for a given sector.
    
    Args:
        sector: Sector name (e.g., "Technology", "Healthcare")
        
    Returns:
        List of ticker symbols representing sector peers
    """
    # Try exact match first
    if sector in SECTOR_PEERS:
        return SECTOR_PEERS[sector]
    
    # Try case-insensitive match
    for key in SECTOR_PEERS:
        if key.lower() == sector.lower():
            return SECTOR_PEERS[key]
    
    # No match found
    return []


def calculate_sector_averages(sector: str) -> Dict[str, Any]:
    """
    Calculate sector median metrics from peer companies.
    
    Args:
        sector: Sector name (e.g., "Technology", "Healthcare")
        
    Returns:
        Dictionary with median values for key metrics:
        - trailing_pe: Price to Earnings (Trailing)
        - price_to_book: Price to Book Ratio
        - return_on_equity: Return on Equity (%)
        - return_on_assets: Return on Assets (%)
        - gross_margins: Gross Margin (%)
        - profit_margins: Net Profit Margin (%)
        - debt_to_equity: Debt to Equity Ratio
        - revenue_growth: Revenue Growth YoY (%)
        - earnings_growth: Earnings Growth YoY (%)
    """
    peers = get_sector_peers(sector)
    if not peers:
        print(f"[calculate_sector_averages] No peers found for sector: {sector}")
        return {}
    
    print(f"[calculate_sector_averages] Fetching data for {len(peers)} peers in {sector} sector...")
    
    # Fetch data for all peers
    metrics_list = []
    for ticker in peers:
        try:
            # Use yfinance directly for more reliability
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info or len(info) < 10:  # Basic sanity check
                print(f"  [WARN] Insufficient data for {ticker}")
                continue
                
            metrics_list.append({
                'trailing_pe': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'price_to_book': info.get('priceToBook'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                'return_on_equity': info.get('returnOnEquity'),
                'return_on_assets': info.get('returnOnAssets'),
                'gross_margins': info.get('grossMargins'),
                'operating_margins': info.get('operatingMargins'),
                'profit_margins': info.get('profitMargins'),
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
            })
            print(f"  [OK] {ticker} data fetched")
        except Exception as e:
            print(f"  [ERROR] Failed to fetch {ticker}: {e}")
            continue
    
    if not metrics_list:
        print(f"[calculate_sector_averages] No valid data collected for {sector}")
        return {}
    
    print(f"[calculate_sector_averages] Successfully collected data from {len(metrics_list)}/{len(peers)} peers")
    
    # Calculate median (more robust than mean for outliers)
    df = pd.DataFrame(metrics_list)
    medians = df.median()
    
    # Convert to regular dict with None for NaN values
    result = {}
    for key, value in medians.items():
        result[key] = None if pd.isna(value) else float(value)
    
    return result
