class Strategy:
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, "")

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            "Binance": {"pairs": ["BTC-USDT"],},
        }
        self.period = 5 * 60
        self.options = {}

        # user defined class attribute
        self.last_type = "sell"
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.high_price_trace = np.array([])
        self.low_price_trace = np.array([])
        self.ma_long = 150
        self.ma_short = 15
        self.UP = 1
        self.DOWN = 2
        self.buy_price = []
        self.hold_time = 0
        self.last_eth = 0
        self.l_ma = 0
        self.init_usdt = 0
        self.BUY = 3
        self.SELL = 4

    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        self.l_ma = l_ma
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN

    def sar_indicator(self):
        sar = talib.SAR(self.high_price_trace, self.low_price_trace)[-1]
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        if s_ma > sar:
            return self.BUY
        else:
            return self.SELL

    # called every self.period
    def trade(self, information):

        exchange = list(information["candles"])[0]
        pair = list(information["candles"][exchange])[0]
        close_price = information["candles"][exchange][pair][0]["close"]
        high_price = information["candles"][exchange][pair][0]["high"]
        low_price = information["candles"][exchange][pair][0]["low"]

        if self.init_usdt == 0:
            self.init_usdt = self["assets"][exchange]["USDT"]

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        self.high_price_trace = np.append(self.high_price_trace, [float(high_price)])
        self.low_price_trace = np.append(self.low_price_trace, [float(low_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long :]
        self.high_price_trace = self.high_price_trace[-self.ma_long :]
        self.low_price_trace = self.low_price_trace[-self.ma_long :]
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()

        Log(
            "info: "
            + str(information["candles"][exchange][pair][0]["time"])
            + ", "
            + str(information["candles"][exchange][pair][0]["open"])
            + ", assets"
            + str(self["assets"][exchange]["BTC"])
        )

        # get_last_order = GetLastOrderSnapshot()
        # Log(str(get_last_order))

        actions = []

        if self["assets"][exchange]["BTC"] > 0:
            self.hold_time += 1

        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []

        if (
            self.sar_indicator() == self.BUY
            and talib.MOM(self.close_price_trace, timeperiod=self.ma_short)[-1] > 0
            # and close_price < self.l_ma
            and cur_cross == self.UP
            and self.last_cross_status == self.DOWN
            and self["assets"][exchange]["BTC"] <= 6
        ):
            Log("buying, opt1:" + self["opt1"])
            self.buy_price.append(int(close_price))
            self.last_cross_status = cur_cross
            actions.append(
                {
                    "exchange": exchange,
                    "amount": 1,
                    "price": -1,
                    "type": "MARKET",
                    "pair": pair,
                }
            )

        if self["assets"][exchange]["BTC"] > 1 and (
            close_price > 1.5 * max(self.buy_price) * (0.993 ** self.hold_time)
            or close_price > 1.03 * max(self.buy_price)
        ):
            Log("selling, " + exchange + ":" + pair)
            self.last_cross_status = cur_cross
            self.hold_time = 0
            self.buy_price.sort()
            amount = int(max(1, self["assets"][exchange]["BTC"] // 2))
            self.buy_price = self.buy_price[:-amount]
            actions.append(
                {
                    "exchange": exchange,
                    "amount": amount,
                    "price": -1,
                    "type": "MARKET",
                    "pair": pair,
                }
            )

        self.last_cross_status = cur_cross
        return actions
