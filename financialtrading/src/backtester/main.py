import argparse
import yfinance as yf
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

COLUMNS = ['Open', 'High', 'Low', 'Close', 'Volume']


def load_price_data(ticker: str, today_str: str|None, years: int):
    if today_str:
        ref_date = datetime.strptime(today_str, '%Y-%m-%d')
    else:
        ref_date = datetime.today()
    start_date = ref_date - relativedelta(years=years)
    end_date = ref_date + timedelta(days=1)
    wk_df = yf.download(
        ticker,
        start=start_date.strftime('%Y-%m-%d'),
        end=end_date.strftime('%Y-%m-%d'),
        interval='1wk',
        auto_adjust=False,
        progress=False,
    )
    dy_df = yf.download(
        ticker,
        start=start_date.strftime('%Y-%m-%d'),
        end=end_date.strftime('%Y-%m-%d'),
        interval='1d',
        auto_adjust=False,
        progress=False,
    )
    if hasattr(wk_df.columns, 'nlevels') and wk_df.columns.nlevels > 1:
        wk_df.columns = wk_df.columns.get_level_values(0)
    if hasattr(dy_df.columns, 'nlevels') and dy_df.columns.nlevels > 1:
        dy_df.columns = dy_df.columns.get_level_values(0)
    wk_df = wk_df[COLUMNS].dropna()
    dy_df = dy_df[COLUMNS].dropna()
    return wk_df, dy_df, ref_date, start_date


def main():

    # Capture input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--ticker', 
        default='IWDA.AS',
        help='Name of ticker to download data for',
    )
    parser.add_argument(
        '--today', 
        default=None,
        help='Date of today (can be in past) in format yyyy-mm-dd',
    )
    parser.add_argument(
        '--years', 
        type=int, 
        default=1,
        help='How many years back from --today to show',
    )
    args = parser.parse_args()

    # Download weekly and daily price charts
    wk_df, dy_df, ref_date, start_date = load_price_data(args.ticker, args.today, args.years)

    # Calculate weekly EMA10 and EMA20
    wk_df['EMA10'] = wk_df['Close'].ewm(span=10, adjust=False).mean()
    wk_df['EMA20'] = wk_df['Close'].ewm(span=20, adjust=False).mean()    

    # Create two axes for plotting both the weekly and daily charts
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))

    # Add EMA10-20 to weekly plot
    wk_ema = [
        mpf.make_addplot(wk_df['EMA10'], ax=axes[0], label='EMA10', width=0.8),
        mpf.make_addplot(wk_df['EMA20'], ax=axes[0], label='EMA20', width=0.8, linestyle='--'),
    ]

    # Plot weekly chart
    mpf.plot(
        wk_df,
        type='candle',
        style='yahoo',
        ax=axes[0],
        addplot=wk_ema,
        volume=False,
        datetime_format='%Y-%m',
        xrotation=0,
    )
    axes[0].set_title(f'{args.ticker} - Weekly ({start_date.date()} to {ref_date.date()}) with EMA10/EMA20')
    axes[0].legend(loc='upper left')

    # Plot daily chart
    mpf.plot(
        dy_df,
        type='candle',
        style='yahoo',
        ax=axes[1],
        volume=False,
        datetime_format='%Y-%m',
        xrotation=0,
    )
    axes[1].set_title(f'{args.ticker} - Daily ({start_date.date()} to {ref_date.date()})')

    # Render everything
    plt.tight_layout()
    plt.show()    


if __name__ == '__main__':
    main()