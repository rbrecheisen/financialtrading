import pandas as pd
import yfinance as yf
import mplfinance as mpl

TICKERS = {
    'equity': 'IWDA.AS',
    'bond': 'AGGH.AS',
}


class Df:
    def __init__(self, df):
        self._df = df

    def df(self):
        return self._df


class DailyDf(Df):
    def __init__(self, df):
        super(DailyDf, self).__init__(df)


class WeeklyDf(Df):
    def __init__(self, df):
        super(WeeklyDf, self).__init__(self.only_complete_weeks(df))

    @staticmethod
    def only_complete_weeks(df):
        today = pd.Timestamp.today(tz=df.index.tz)
        if df.index[-1].isocalendar().week == today.isocalendar().week and df.index[-1].year == today.year:
            return df.iloc[:-2]
        return df.iloc[:-1]


class Strategy:
    pass


class MyStrategy(Strategy):
    def __init__(self, weekly_df, daily_df):
        super(MyStrategy, self).__init__()
        self._weekly_df = weekly_df
        self._daily_df = daily_df

    def ok(self):
        return self._weekly_ok(self._weekly_df) and self._daily_ok(self._daily_df)
    
    def _weekly_ok(self, df):
        return True
    
    def _daily_ok(self, df):
        return True


class BackTester:
    def __init__(self, strategy, today=pd.Timestamp.today(tz=df.index.tz)):
        self._strategy = strategy

    def ok(self):
        return self._strategy.ok()


def get_last_complete_week(df):
    today = pd.Timestamp.today(tz=df.index.tz)
    if df.index[-1].isocalendar().week == today.isocalendar().week and df.index[-1].year == today.year:
        return df.iloc[-2]
    return df.iloc[-1]


def main():
    wk_df = WeeklyDf(yf.Ticker(TICKERS['equity']).history(period='1y', interval='1wk'))
    dy_df = DailyDf(yf.Ticker(TICKERS['equity']).history(period='1y', interval='1d'))
    tester = BackTester(MyStrategy(wk_df, dy_df))
    print(tester.ok())

if __name__ == '__main__':
    main()