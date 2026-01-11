"""
Stock screening utilities for finding high-growth potential stocks.
"""

import yfinance as yf
from typing import List, Dict, Any
import pandas as pd


# S&P 500 대표 종목 리스트 (실제로는 전체 500개를 사용해야 하지만, 시작은 주요 종목으로)
SP500_SAMPLE = [
    # Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "CRM", "ADBE",
    # Finance
    "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "AXP", "BLK", "SCHW",
    # Healthcare
    "JNJ", "UNH", "PFE", "LLY", "ABBV", "TMO", "ABT", "DHR", "MRK", "BMY",
    # Consumer
    "WMT", "PG", "KO", "PEP", "COST", "NKE", "MCD", "SBUX", "HD", "TGT",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL",
    # Industrial
    "BA", "CAT", "UPS", "HON", "UNP", "LMT", "RTX", "DE", "MMM", "GE",
    # Other
    "DIS", "NFLX", "CMCSA", "VZ", "T", "INTC", "CSCO", "ORCL", "IBM", "QCOM"
]


def get_stock_universe(min_market_cap: float = 200e6, max_market_cap: float = 5e9) -> List[str]:
    """
    Get list of stocks to screen based on market cap criteria.
    
    Args:
        min_market_cap: Minimum market cap in dollars
        max_market_cap: Maximum market cap in dollars
        
    Returns:
        List of ticker symbols
    """
    # For now, return sample tickers
    # In production, this would query all stocks and filter by market cap
    return SP500_SAMPLE


def fetch_stock_data(ticker: str) -> Dict[str, Any]:
    """
    Fetch comprehensive stock data for screening.
    
    Returns dict with:
        - basic_info: price, market_cap, etc.
        - financials: revenue, earnings, margins
        - valuation: P/E, P/B, PEG
        - growth: revenue_growth, earnings_growth
        - technical: price_change_6m, relative_strength
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get historical data for growth calculations
        hist = stock.history(period="2y")
        
        # Basic info
        current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        market_cap = info.get("marketCap", 0)
        
        # Financials
        revenue = info.get("totalRevenue", 0)
        trailing_eps = info.get("trailingEps", 0)
        forward_eps = info.get("forwardEps", 0)
        
        # Growth metrics
        revenue_growth = info.get("revenueGrowth", 0) * 100 if info.get("revenueGrowth") else 0
        earnings_growth = info.get("earningsGrowth", 0) * 100 if info.get("earningsGrowth") else 0
        
        # Valuation
        pe_ratio = info.get("trailingPE", 0)
        pb_ratio = info.get("priceToBook", 0)
        peg_ratio = info.get("pegRatio", 0)
        
        # Calculate PEG if not available
        if not peg_ratio and pe_ratio and earnings_growth and earnings_growth > 0:
            peg_ratio = pe_ratio / earnings_growth
        
        # Profitability
        roe = info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else 0
        profit_margin = info.get("profitMargins", 0) * 100 if info.get("profitMargins") else 0
        
        # Financial health
        debt_to_equity = info.get("debtToEquity", 0) / 100 if info.get("debtToEquity") else 0
        current_ratio = info.get("currentRatio", 0)
        
        # Technical/Momentum
        # Calculate 6-month price change
        if len(hist) >= 126:  # ~6 months of trading days
            price_6m_ago = hist['Close'].iloc[-126]
            price_change_6m = ((current_price - price_6m_ago) / price_6m_ago) * 100
        else:
            price_change_6m = 0
        
        # 52-week high/low
        fifty_two_week_high = info.get("fiftyTwoWeekHigh", current_price)
        fifty_two_week_low = info.get("fiftyTwoWeekLow", current_price)
        
        # Distance from 52-week high (momentum indicator)
        if fifty_two_week_high > 0:
            distance_from_high = ((current_price - fifty_two_week_high) / fifty_two_week_high) * 100
        else:
            distance_from_high = -100
        
        # Volume
        avg_volume = info.get("averageVolume", 0)
        
        # Institutional ownership
        institutional_ownership = info.get("heldPercentInstitutions", 0) * 100 if info.get("heldPercentInstitutions") else 0
        
        return {
            "ticker": ticker,
            "name": info.get("shortName", ticker),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            
            # Basic
            "price": current_price,
            "market_cap": market_cap,
            "avg_volume": avg_volume,
            
            # Growth
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            
            # Valuation
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "peg_ratio": peg_ratio,
            
            # Profitability
            "roe": roe,
            "profit_margin": profit_margin,
            
            # Financial Health
            "debt_to_equity": debt_to_equity,
            "current_ratio": current_ratio,
            
            # Momentum
            "price_change_6m": price_change_6m,
            "distance_from_52w_high": distance_from_high,
            "institutional_ownership": institutional_ownership,
            
            # Raw info for additional analysis
            "raw_info": info
        }
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None


def screen_stocks(
    tickers: List[str],
    min_revenue_growth: float = 0,
    min_earnings_growth: float = 0,
    max_peg_ratio: float = 10,
    min_roe: float = 0,
    max_debt_to_equity: float = 10
) -> pd.DataFrame:
    """
    Screen stocks based on criteria.
    
    Args:
        tickers: List of ticker symbols to screen
        min_revenue_growth: Minimum revenue growth % (YoY)
        min_earnings_growth: Minimum earnings growth %
        max_peg_ratio: Maximum PEG ratio
        min_roe: Minimum ROE %
        max_debt_to_equity: Maximum debt/equity ratio
        
    Returns:
        DataFrame with screened stocks and their metrics
    """
    results = []
    
    for ticker in tickers:
        data = fetch_stock_data(ticker)
        if data and data["market_cap"] > 0:
            # Apply filters
            if (data["revenue_growth"] >= min_revenue_growth and
                data["earnings_growth"] >= min_earnings_growth and
                (data["peg_ratio"] <= max_peg_ratio if data["peg_ratio"] > 0 else True) and
                data["roe"] >= min_roe and
                data["debt_to_equity"] <= max_debt_to_equity):
                
                results.append(data)
    
    if not results:
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    return df


def get_sector_list() -> List[str]:
    """Get unique list of sectors for filtering."""
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
