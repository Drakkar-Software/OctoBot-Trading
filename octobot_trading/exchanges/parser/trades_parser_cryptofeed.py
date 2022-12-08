import octobot_trading.exchanges.parser.orders_parser_cryptofeed as orders_parser_cryptofeed


class CryptoFeedTradesParser(orders_parser_cryptofeed.CryptoFeedOrdersParser):
    """
    override CryptoFeedTradesParser if you add support for a crypto feed exchange

    parser usage:   parser = CryptoFeedTradesParser(exchange)
                    orders = await parser.parse_orders(raw_orders)
                    order = await parser.parse_order(raw_order)
    """

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "crypto feed trades"

    async def parse_trades(self):
        raise NotImplementedError

    async def parse_trade(
        self,
        crypto_feed_trade,
        check_completeness: bool = True,
    ) -> dict:
        """
        use this method to format a single trade

        :param crypto_feed_trade: crypto_feed_trade with eventually missing data

        :param check_completeness: if true checks all attributes,
            if somethings missing it'll try to fetch it from the exchange

        :return: formatted trade dict (100% complete or we raise NotImplemented)

        """

        await super().parse_trade(
            raw_trade=crypto_feed_trade.__dict__, check_completeness=check_completeness
        )
