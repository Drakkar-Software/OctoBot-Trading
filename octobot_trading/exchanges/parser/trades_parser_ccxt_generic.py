import octobot_trading.exchanges.parser as parser


class GenericCCXTTradesParser(parser.CCXTTradesParser, parser.GenericCCXTOrdersParser):
    """
    dont override this class, use CCXTTradesParser or TradesParser as a base instead 

        parser usage:   parser = GenericCCXTTradesParser(exchange)
                        trades = await parser.parse_trades(raw_trades)
                        trade = await parser.parse_trade(raw_trade)
    """

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "generic ccxt recent trades"

