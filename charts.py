import datetime
import time
import yfinance as yf
import plotly.graph_objects as go


def get_prices(tickers):
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=30)
    end_str = datetime.datetime.strftime(end, "%Y-%m-%d")
    start_str = datetime.datetime.strftime(start, "%Y-%m-%d")
    return yf.download(" ".join(tickers), start=start_str, end=end_str)


def plot_prices(tickers):
    # tickers = [t.strip() for t in tickers.split(",")]
    data = get_prices(tickers)

    if len(tickers) > 1:
        data = data.stack(level=0)

    figs = []

    for t in tickers:
        df = data

        if len(tickers) > 1:
            df = data[t]
            df = df.unstack()

        f = go.Figure(
            data=[
                go.Candlestick(
                    x=df.index,
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                )
            ]
        )

        f.update_layout(xaxis_rangeslider_visible=False)
        f.update_layout(title=f"{t} price chart", title_x=0.5)

        figs.append(f)

    return figs
