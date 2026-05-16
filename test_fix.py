import sys
sys.path.insert(0, 'scripts')
from data_fetcher import TWStockDataFetcher

f = TWStockDataFetcher()

# Test 1: _get_last_trading_day
print('=== Test _get_last_trading_day ===')
for d in ['20260515', '20260516', '20260517', '20260518']:
    print('  %s -> %s' % (d, f._get_last_trading_day(d)))

# Test 2: _yf_price (quick check with 2 days)
print('\n=== Test _yf_price ===')
df = f._yf_price('2317', days=2)
if not df.empty:
    last = df.iloc[-1]
    print('  2317 Close=%s, Date=%s' % (last.get('Close'), df.index[-1]))
else:
    print('  2317 empty')
