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
    data = yf.download(tickers, period="1d", progress=False)
    
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
            result.append({
                "symbol": ticker,
                "name": info.get("shortName", ticker),
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "changesPercentage": ((info.get("currentPrice", 0) - info.get("previousClose", 1)) / info.get("previousClose", 1)) * 100 if info.get("previousClose") else 0.0,
                "change": (info.get("currentPrice", 0) - info.get("previousClose", 0)) if info.get("currentPrice") and info.get("previousClose") else 0.0,
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
    
    # If no tickers, default to SPY for general market news
    target_tickers = list(tickers) if tickers else ["SPY"]
    
    # Limit to first 3 tickers to avoid too many requests if list is long
    for ticker in target_tickers[:3]:
        try:
            yf_ticker = yf.Ticker(ticker)
            news_items = yf_ticker.news
            
            for item in news_items:
                # Handle nested 'content' structure if present (common in newer yfinance versions)
                data = item.get("content", item)
                
                # Extract fields with fallbacks
                title = data.get("title")
                
                # URL can be in 'clickThroughUrl' -> 'url' or top level 'link'
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
                pub_date = data.get("providerPublishTime") # Timestamp
                if not pub_date and "pubDate" in data:
                    pub_date = data["pubDate"] # ISO string
                    
                # Summary
                summary = data.get("summary") or data.get("description")
                if not summary and "relatedTickers" in data:
                    summary = f"Related: {', '.join(data['relatedTickers'])}"
                
                # Thumbnail
                thumbnail_url = None
                if "thumbnail" in data:
                    thumbs = data["thumbnail"].get("resolutions")
                    if thumbs and isinstance(thumbs, list) and len(thumbs) > 0:
                        # Try to find a reasonable size, or just take the first/last
                        thumbnail_url = thumbs[-1].get("url") # Usually the largest or original
                    elif "originalUrl" in data["thumbnail"]:
                        thumbnail_url = data["thumbnail"]["originalUrl"]

                # Skip if no title or url
                if not title:
                    continue

                # Format to match app expectation
                all_news.append({
                    "symbol": ticker,
                    "title": title,
                    "url": url,
                    "site": site or "Yahoo Finance",
                    "publishedDate": pd.to_datetime(pub_date),
                    "summary": summary or "",
                    "thumbnail": thumbnail_url
                })
        except Exception:
            continue
            
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
