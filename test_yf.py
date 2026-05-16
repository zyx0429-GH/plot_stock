import yfinance as yf
import pandas as pd

for sid in ["2317", "2327", "2449", "3661"]:
    print(f"\n=== {sid} ===")
    for suffix in [".TW", ".TWO"]:
        try:
            ticker = yf.Ticker(f"{sid}{suffix}")
            df = ticker.history(period="5d")
            if not df.empty:
                latest = df.iloc[-1]
                print(f"  {suffix}: Close={latest.get('Close','N/A')}, Open={latest.get('Open','N/A')}, Volume={latest.get('Volume','N/A')}, Date={df.index[-1]}")
                # Check if auto_adjust might be affecting
                if 'Adj Close' in df.columns:
                    print(f"  Adj Close={latest.get('Adj Close','N/A')}")
            else:
                print(f"  {suffix}: empty")
        except Exception as e:
            print(f"  {suffix}: ERROR {e}")
