#!/usr/bin/env python3
"""Test script to diagnose yfinance API issues."""

import sys

print("Testing yfinance import...")
try:
    import yfinance as yf
    print("✓ yfinance imported successfully")
except ImportError as e:
    print(f"✗ Failed to import yfinance: {e}")
    sys.exit(1)

print("\n1. Testing market indices...")
try:
    indices = ["^GSPC", "^DJI", "^IXIC"]
    tickers_obj = yf.Tickers(" ".join(indices))
    
    for ticker in indices:
        try:
            info = tickers_obj.tickers[ticker].info
            price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("ask")
            name = info.get("shortName", ticker)
            print(f"  {ticker}: {name} - ${price}")
        except Exception as e:
            print(f"  {ticker}: Error - {e}")
except Exception as e:
    print(f"✗ Market indices test failed: {e}")

print("\n2. Testing sector ETFs...")
try:
    sector_etfs = ["XLE", "XLK", "XLF"]
    tickers_obj = yf.Tickers(" ".join(sector_etfs))
    
    for ticker in sector_etfs:
        try:
            info = tickers_obj.tickers[ticker].info
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            name = info.get("shortName", ticker)
            print(f"  {ticker}: {name} - ${price}")
        except Exception as e:
            print(f"  {ticker}: Error - {e}")
except Exception as e:
    print(f"✗ Sector ETF test failed: {e}")

print("\n3. Testing sector performance function...")
try:
    sys.path.insert(0, "/Users/jaykim/Documents/jBoard")
    from services import yfinance_client
    
    result = yfinance_client.get_sector_performance()
    print(f"  Returned {len(result)} sectors")
    if result:
        print(f"  Sample: {result[0]}")
    else:
        print(f"  ⚠ Empty result from get_sector_performance()")
except Exception as e:
    print(f"✗ Sector performance test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n4. Testing market indices function...")
try:
    result = yfinance_client.get_market_indices(["^GSPC", "^DJI", "^IXIC"])
    print(f"  Returned {len(result)} indices")
    if result:
        print(f"  Sample: {result[0]}")
    else:
        print(f"  ⚠ Empty result from get_market_indices()")
except Exception as e:
    print(f"✗ Market indices test failed: {e}")
    import traceback
    traceback.print_exc()

print("\nDone!")
