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
    result = []
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Calculate change %
            current = info.get("currentPrice") or info.get("regularMarketPrice")
            prev_close = info.get("previousClose")
            
            change_pct = 0.0
            if current and prev_close and prev_close != 0:
                change_pct = ((current - prev_close) / prev_close) * 100
            
            sector_name = TICKER_TO_SECTOR.get(ticker, ticker)
            result.append({
                "sector": sector_name,
                "changesPercentage": change_pct
            })
        except Exception:
            # Skip failed tickers
            continue
            
    return result

def get_sector_etf_quotes() -> List[Dict[str, Any]]:
    """
    Fetch snapshot quotes for the sector-tracking ETFs.
    """
    tickers = list(SECTOR_ETF_MAP.values())
    result = []
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            current = info.get("currentPrice") or info.get("regularMarketPrice")
            prev_close = info.get("previousClose", 1)
            
            change_pct = 0.0
            change_abs = 0.0
            if current and prev_close and prev_close != 0:
                change_abs = current - prev_close
                change_pct = (change_abs / prev_close) * 100
            
            result.append({
                "symbol": ticker,
                "name": info.get("shortName", ticker),
                "price": current,
                "changesPercentage": change_pct,
                "change": change_abs,
                "yearHigh": info.get("fiftyTwoWeekHigh"),
                "yearLow": info.get("fiftyTwoWeekLow"),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
            })
        except Exception:
            # Skip failed tickers
            continue
            
    return result

def get_market_indices(symbols: Iterable[str]) -> List[Dict[str, Any]]:
    """Fetch quote data for the supplied market index symbols."""
    result = []
    
    for ticker in symbols:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("ask")
            prev_close = info.get("previousClose")
            
            change = 0.0
            change_pct = 0.0
            if price and prev_close and prev_close != 0:
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
            # Skip failed indices
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
