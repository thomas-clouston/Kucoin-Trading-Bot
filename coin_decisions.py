# Decisions
def decision(current_position, close_price, change, bounce_range, change_period, last_close, bounce_continuation):
    if current_position == 'buy':
        bounce_range = -abs(bounce_range)

        if change <= (bounce_range * 2):
            position_change = 'sell'
        elif change < 0:
            if last_close == 0:
                last_close = close_price
                change_period += change
                bounce_continuation = True
            elif close_price <= last_close:
                change_period += change
                last_close = close_price
                bounce_continuation = True
            elif close_price > last_close:
                if bounce_continuation is True:
                    bounce_continuation = False
                    last_close = close_price
                else:
                    change_period = 0
                    last_close = 0

            if change_period < (bounce_range * 2):
                position_change = 'sell'
        elif change >= 0:
            if bounce_continuation is True:
                bounce_continuation = False
            else:
                change_period = 0
                last_close = 0

    elif current_position == 'sell':
        bounce_range = abs(bounce_range)

        if change >= (bounce_range * 2):
            position_change = 'buy'
        elif change > 0:
            if last_close == 0:
                last_close = close_price
                change_period += change
                bounce_continuation = True
            elif close_price >= last_close:
                change_period += change
                last_close = close_price
                bounce_continuation = True
            elif close_price < last_close:
                if bounce_continuation is True:
                    bounce_continuation = False
                    last_close = close_price
                else:
                    change_period = 0
                    last_close = 0

            if change_period > (bounce_range * 2):
                position_change = 'buy'
        elif change <= 0:
            if bounce_continuation is True:
                bounce_continuation = False
            else:
                change_period = 0
                last_close = 0
    try:
        return change_period, last_close, position_change, bounce_continuation
    except:
        position_change = None
        return change_period, last_close, position_change, bounce_continuation
