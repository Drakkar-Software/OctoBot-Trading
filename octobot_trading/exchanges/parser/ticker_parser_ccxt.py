from octobot_trading.enums import (
    ExchangeConstantsTickersColumns as TickerCols,
    ExchangeConstantsMarkPriceColumns as MarkPriceCols,
)
import octobot_trading.exchanges.parser.ticker_parser as ticker_parser
import octobot_trading.exchanges.parser.util as parser_util


class CCXTTickerParser(ticker_parser.TickerParser):
    """
    use CCXTTickerParser as a base if you want to add support for a new exchange
    
    only include code into the parser according to ccxt standards

        parser usage:   parser = TickerParser(exchange)
                        ticker = await parser.parse_trades(raw_ticker)
    """

    SYMBOL_KEYS: list = [TickerCols.SYMBOL.value]
    TIMESTAMP_KEYS: list = [TickerCols.TIMESTAMP.value]
    AVERAGE_KEYS: list = [TickerCols.AVERAGE.value]
    BID_KEYS: list = [TickerCols.BID.value]
    BID_VOLUME_KEYS: list = [TickerCols.BID_VOLUME.value]
    ASK_KEYS: list = [TickerCols.ASK.value]
    ASK_VOLUME_KEYS: list = [TickerCols.ASK_VOLUME.value]
    LAST_PRICE_KEYS: list = [TickerCols.LAST.value]
    PREVIOUS_CLOSE_PRICE_KEYS: list = [TickerCols.PREVIOUS_CLOSE.value]
    CHANGE_KEYS: list = [TickerCols.CHANGE.value]
    PERCENTAGE_KEYS: list = [TickerCols.PERCENTAGE.value]
    OPEN_PRICE_KEYS: list = [TickerCols.OPEN.value]
    HIGH_PRICE_KEYS: list = [TickerCols.HIGH.value]
    LOW_PRICE_KEYS: list = [TickerCols.LOW.value]
    CLOSE_PRICE_KEYS: list = [TickerCols.CLOSE.value]
    QUOTE_VOLUME_KEYS: list = [TickerCols.QUOTE_VOLUME.value]
    BASE_VOLUME_KEYS: list = [TickerCols.BASE_VOLUME.value]
    MARK_PRICE_KEYS: list = [MarkPriceCols.MARK_PRICE.value]

    USE_INFO_SUB_DICT_FOR_MARK_PRICE: bool = True

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "ccxt ticker"

