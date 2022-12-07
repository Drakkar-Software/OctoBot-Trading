import octobot_trading.exchanges.parser as parser


class CCXTTradesParser(parser.TradesParser, parser.CCXTOrdersParser):
    """
    overwrite TradesParser class methods if necessary
    always/only include bulletproof custom code into the parser to improve generic support

        parser usage:   parser = TradesParser(exchange)
                        trades = await parser.parse_trades(raw_trades)
                        trade = await parser.parse_trade(raw_trade)
    """

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "recent trades"
