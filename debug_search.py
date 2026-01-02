from services import yfinance_client
import time

print("Testing search for 'apple'...")
results = yfinance_client.search_symbols("apple")
print(f"Results: {results}")

print("\nTesting search for 'Samsung'...")
results_kr = yfinance_client.search_symbols("Samsung")
print(f"Results: {results_kr}")
