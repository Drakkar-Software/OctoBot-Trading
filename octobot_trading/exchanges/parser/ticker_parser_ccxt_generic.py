import octobot_trading.exchanges.parser.ticker_parser_ccxt as ticker_parser_ccxt
from octobot_trading.enums import (
    ExchangeConstantsTickersColumns as TickerCols,
)
import octobot_trading.exchanges.parser.util as parser_util


class GenericCCXTTickerParser(ticker_parser_ccxt.CCXTTickerParser):
    """
    dont override this class, use CCXTTickerParser as a base instead

        parser usage:   parser = GenericCCXTTickerParser(exchange)
                        ticker = await parser.parse_trades(raw_ticker)
    """

    FETCH_PRICES_WITH_GET_SYMBOL_IF_MISSING: bool = True

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "generic ccxt ticker"

    def _parse_timestamp(self):
        self._try_to_find_and_set(
            TickerCols.TIMESTAMP.value,
            self.TIMESTAMP_KEYS,
            parse_method=parser_util.convert_any_time_to_seconds,
            not_found_method=self.missing_timestamp,
        )

    def missing_timestamp(self, _):
        return self.exchange.connector.client.milliseconds
