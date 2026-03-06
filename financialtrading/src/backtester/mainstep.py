import argparse
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import yfinance as yf
import mplfinance as mpf
import matplotlib.pyplot as plt

COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def clean_df(df):
    if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(0)
    return df[COLUMNS].dropna().copy()


def load_daily_history(ticker: str, today_str: str | None, years: int, weeks: int):
    if today_str:
        ref_date = datetime.strptime(today_str, "%Y-%m-%d")
    else:
        ref_date = datetime.today()

    # Need enough daily history to support the weekly window as well
    start_date = ref_date - relativedelta(years=years) - timedelta(days=14)
    end_date = ref_date + timedelta(days=30)  # a bit of extra room for stepping forward

    df = yf.download(
        ticker,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        interval="1d",
        auto_adjust=False,
        progress=False,
    )
    df = clean_df(df)
    return df, ref_date


def build_visible_data(full_daily_df, ref_date: datetime, years: int, weeks: int):
    weekly_start = ref_date - relativedelta(years=years)
    daily_start = ref_date - timedelta(weeks=weeks)

    # daily end inclusive
    dy_df = full_daily_df.loc[
        (full_daily_df.index >= daily_start) & (full_daily_df.index <= ref_date)
    ].copy()

    wk_source = full_daily_df.loc[
        (full_daily_df.index >= weekly_start) & (full_daily_df.index <= ref_date)
    ].copy()

    # Build weekly candles from daily data
    wk_df = (
        wk_source.resample("W-FRI")
        .agg(
            {
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }
        )
        .dropna()
    )

    # Weekly EMAs
    wk_df["EMA10"] = wk_df["Close"].ewm(span=10, adjust=False).mean()
    wk_df["EMA20"] = wk_df["Close"].ewm(span=20, adjust=False).mean()

    # Project weekly EMAs onto daily dates
    dy_df["EMA10_WK"] = wk_df["EMA10"].reindex(dy_df.index, method="ffill")
    dy_df["EMA20_WK"] = wk_df["EMA20"].reindex(dy_df.index, method="ffill")

    return wk_df, dy_df, weekly_start, daily_start


def draw_charts(fig, axes, ticker, wk_df, dy_df, weekly_start, daily_start, ref_date):
    axes[0].clear()
    axes[1].clear()

    wk_ema = [
        mpf.make_addplot(wk_df["EMA10"], ax=axes[0], label="EMA10", width=0.8),
        mpf.make_addplot(
            wk_df["EMA20"], ax=axes[0], label="EMA20", width=0.8, linestyle="--"
        ),
    ]

    dy_ema = [
        mpf.make_addplot(
            dy_df["EMA10_WK"], ax=axes[1], label="Weekly EMA10", width=0.8
        ),
        mpf.make_addplot(
            dy_df["EMA20_WK"],
            ax=axes[1],
            label="Weekly EMA20",
            width=0.8,
            linestyle="--",
        ),
    ]

    my_style = mpf.make_mpf_style(
        base_mpf_style='yahoo',
        gridaxis='horizontal',   # only horizontal grid lines
        gridstyle=':',
    )

    mpf.plot(
        wk_df,
        type="candle",
        style=my_style,
        ax=axes[0],
        addplot=wk_ema,
        volume=False,
        datetime_format="%Y-%m",
        xrotation=0,
    )
    axes[0].grid(True, axis='y', linestyle=':', linewidth=0.6, alpha=0.6)   
    axes[0].set_title(f"{ticker} - Weekly ({weekly_start.date()} to {ref_date.date()})")
    axes[0].legend(loc="upper left")

    week_starts = dy_df.groupby(dy_df.index.to_period('W-MON')).apply(lambda x: x.index.min()).tolist()

    mpf.plot(
        dy_df,
        type="candle",
        style=my_style,
        ax=axes[1],
        addplot=dy_ema,
        volume=False,
        datetime_format="%Y-%m-%d",
        xrotation=15,
        vlines=dict(
            vlines=week_starts,
            linewidths=0.6,
            linestyle=':',
            alpha=0.4,
        ),
    )
    axes[1].grid(True, axis='y', linestyle=':', linewidth=0.6, alpha=0.6)
    axes[1].set_title(f"{ticker} - Daily ({daily_start.date()} to {ref_date.date()})")
    axes[1].legend(loc="upper left")

    fig.tight_layout()
    fig.canvas.draw_idle()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="IWDA.AS")
    parser.add_argument("--today", default=None, help="YYYY-MM-DD")
    parser.add_argument("--years", type=int, default=1)
    parser.add_argument("--weeks", type=int, default=4)
    args = parser.parse_args()

    full_daily_df, initial_ref_date = load_daily_history(
        args.ticker, args.today, args.years, args.weeks
    )

    state = {
        "ref_date": initial_ref_date,
    }

    fig, axes = plt.subplots(2, 1, figsize=(12, 10))

    def refresh():
        wk_df, dy_df, weekly_start, daily_start = build_visible_data(
            full_daily_df, state["ref_date"], args.years, args.weeks
        )
        draw_charts(
            fig,
            axes,
            args.ticker,
            wk_df,
            dy_df,
            weekly_start,
            daily_start,
            state["ref_date"],
        )

    def on_key(event):
        if event.key in ["right", "n"]:
            state["ref_date"] = state["ref_date"] + timedelta(days=1)
            refresh()
        elif event.key in ["left", "p"]:
            state["ref_date"] = state["ref_date"] - timedelta(days=1)
            refresh()

    refresh()
    fig.canvas.mpl_connect("key_press_event", on_key)
    plt.show()


if __name__ == "__main__":
    main()