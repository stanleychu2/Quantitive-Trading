class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['MIOTA-USDT'],
            },
        }
        self.period = 10 * 60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.amount = 2000

        # hyparameters settinh
        self.ma_long = 200
        self.ma_mid = 100
        self.ma_short = 50
        self.UP = 1
        self.DOWN = 2

    def get_RSI(self):

        return talib.RSI(self.close_price_trace, 50)[-1];

    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        m_ma = talib.SMA(self.close_price_trace, self.ma_mid)[-1]

        if np.isnan(s_ma) or np.isnan(l_ma)  or np.isnan(m_ma):
            return None
        if s_ma > m_ma > l_ma:
            return self.UP
        elif s_ma < m_ma < l_ma:
            return self.DOWN

    # called every self.period
    def trade(self, information):

        extra = 0
        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        #  收盤價
        close_price = information['candles'][exchange][pair][0]['close']

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()

        # Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['MIOTA']))

        # Log(str(self.get_RSI()) + "RSI")

        if cur_cross is None:
            return []

        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []

        # cross up
        if  close_price <= min(self.close_price_trace[-1*self.ma_mid:-1]):
            Log("Min")
            return [
                {
                    'exchange': exchange,
                    'amount': 5000,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif  close_price >= max(self.close_price_trace[-1*self.ma_mid:-1]):
            Log("Max")
            return [
                {
                    'exchange': exchange,
                    'amount': -2000,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif  cur_cross == self.UP:
            Log('buying, opt1:' + self['opt1'])
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            if self.get_RSI() <= 47:
                extra =  500
            return [
                {
                    'exchange': exchange,
                    'amount': self.amount + extra,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # cross down
        elif self['assets'][exchange]['MIOTA'] > 0 and cur_cross == self.DOWN:
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            if self.get_RSI() >= 55.5:
                extra = 500
            return [
                {
                    'exchange': exchange,
                    'amount': -1*(self.amount+extra),
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        self.last_cross_status = cur_cross
        return []
