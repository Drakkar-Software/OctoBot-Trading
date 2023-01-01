import octobot_trading.enums as enums
import octobot_trading.exchanges.parser as parser


class TradesParser(parser.OrdersParser):
    """
        use TradesParser as a base class if you implement
        a new parser for a non ccxt or crypto feed exchange

        parser usage:   parser = TradesParser(exchange)
                        trades = await parser.parse_trades(raw_trades)
                        trade = await parser.parse_trade(raw_trade)
    """

    def __init__(
        self,
        exchange,
        parser_type_name: str = "trades",
    ):
        super().__init__(
            exchange=exchange,
            parser_type_name=parser_type_name,
        )

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
            self.reporter.create_debugging_report(self)
        return self.formatted_records

    async def parse_trade(
        self, raw_trade: dict, check_completeness: bool = True
    ) -> dict:
        # all trades are closed orders (if status is missing)
        # set type to market if its missing
        await self.parse_order(
            raw_trade,
            status=enums.OrderStatus.CLOSED.value,
            order_type=enums.TradeOrderType.MARKET.value,
            check_completeness=check_completeness,
        )
        return self.formatted_record
