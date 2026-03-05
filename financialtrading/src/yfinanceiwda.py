import yfinance as yf
import pandas as pd

ticker = "IWDA.AS"

# Download daily OHLCV data
df = yf.download(
    ticker,
    start="2015-01-01",
    auto_adjust=True,   # adjusted prices (splits/dividends) folded into OHLC
    progress=False
)

# Basic cleanup / sanity checks
df = df.dropna()
df.index = pd.to_datetime(df.index)
df.to_csv('IWDA.AS.csv')

print(df.tail())
print("Rows:", len(df), "From:", df.index.min().date(), "To:", df.index.max().date())