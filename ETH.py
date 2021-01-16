# Class name must be Strategy
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
               'pairs': ['ETH-USDT'],  #交易對
           },
       }
       self.period = 10 * 60 #取樣頻率
       self.options = {}
       # user defined class attribute
       self.last_type = 'sell'
       self.last_cross_status = None
       self.close_price_trace = np.array([])
       self.ma_long = 10  #定義10個週期，用以計算長均線
       self.ma_short = 5  #定義5個週期，用以計算短均線
       self.UP = 1
       self.DOWN = 2
       self.firstbuy = 0
       self.lastbuyprice = 0
   def get_current_ma_cross(self):
       s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
       l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
       if np.isnan(s_ma) or np.isnan(l_ma):
           return None
       if s_ma > l_ma:
           return self.UP
       return self.DOWN
   # called every self.period
   def trade(self, information):  
      
       exchange = list(information['candles'])[0]                          #交易所
       pair = list(information['candles'][exchange])[0]                    #交易對
       close_price = information['candles'][exchange][pair][0]['close']    #收盤價格
       targetCurrency_amount = self['assets'][exchange]['ETH']             #持有量
    # add latest price into trace
       self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
       # only keep max length of ma_long count elements
       self.close_price_trace = self.close_price_trace[-self.ma_long:]
       # calculate current ma cross status
       cur_cross = self.get_current_ma_cross()
       #print 交易時間、開盤價等資訊
       Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['ETH']))
      
       if self.firstbuy == 0:  #等黃金交叉 先買40k
           if cur_cross is None:
               return []
           if self.last_cross_status is None:
               self.last_cross_status = cur_cross
               return []
           # cross up
           if self.last_type == 'sell' and cur_cross == self.UP and self.last_cross_status == self.DOWN:  
               Log('buying, opt1:' + self['opt1'])
               self.last_type = 'buy'
               self.last_cross_status = cur_cross
               self.firstbuy = 1
               self.lastbuyprice = close_price
               return [
                   {
                       'exchange': exchange,     #交易所
                       'amount': 65 ,            #買65
                       'price': -1 ,             #price不指定
                       'type': 'MARKET',
                       'pair': pair,
                   }
               ]
           self.last_cross_status = cur_cross
           return []
       else:   #網格策略+上下bound
           if close_price/self.lastbuyprice >= 1.014 and (self['assets'][exchange]['ETH'] - 1 ) * close_price > 15000 :  
           #若漲1.4% 且 賣掉後的ETH > 15000 則賣
               self.lastbuyprice = close_price
               return [
                   {
                       'exchange': exchange,
                       'amount': - 1 , 
                       'price': -1,
                       'type': 'MARKET',
                       'pair': pair,
                   }
            ]
           elif close_price/self.lastbuyprice <= 0.986 and self['assets'][exchange]['USDT'] - close_price > 15000 :  
           #若跌1.4% 且 買後的USDT > 15000  則買
               self.lastbuyprice = close_price
               return [
                   {
                       'exchange': exchange,
                       'amount': 1 , 
                       'price': -1,
                       'type': 'MARKET',
                       'pair': pair,
                   }
               ]          
           return []
      