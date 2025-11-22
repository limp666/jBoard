"""Offline sample data used when APIs are unavailable."""

SECTOR_PERFORMANCE = [
    {"sector": "Energy", "changesPercentage": "1.32%"},
    {"sector": "Materials", "changesPercentage": "0.87%"},
    {"sector": "Industrials", "changesPercentage": "-0.24%"},
    {"sector": "Consumer Discretionary", "changesPercentage": "0.65%"},
    {"sector": "Consumer Staples", "changesPercentage": "-0.12%"},
    {"sector": "Health Care", "changesPercentage": "0.41%"},
    {"sector": "Financials", "changesPercentage": "0.73%"},
    {"sector": "Technology", "changesPercentage": "1.85%"},
    {"sector": "Communication Services", "changesPercentage": "1.08%"},
    {"sector": "Utilities", "changesPercentage": "-0.44%"},
    {"sector": "Real Estate", "changesPercentage": "0.19%"},
]

SECTOR_ETF_QUOTES = [
    {
        "symbol": "XLE",
        "name": "Energy Select Sector SPDR Fund",
        "price": 89.52,
        "changesPercentage": 1.34,
        "change": 1.18,
        "yearHigh": 92.46,
        "yearLow": 75.38,
        "volume": 18653245,
    },
    {
        "symbol": "XLK",
        "name": "Technology Select Sector SPDR Fund",
        "price": 208.14,
        "changesPercentage": 1.91,
        "change": 3.9,
        "yearHigh": 214.12,
        "yearLow": 142.11,
        "volume": 8905412,
    },
    {
        "symbol": "XLY",
        "name": "Consumer Discretionary Select Sector SPDR Fund",
        "price": 171.22,
        "changesPercentage": 0.68,
        "change": 1.16,
        "yearHigh": 176.9,
        "yearLow": 138.41,
        "volume": 5432211,
    },
]

MARKET_INDICES = [
    {
        "symbol": "^GSPC",
        "name": "S&P 500",
        "price": 5496.33,
        "changesPercentage": 0.34,
        "change": 18.6,
    },
    {
        "symbol": "^DJI",
        "name": "Dow Jones Industrial Average",
        "price": 39601.12,
        "changesPercentage": 0.21,
        "change": 81.83,
    },
    {
        "symbol": "^IXIC",
        "name": "NASDAQ Composite",
        "price": 17877.02,
        "changesPercentage": 0.92,
        "change": 163.52,
    },
]

NEWS_ITEMS = [
    {
        "symbol": "XLK",
        "publishedDate": "2024-06-14 09:15:00",
        "title": "Tech sector rallies as AI demand accelerates",
        "text": "Chipmakers and cloud stocks lead gains following upbeat earnings guidance driven by AI infrastructure spending.",
        "url": "https://example.com/news/tech-ai-demand",
        "image": "https://example.com/images/tech.jpg",
        "site": "MarketWatch (sample)",
        "summary": "AI-focused investments continue to lift the technology sector.",
    },
    {
        "symbol": "XLE",
        "publishedDate": "2024-06-14 08:35:00",
        "title": "Oil prices climb on supply concerns",
        "text": "Supply disruptions in major producing regions pushed crude prices higher, boosting energy shares.",
        "url": "https://example.com/news/oil-supply",
        "image": "https://example.com/images/oil.jpg",
        "site": "Reuters (sample)",
        "summary": "Crude supply tightness supports the energy sector.",
    },
    {
        "symbol": "XLF",
        "publishedDate": "2024-06-14 07:55:00",
        "title": "Bank stocks firm as yields rise",
        "text": "Financials advanced alongside Treasury yields, with major banks posting solid trading revenue.",
        "url": "https://example.com/news/bank-stocks",
        "image": "https://example.com/images/banks.jpg",
        "site": "Bloomberg (sample)",
        "summary": "Higher yields and trading revenue support financials.",
    },
]
