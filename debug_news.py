import yfinance as yf
import json

try:
    for symbol in ["SPY", "QQQ"]:
        print(f"--- Fetching news for {symbol} ---")
        ticker = yf.Ticker(symbol)
        news = ticker.news
        print(f"Count: {len(news)}")
        # print(json.dumps(news, indent=2)) 
except Exception as e:
    print(f"Error: {e}")
