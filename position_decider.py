# Imports
from coin_decisions import decision
from kucoin_futures.client import Market
from datetime import datetime, timedelta


def choose_position(trading_pair, positive_bounce_range, negative_bounce_range, *arg):
    # Parameters
    change_period = 0
    last_close = 0
    bounce_continuation = False
    trend_interval = 1440
    candle_interval = 60
    skipped = False

    # Setting up client
    market_client = Market(url='https://api-futures.kucoin.com')

    # Fetching data

    # Starting from when position was opened
    if len(arg) > 0:
        seconds = arg[0]

        # Setting initial position
        current_position = arg[1]
        initial_position = current_position

        candle_data = market_client.get_kline_data(trading_pair, candle_interval, seconds)

    else:
        current_date = datetime.today() - timedelta(minutes=trend_interval)
        current_date = current_date.strftime("%d.%m.%Y %H:%M:%S")
        current_date = datetime.strptime(current_date, '%d.%m.%Y %H:%M:%S')
        seconds = int(current_date.timestamp() * 1000)

        candle_data = market_client.get_kline_data(trading_pair, candle_interval, seconds)

        opening_price = candle_data[0][1]
        closing_price = candle_data[0][4]
        change = ((closing_price - opening_price) / opening_price) * 100

        if change > 0:
            current_position = 'buy'
            initial_position = current_position
        elif change <= 0:
            current_position = 'sell'
            initial_position = current_position

    # Simulate position change
    for data in candle_data:
        if current_position == 'buy':
            bounce_range = positive_bounce_range
        else:
            bounce_range = negative_bounce_range

        # Setting price data
        open_price = data[1]
        close_price = data[4]

        # Calculate percentage
        change = ((close_price - open_price) / open_price) * 100

        # Simulate decision
        decisions = decision(current_position, close_price, change, bounce_range, change_period, last_close,
                             bounce_continuation)
        change_period = decisions[0]
        last_close = decisions[1]
        position_change = decisions[2]
        bounce_continuation = decisions[3]

        if position_change is not None:
            if current_position != position_change:
                current_position = position_change
                change_period = 0
                last_close = 0
                bounce_continuation = False

        # Skipping second candle for chance
        if bounce_range == 0:
            if initial_position == 'buy' and change < 0:
                if skipped is False:
                    skipped = True
                    position_change = None
                    current_position = initial_position
            elif initial_position == 'sell' and change > 0:
                if skipped is False:
                    skipped = True
                    position_change = None
                    current_position = initial_position

    position_change = current_position
    return position_change
