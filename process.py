# Imports
from market_analytics import analyse_market
from coin_analytics import analyse_coin
from position_decider import choose_position
from kucoin_futures.client import Market, Trade, User
from datetime import datetime, date, timedelta, time


class Run:
    def __init__(self, api_key, api_secret, api_passphrase, fail):
        # Credentials
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase

        # Parameters
        self.loss_count = 0
        self.just_opened = False
        self.fail = fail
        self.past_PNL = None
        self.open_position = False
        self.wait = False
        self.exclude = False

        # Setting up clients

        # Setup trading client
        self.trading_client = Trade(api_key, api_secret, api_passphrase, is_sandbox=False, url='')

        # Setup market client
        self.market_client = Market(url='https://api-futures.kucoin.com')

        # Setup user client
        self.user_client = User(api_key, api_secret, api_passphrase)

        self.main_process()

    # Closing position process
    def closing_process(self, pair):
        count = 0

        while True:
            try:
                close_position = self.trading_client.create_market_order(pair, self.current_position, '1', closeOrder=True)
                self.open_position = False
                count = 0
                break
            except Exception as e:
                count += 1
                if count > 10:
                    quit()
                print('Error in closing position:', e)

    # Opening position process
    def opening_process(self):
        count = 0

        while True:
            try:
                # Balance
                user = self.user_client.get_account_overview('USDT')
                balance = user['availableBalance']

                # Use quarter of balance
                balance_divisor = 4

                # Decide leverage
                if self.position_change == 'sell':
                    leverage = '1'
                elif self.position_change == 'buy':
                    leverage = '2'

                balance = balance / balance_divisor

                # Lot size
                contract = self.market_client.get_contract_detail(self.trading_pair)
                multiplier = contract['multiplier']

                # Trade amount calculation
                price = self.market_client.get_ticker(self.trading_pair)
                price = price['price']
                price = float("{:.9f}".format(float(price)))

                # Minimum amount
                minimum_amount = price * multiplier

                trade_amount = balance / price
                trade_amount = (trade_amount * int(leverage)) / multiplier

                if trade_amount > minimum_amount:
                    # Preform order
                    open_order = self.trading_client.create_market_order(self.trading_pair, self.position_change, leverage, size=trade_amount)

                # Checking for order success
                position = self.trading_client.get_all_position()

                count = 0
                break

            except Exception as e:
                count += 1
                if count > 10:
                    quit()
                print('Error in opening order:', e)

        # If the order failed
        if 'data' in position:
            self.open_position = False
            self.wait = False
            self.exclude = False
            self.main_process()

        # If order succeeded
        self.current_position = self.position_change
        self.wait = True
        self.just_opened = True
        self.open_position = True
        self.exclude = False

    # Bot looping
    def main_process(self):
        count = 0

        # Waiting for an hour
        if self.wait is True:
            current_time = datetime.now()
            loop_time = time(0, 0)
            loop_time = datetime.combine(date.today(), loop_time)

            while loop_time < current_time:
                loop_time = loop_time + timedelta(minutes=60)

            loop_time = loop_time - timedelta(minutes=5)

            if loop_time < current_time:
                loop_time = loop_time + timedelta(minutes=60)

            current_time = current_time.strftime("%H:%M")
            loop_time = loop_time.strftime("%H:%M")

            while current_time != loop_time:
                current_time = datetime.now()
                current_time = current_time.strftime("%H:%M")

        # Finding new coin
        if self.open_position is False:
            if self.exclude is True:
                self.trading_pair = analyse_market(self.coin_exclude)
            else:
                self.trading_pair = analyse_market()

            # Deciding initial coin position
            if self.open_position is False:
                while True:
                    try:
                        issue = 'Error finding initial Bounce range:'
                        bounce_ranges = analyse_coin(self.trading_pair)
                        positive_bounce_range = bounce_ranges[0]
                        negative_bounce_range = bounce_ranges[1]

                        issue = 'Error finding initial Position change:'
                        self.position_change = choose_position(self.trading_pair, positive_bounce_range, negative_bounce_range)
                        count = 0
                        break
                    except Exception as e:
                        count += 1
                        if count > 10:
                            quit()
                        print(issue, e)

                # Opening new position for new coin
                self.opening_process()

        # Checking PNL
        if self.just_opened is False:
            while True:
                try:
                    PNL = self.trading_client.get_position_details(self.trading_pair)
                    PNL = PNL['unrealisedPnl']

                    count = 0
                    break
                except Exception as e:
                    count += 1
                    if count > 10:
                        quit()
                    print('Error fetching PNL:', e)

            # Deciding if a coin change is needed
            if PNL < 0:
                if self.past_PNL is None:
                    self.past_PNL = PNL

                elif PNL <= self.past_PNL:
                    self.loss_count += 1
                    if self.loss_count == self.fail:
                        self.wait = False
                        self.open_position = False
                        self.loss_count = 0
                        self.past_PNL = None
                        self.exclude = True
                        self.coin_exclude = self.trading_pair
                        self.closing_process(self.trading_pair)
                        self.main_process()

                elif PNL > self.past_PNL:
                    self.past_PNL = PNL
        else:
            self.just_opened = False

        # Finding bounce range and position
        while True:
            try:
                issue = 'Error finding Bounce range:'

                position = self.trading_client.get_all_position()
                open_time = position[0]['openingTimestamp']

                bounce_ranges = analyse_coin(self.trading_pair, open_time, self.current_position)
                positive_bounce_range = bounce_ranges[0]
                negative_bounce_range = bounce_ranges[1]

                issue = 'Error finding Position change:'
                self.position_change = choose_position(self.trading_pair, positive_bounce_range, negative_bounce_range, open_time, self.current_position)

                count = 0
                break
            except Exception as e:
                count += 1
                if count > 10:
                    quit()
                print(issue, e)

        # If a change in position is needed
        if self.position_change != self.current_position:
            self.closing_process(self.trading_pair)

            # Opening new position
            self.opening_process()

        # Loop
        self.main_process()
