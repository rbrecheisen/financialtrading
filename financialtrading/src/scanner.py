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
    

def load_etfs():
    with open('etfs.json', 'r') as f:
        data = json.load(f)
    return data


def load_stocks():
    with open('stocks.json', 'r') as f:
        data = json.load(f)
    return data


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


def update_df(df, ema_period=20, slope_lookback=5):
    df['EMA20'] = df['Close'].ewm(span=ema_period, adjust=False).mean()
    df['EMA20_slope_pct'] = (
        (df['EMA20'] - df['EMA20'].shift(slope_lookback))
        / df['EMA20'].shift(slope_lookback)
        * 100
    )
    last = df.iloc[-1]
    return df, last


def get_rules(last, min_slope_pct=2.0, price_range=(10, 100)):
    price_above_ema20 = last['Close'] > last['EMA20']
    ema20_slope_ok = last['EMA20_slope_pct'] > min_slope_pct
    within_price_range = price_range[0] < last['Close'] < price_range[1]
    candidate = price_above_ema20 and ema20_slope_ok and within_price_range
    return candidate


def main():

    access_token = load_access_token()

    print('Scanning ETFs...')
    candidate_etfs = []
    etfs = load_etfs()
    for etf in etfs:
        payload = get_payload(etf['Uic'], 'Etf', access_token)
        df = convert_to_df(payload)
        df, last = update_df(df)
        candidate = get_rules(last)
        if candidate:
            # print(json.dumps(etf, indent=2))
            symbol = etf['Symbol']
            description = etf['Description']
            candidate_etfs.append((description, symbol, last['Close']))
            print('X', end='', flush=True)
        else:
            print('.', end='', flush=True)
        time.sleep(0.5)
    print()

    print('Scanning stocks...')
    candidate_stocks = []
    stocks = load_stocks()
    for stock in stocks:
        payload = get_payload(stock['Uic'], 'Stock', access_token)
        df = convert_to_df(payload)
        df, last = update_df(df)
        candidate = get_rules(last)
        if candidate:
            symbol = stock['Symbol']
            description = stock['Description']
            candidate_stocks.append((description, symbol, last['Close']))
            print('X', end='', flush=True)
        else:
            print('.', end='', flush=True)
        time.sleep(0.5)

    section = 'Candidate ETFs found:'
    print()
    print(section)
    with open('candidate_etfs.txt', 'w') as f:
        f.write(section + '\n')
        for item in candidate_etfs:
            line = f' - {item[0]} ({item[1]}) at {item[2]}'
            f.write(line + '\n')
            print(line)

    section = 'Candidate stocks found:'
    print()
    print(section)
    with open('candidate_stocks.txt', 'w') as f:
        f.write(section + '\n')
        for item in candidate_stocks:
            line = f' - {item[0]} ({item[1]}) at {item[2]}'
            f.write(line + '\n')
            print(line)


if __name__ == '__main__':
    main()