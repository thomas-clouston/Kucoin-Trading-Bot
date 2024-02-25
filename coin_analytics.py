# Imports
from kucoin_futures.client import Market
from datetime import datetime, timedelta
import math
import statistics
import time


def analyse_coin(trading_pair, *arg):
    # Parameters
    bounce_continuation = False
    first = True
    skip = False
    trend_interval = 1440
    candle_interval = 60
    trend_block = 12

    # Setup market client
    market_client = Market(url='https://api-futures.kucoin.com')

    # Lists
    trend_list = []
    bounce_list = []
    temp_candle_list = []
    positive_bounce_list = []
    negative_bounce_list = []

    # Converting week to milliseconds
    current_date = datetime.today() - timedelta(minutes=trend_interval)
    current_date = current_date.strftime("%d.%m.%Y %H:%M:%S")
    current_date = datetime.strptime(current_date, '%d.%m.%Y %H:%M:%S')
    seconds = int(current_date.timestamp() * 1000)

    candle_data = market_client.get_kline_data(trading_pair, candle_interval, seconds)

    if len(arg) > 0:
        current_position = arg[1]
        if current_position == 'buy':
            trend_2 = 'positive'
        else:
            trend_2 = 'negative'

        closing_trend_time2 = int(round(time.time() * 1000))

        seconds_2 = arg[0]

        if seconds_2 < seconds:
            candle_data = market_client.get_kline_data(trading_pair, candle_interval, seconds_2)
            trend_list.append(seconds_2)
            trend_list.append(closing_trend_time2)
            trend_list.append(trend_2)
            skip = True

    if skip is False:
        # Finding iteration to stop and add index
        remainder = len(candle_data) % trend_block
        if remainder == 0:
            end_number = len(candle_data) - trend_block
            end_digit = trend_block - 1
        else:
            end_number = len(candle_data) / trend_block
            end_number = math.floor(end_number) * trend_block
            end_digit = (len(candle_data) - end_number) - 1

        # Building trend data
        for iteration in range(0, len(candle_data), trend_block):
            if iteration == end_number:
                closing_trend_price = candle_data[iteration + end_digit][4]
                closing_trend_time = candle_data[iteration + end_digit][0]
            else:
                closing_trend_price = candle_data[iteration + trend_block][4]
                closing_trend_time = candle_data[iteration + trend_block][0]

            opening_trend_price = candle_data[iteration][1]
            opening_trend_time = candle_data[iteration][0]

            # Calculate trend percentages
            trend_change = ((closing_trend_price - opening_trend_price) / opening_trend_price) * 100

            # Finding trends
            if trend_change > 0:
                trend = 'positive'

            else:
                trend = 'negative'

            # Adding current position
            if len(arg) > 0:
                if seconds_2 < opening_trend_time:
                    if trend_2 == trend_list[-1]:
                        trend_list[-2] = closing_trend_time2
                    else:
                        trend_list[-2] = seconds_2
                        trend_list.append(seconds_2)
                        trend_list.append(closing_trend_time2)
                        trend_list.append(trend_2)
                    break

            # Compiling trends together
            if len(trend_list) == 0:
                trend_list = [opening_trend_time, closing_trend_time, trend]
            else:
                if trend == trend_list[-1]:
                    trend_list[-2] = closing_trend_time
                else:
                    trend_list.append(opening_trend_time)
                    trend_list.append(closing_trend_time)
                    trend_list.append(trend)

            if len(arg) > 0:
                if first is True:
                    first = False
                else:
                    if seconds_2 < trend_list[-2]:
                        if trend_2 != trend_list[-1]:
                            trend_list[-2] = seconds_2
                            trend_list.append(seconds_2)
                            trend_list.append(closing_trend_time2)
                            trend_list.append(trend_2)
                        break

    # Finding all candles times in trend interval
    for iteration_2 in range(0, len(trend_list), 3):
        for iteration_3 in candle_data:

            if iteration_3[0] in range(trend_list[iteration_2], trend_list[iteration_2 + 1]):
                open_price = iteration_3[1]
                close_price = iteration_3[4]

                # Calculate candle percentages
                candle_change = ((close_price - open_price) / open_price) * 100

                # Build list of candles against trend
                if trend_list[iteration_2 + 2] == 'positive':
                    if candle_change < 0:
                        bounce_continuation = True

                        if len(temp_candle_list) == 0:
                            temp_candle_list = [candle_change]
                            last_close = close_price

                        elif temp_candle_list[-1] < 0:  # If the last percent was also negative
                            if close_price <= last_close:
                                temp_candle_list.append(candle_change)
                                last_close = close_price

                            elif close_price > last_close:
                                temp_candle_list = [abs(number) for number in temp_candle_list]
                                bounce_list.append(sum(temp_candle_list))
                                temp_candle_list = [candle_change]
                                last_close = close_price

                    elif candle_change >= 0:
                        if len(temp_candle_list) != 0:
                            if bounce_continuation is True:
                                bounce_continuation = False
                            else:
                                temp_candle_list = [abs(number) for number in temp_candle_list]
                                bounce_list.append(sum(temp_candle_list))
                                temp_candle_list = []

                elif trend_list[iteration_2 + 2] == 'negative':
                    if candle_change > 0:
                        bounce_continuation = True

                        if len(temp_candle_list) == 0:
                            temp_candle_list = [candle_change]
                            last_close = close_price

                        elif temp_candle_list[-1] > 0:
                            if close_price >= last_close:
                                temp_candle_list.append(candle_change)
                                last_close = close_price

                            elif close_price < last_close:
                                bounce_list.append(sum(temp_candle_list))
                                temp_candle_list = [candle_change]
                                last_close = close_price

                    elif candle_change <= 0:
                        if len(temp_candle_list) != 0:
                            if bounce_continuation is True:
                                bounce_continuation = False
                            else:
                                bounce_list.append(sum(temp_candle_list))
                                temp_candle_list = []

        # Adding leftovers to bounce list
        if len(temp_candle_list) != 0:
            temp_candle_list = [abs(number) for number in temp_candle_list]
            bounce_list.append(sum(temp_candle_list))
            temp_candle_list = []

        # Sorting bounce list into two trends
        if trend_list[iteration_2 + 2] == 'positive':
            positive_bounce_list += bounce_list
        else:
            negative_bounce_list += bounce_list

        bounce_list = []

    # Calculating averages
    if len(positive_bounce_list) != 0:
        positive_bounce_range = statistics.mean(positive_bounce_list)
    else:
        positive_bounce_range = 0
    if len(negative_bounce_list) != 0:
        negative_bounce_range = statistics.mean(negative_bounce_list)
    else:
        negative_bounce_range = 0

    return positive_bounce_range, negative_bounce_range
