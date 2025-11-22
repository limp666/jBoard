import yfinance as yf
import json

try:
    ticker = yf.Ticker("AAPL")
    news = ticker.news
    print("Raw News Data:")
    print(json.dumps(news, indent=2))
except Exception as e:
    print(f"Error: {e}")
