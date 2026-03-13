import os
import time
import requests
import json
import pandas as pd
from pathlib import Path

DATA_DIR = str(Path(__file__).resolve().parent)
DATA_ETFS_FILE = os.path.join(DATA_DIR, 'data/etfs.json')
DATA_ETFS_XLSX_FILE = os.path.join(DATA_DIR, 'data/etfs.xlsx')
DATA_STOCKS_FILE = os.path.join(DATA_DIR, 'data/stocks.json')
DATA_STOCKS_XLSX_FILE = os.path.join(DATA_DIR, 'data/stocks.xlsx')
DATA_TOKENINFO_FILE = os.path.join(DATA_DIR, 'data/tokeninfo.json')
DATA_CANDIDATE_ETFS_FILE = os.path.join(DATA_DIR, 'data/candidate_etfs.xlsx')
DATA_CANDIDATE_STOCKS_FILE = os.path.join(DATA_DIR, 'data/candidate_stocks.xlsx')
BASE_URL = 'https://gateway.saxobank.com/sim/openapi'
CHARTS_URL = f'{BASE_URL}/chart/v3/charts'


class Scanner:
    def __init__(self, ema_period=20, slope_lookback=5, min_slope_pct=2.0, price_range=(10, 100)):
        self._ema_period = ema_period
        self._slope_lookback = slope_lookback
        self._min_slope_pct = min_slope_pct
        self._price_range = price_range
        self._access_token = self.load_access_token()
        self._etfs = self.load_etfs()
        self._stocks = self.load_stocks()

    def load_access_token(self):
        with open(DATA_TOKENINFO_FILE, 'r') as f:
            data = json.load(f)
            return data['access_token']
        
    def load_etfs(self):
        with open(DATA_ETFS_FILE, 'r') as f:
            data = json.load(f)
        return data

    def load_stocks(self):
        with open(DATA_STOCKS_FILE, 'r') as f:
            data = json.load(f)
        return data
    
    def get_payload(self, uic, asset_type, access_token):
        params = {'Uic': uic, 'AssetType': asset_type, 'Horizon': 1440, 'Count': 365}
        result = requests.get(CHARTS_URL, headers={'Authorization': f'Bearer {access_token}'}, params=params)
        result.raise_for_status()
        payload = result.json()
        return payload

    def convert_to_df(self, payload):
        df = pd.DataFrame(payload['Data'])
        df['Time'] = pd.to_datetime(df['Time'])
        df = df.set_index("Time").sort_index()
        return df

    def update_df(self, df, ema_period, slope_lookback):
        df[f'EMA{ema_period}'] = df['Close'].ewm(span=ema_period, adjust=False).mean()
        df[f'EMA{ema_period}_slope_pct'] = (
            (df[f'EMA{ema_period}'] - df[f'EMA{ema_period}'].shift(slope_lookback))
            / df[f'EMA{ema_period}'].shift(slope_lookback)
            * 100
        )
        last = df.iloc[-1]
        return df, last

    def get_rules(self, last, ema_period, min_slope_pct, price_range):
        price_above_ema = last['Close'] > last[f'EMA{ema_period}']
        ema_slope_ok = last[f'EMA{ema_period}_slope_pct'] > min_slope_pct
        within_price_range = price_range[0] < last['Close'] < price_range[1]
        candidate = price_above_ema and ema_slope_ok and within_price_range
        return candidate, price_above_ema, ema_slope_ok, within_price_range

    def run(self):
        print(f'Search criteria: ema_period: {self._ema_period}, slope_lookback: {self._slope_lookback}, min_slop_pct: {self._min_slope_pct}, price_range: {self._price_range}')

        print('Searching ETFs...')
        rows_etfs = []
        for etf in self._etfs:
            symbol = etf['Symbol']
            description = etf['Description']
            payload = self.get_payload(etf['Uic'], 'Etf', self._access_token)
            df = self.convert_to_df(payload)
            df, last = self.update_df(df, self._ema_period, self._slope_lookback)
            candidate, price_above_ema, ema_slope_ok, within_price_range = self.get_rules(
                last, self._ema_period, self._min_slope_pct, self._price_range)
            if candidate:
                row = {
                    'description': description, 
                    'symbol': symbol, 
                    'last_close': last['Close'], 
                    'ema_slope_pct': last[f'EMA{self._ema_period}_slope_pct'],
                    'price_above_ema': price_above_ema,
                    'ema_slope_ok': ema_slope_ok,
                    'within_price_range': within_price_range,
                }
                rows_etfs.append(row)
                print(f'{description}: possible candidate')
            else:
                print(f'{description}')
            time.sleep(0.5)
        df_etfs = pd.DataFrame(rows_etfs)
        df_etfs.to_excel(DATA_CANDIDATE_ETFS_FILE, index=False)
        
        print('Searching stocks...')
        rows_stocks = []
        for stock in self._stocks:
            symbol = stock['Symbol']
            description = stock['Description']
            payload = self.get_payload(stock['Uic'], 'Stock', self._access_token)
            df = self.convert_to_df(payload)
            df, last = self.update_df(df, self._ema_period, self._slope_lookback)
            candidate, price_above_ema, ema_slope_ok, within_price_range = self.get_rules(
                last, self._ema_period, self._min_slope_pct, self._price_range)
            if candidate:
                row = {
                    'description': description, 
                    'symbol': symbol, 
                    'last_close': last['Close'], 
                    'ema_slope_pct': last[f'EMA{self._ema_period}_slope_pct'],
                    'price_above_ema': price_above_ema,
                    'ema_slope_ok': ema_slope_ok,
                    'within_price_range': within_price_range,
                }
                rows_stocks.append(row)
                print(f'{description}: possible candidate')
            else:
                print(f'{description}')
            time.sleep(0.5)
        df_stocks = pd.DataFrame(rows_stocks)
        df_stocks.to_excel(DATA_CANDIDATE_STOCKS_FILE, index=False)

        print('Done')
        return rows_etfs, rows_stocks