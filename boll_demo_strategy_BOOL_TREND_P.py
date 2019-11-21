from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
    Direction
)

from vnpy.trader.constant import Interval

class BollDemoStrategy_BOOL_TREND(CtaTemplate):
    """"""
    author = "用Python的交易员"

    boll_window = 18
    boll_dev = 3.4
    fixed_size = 1
    atr_window = 20
    atr_multiplier = 2
    fixed_tp=500
    boll_up = 0
    boll_down = 0
    boll_mid = 0
    
    atr_value = 0
    intra_trade_high = 0
    long_sl = 0
    intra_trade_low = 0
    short_sl = 0
    
    long_entry= 0
    long_tp= 0
    short_entry= 0
    short_tp= 0

    parameters = [
        "boll_window", "boll_dev", 
        "fixed_size", 
        "atr_window", "atr_multiplier",
        "fixed_tp"
    ]
    variables = [
        "boll_up", "boll_down", "boll_mid",
        "atr_value",
        "intra_trade_high", "long_sl",
        "intra_trade_low", "short_sl",
        "long_entry", "long_tp",
        "short_entry", "short_tp"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar, 1, self.on_15min_bar,interval=Interval.HOUR)
        self.am = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_15min_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        self.boll_up, self.boll_down = am.boll(self.boll_window, self.boll_dev)
        self.boll_mid = am.sma(self.boll_window)
        self.atr_value = am.atr(self.atr_window)
        
        if self.pos == 0:
            self.buy(self.boll_up, self.fixed_size, True)
            self.short(self.boll_down, self.fixed_size, True)

            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            self.long_entry= 0
            self.long_tp= 0
            self.short_entry= 0
            self.short_tp= 0
        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            self.long_sl = self.intra_trade_high - self.atr_value * self.atr_multiplier
            self.long_sl =max(self.boll_mid,long_sl)
            self.sell(self.long_sl, abs(self.pos), True)

            if self.long_tp:
                self.sell(self.long_tp, abs(self.pos))
        elif self.pos < 0:
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.intra_trade_high = bar.high_price

            self.short_sl = self.intra_trade_low + self.atr_value * self.atr_multiplier
            self.short_sl =min(self.boll_mid,short_sl)
            self.cover(self.short_sl, abs(self.pos), True)

            if self.short_tp:
                self.cover(self.short_tp, abs(self.pos))

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        if self.pos !=0:
            if trade.direction == Direction.LONG:
                self.long_entry=trade.close_price
                self.long_tp = self.long_entry+self.fixed_tp
            else:
                self.short_entry=trade.close_price
                self.short_tp = self.short_entry-self.fixed_tp

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
