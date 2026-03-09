import json
import time
import requests
import pandas as pd

BASE_URL = 'https://gateway.saxobank.com/sim/openapi'
CHARTS_URL = f'{BASE_URL}/chart/v3/charts'


def load_access_token():
    with open('tokeninfo.json', 'r') as f:
        data = json.load(f)
        return data['access_token']
    

def load_etf_symbols_and_uics():
    symbols_uics = []
    with open('etfs.json', 'r') as f:
        data = json.load(f)
        for item in data:
            symbols_uics.append((item['Symbol'], item['Uic']))
    return symbols_uics


def get_payload(uic, asset_type, access_token):
    params = {'Uic': uic, 'AssetType': asset_type, 'Horizon': 1440, 'Count': 365}
    result = requests.get(CHARTS_URL, headers={'Authorization': f'Bearer {access_token}'}, params=params)
    result.raise_for_status()
    payload = result.json()
    return payload


def convert_to_df(payload):
    df = pd.DataFrame(payload['Data'])
    df['Time'] = pd.to_datetime(df['Time'])
    df = df.set_index("Time").sort_index()
    return df


def update_df(df):
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()
    df["VolMA20"] = df["Volume"].rolling(20).mean()
    df["Prev20High"] = df["High"].shift(1).rolling(20).max()
    last = df.iloc[-1]
    return df, last


def get_rules(last):
    uptrend = (last["Close"] > last["SMA20"] > last["SMA50"] > last["SMA200"])
    breakout = last["Close"] > last["Prev20High"]
    volume_ok = last["Volume"] > 1.5 * last["VolMA20"]
    return uptrend, breakout, volume_ok


def main():
    access_token = load_access_token()
    symbols_uics = load_etf_symbols_and_uics()
    for symbol_uic in symbols_uics:
        payload = get_payload(symbol_uic[1], 'Etf', access_token)
        df = convert_to_df(payload)
        df, last = update_df(df)
        uptrend, breakout, volume_ok = get_rules(last)
        if uptrend and breakout and volume_ok:
            print(f'Found candidate ETF symbol: {symbol_uic[0]}')
        else:
            print('.', end='', flush=True)
        time.sleep(0.5)


if __name__ == '__main__':
    main()