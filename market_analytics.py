# Imports
from kucoin_futures.client import Market
from datetime import datetime, timedelta
import statistics


def analyse_market(*arg):
    count = 0

    # Setup market client
    market_client = Market(url='https://api-futures.kucoin.com')

    # Parameters
    trend_interval = 1440
    candle_interval = 60

    while True:
        try:
            # Lists
            best_pair = []
            averages_list = []
            trends_list = []

            # Converting week to milliseconds
            current_date = datetime.today() - timedelta(minutes=trend_interval)
            current_date = current_date.strftime("%d.%m.%Y %H:%M:%S")
            current_date = datetime.strptime(current_date, '%d.%m.%Y %H:%M:%S')
            seconds = int(current_date.timestamp() * 1000)

            # Finding all available trading pairs
            pairs = market_client.get_contracts_list()

            if len(arg) > 0:
                coin_exclude = arg[0]
            else:
                coin_exclude = None

            # Analysing market
            for index in pairs:
                trading_pair = index['symbol']
                if trading_pair != coin_exclude:
                    if trading_pair.endswith('USDTM'):
                        # Pulling candle data
                        candle_data = market_client.get_kline_data(trading_pair, candle_interval, seconds)
                        closing_price = candle_data[-1][4]
                        opening_price = candle_data[0][1]

                        trend = ((closing_price - opening_price) / opening_price) * 100
                        trends_list.append(abs(trend))
                        trends_list.append(trading_pair)

                        # Calculating gradient based on trend
                        gradient = (closing_price - opening_price) / 23

                        variance_list = []

                        # Calculating predicted values and variance
                        for data in enumerate(candle_data):
                            x = data[0]
                            price = data[1][4]
                            y = (gradient * x) + opening_price
                            variance = abs(((price - y) / y) * 100)
                            variance_list.append(variance)

                        average = statistics.mean(variance_list)
                        averages_list.append(average)
                        averages_list.append(trading_pair)

            break

        except Exception as e:
            count += 1
            if count > 10:
                quit()
            print('Error in Market analytics:', e)

    # Sorting

    # Sorting trends
    # Define smallest item index value
    for iteration_1 in range(0, len(trends_list), 2):
        smallest = iteration_1

        # Compares current smallest to rest of array
        for iteration_2 in range(iteration_1 + 2, len(trends_list), 2):

            # Defines new smallest item index value
            if trends_list[iteration_2] < trends_list[smallest]:
                smallest = iteration_2

        # Swap new smallest value with current value
        trends_list[smallest], trends_list[iteration_1], trends_list[smallest + 1], trends_list[iteration_1 + 1] = trends_list[iteration_1], trends_list[smallest], trends_list[iteration_1 + 1], trends_list[smallest + 1]

    # Sorting averages
    for iteration_1 in range(0, len(averages_list), 2):
        smallest = iteration_1

        for iteration_2 in range(iteration_1 + 2, len(averages_list), 2):

            if averages_list[iteration_2] < averages_list[smallest]:
                smallest = iteration_2

        averages_list[smallest], averages_list[iteration_1], averages_list[smallest + 1], averages_list[iteration_1 + 1] = averages_list[iteration_1], averages_list[smallest], averages_list[iteration_1 + 1], averages_list[smallest + 1]
    averages_list.reverse()

    # Finding the trading pair's total rank
    for i in range(1, len(trends_list), 2):
        trading_pair = trends_list[i]
        if trading_pair in averages_list:
            average = averages_list.index(trading_pair)
            index_sum = average + i

            # Finding the best pair
            new_pair = [trading_pair, index_sum]
            if len(best_pair) == 0:
                best_pair = new_pair
            elif new_pair[1] > best_pair[1]:
                best_pair = new_pair

    trading_pair = best_pair[0]
    return trading_pair
