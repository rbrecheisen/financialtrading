import json
import pandas as pd
import yfinance as yf


class WeeklyTrendScanner:
    def __init__(self, period='2y', ema_period=20, slope_lookback=5, min_slope_pct=2.0):
        self._period = period
        self._ema_period = ema_period
        self._slope_lookback = slope_lookback
        self._min_slope_pct = min_slope_pct

    def load_symbols(self):
        symbols = []
        with open('etfs.json', 'r') as f:
            etfs = json.load(f)
            for etf in etfs:
                symbols.append(etf)
        with open('stocks.json', 'r') as f:
            stocks = json.load(f)
            for stock in stocks:
                symbols.append(stock)
        return symbols
    
    def run(self):
        symbols = self.load_symbols()
        rows = []
        for symbol in symbols:
            try:
                df = yf.download(
                    f'{symbol}.AS',
                    period=self._period,
                    interval='1wk',
                    auto_adjust=True,
                    progress=False,
                    multi_level_index=False,
                )
                if df.empty:
                    print(f'No data found for symbol {symbol}.AS')
                    continue
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                min_bars = self._ema_period + self._slope_lookback
                if len(df) < min_bars:
                    print(f'Not enough weekly bars for {symbol}.AS. Need at least {min_bars}')
                    continue
                df['EMA20'] = df['Close'].ewm(span=self._ema_period, adjust=False).mean()
                df['EMA20_slope_pct'] = (
                    (df['EMA20'] - df['EMA20'].shift(self._slope_lookback))
                    / df['EMA20'].shift(self._slope_lookback)
                    * 100
                )
                last = df.iloc[-1]
                price_above_ema20 = last['Close'] > last['EMA20']
                ema20_slope_ok = last['EMA20_slope_pct'] > self._min_slope_pct
                candidate = price_above_ema20 and ema20_slope_ok
                row = {
                    'symbol': symbol,
                    'date': str(df.index[-1].date()),
                    'close': round(float(last['Close']), 4),
                    'ema20': round(float(last['EMA20']), 4),
                    'ema20_slope_pct': round(float(last['EMA20_slope_pct']), 4),
                    'price_above_ema20': bool(price_above_ema20),
                    'ema20_slope_ok': bool(ema20_slope_ok),
                    'candidate': bool(candidate),
                }
                rows.append(row)
            except Exception:
                pass
        df_all = pd.DataFrame(rows)
        print(df_all)


if __name__ == '__main__':
    scanner = WeeklyTrendScanner()
    scanner.run()