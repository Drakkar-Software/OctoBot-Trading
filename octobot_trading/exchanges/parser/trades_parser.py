from octobot_trading.enums import OrderStatus, TradeOrderType
import octobot_trading.exchanges.parser as parser


class TradesParser(parser.OrdersParser):
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

    async def parse_trades(
        self, raw_trades: list, check_completeness: bool = True
    ) -> list:
        """

        use this method to parse a raw list of trades

        :param raw_trades:
         # optional
        :param check_completeness: if true checks all attributes,
            if somethings missing it'll try to fetch it from the exchange

        :return: formatted trades list of trade dicts

        """
        check_completeness = (
            check_completeness if check_completeness is not None else True
        )
        self._ensure_list(raw_trades)
        self.formatted_records = (
            [
                await self.parse_trade(raw_trade, check_completeness)
                for raw_trade in raw_trades
            ]
            if self.raw_records
            else []
        )
        if check_completeness:
            self._create_debugging_report()
        return self.formatted_records

    async def parse_trade(
        self, raw_trade: dict, check_completeness: bool = True
    ) -> dict:
        # all trades are closed orders (if status is missing)
        # set type to market if its missing
        await self.parse_order(
            raw_trade,
            status=OrderStatus.CLOSED.value,
            order_type=TradeOrderType.MARKET.value,
            check_completeness=check_completeness,
        )
        return self.formatted_record
