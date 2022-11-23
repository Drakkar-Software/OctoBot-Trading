from octobot_commons import enums as commons_enums
from octobot_trading.enums import (
    ExchangeConstantsOrderColumns as ecoc,
    ExchangeConstantsTickersColumns as t_cols,
)
from octobot_trading.exchanges.parser.util import Parser

# todo WIP
class FundingRateParser(Parser):
    """
    overwrite FundingRateParser class methods if necessary
    always/only include bulletproof custom code into the parser to improve generic support

        parser usage:   parser = FundingRateParser(exchange)
                        funding_rate = await parser.parse_funding_rate(raw_funding_rate)
    """

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "funding rate"
        
    def parse_funding_rate(self, funding_rate: dict):
        """

        use this method to parse a raw ticker

        :param symbol:
        :param ticker:
        :param exchange:

        :return: formatted ticker

        """
        self._ensure_dict(funding_rate)
#         self._parse_symbol()
#     def parse_funding(self, funding_dict, from_ticker=False):
        
# '            last_funding_time = self.connector.get_uniform_timestamp(
#                 self.connector.client.safe_float(funding_dict, self.BINANCE_LAST_FUNDING_TIME))
#             funding_dict = {
#                 trading_enums.ExchangeConstantsFundingColumns.LAST_FUNDING_TIME.value: last_funding_time,
#                 trading_enums.ExchangeConstantsFundingColumns.FUNDING_RATE.value:
#                     self.connector.client.safe_float(funding_dict, self.BINANCE_FUNDING_RATE),
#                 trading_enums.ExchangeConstantsFundingColumns.NEXT_FUNDING_TIME.value:
#                     last_funding_time + self.BINANCE_FUNDING_DURATION
#             }
#                         funding_next_timestamp = self.parse_timestamp(
#                 funding_dict, trading_enums.ExchangeConstantsFundingColumns.NEXT_FUNDING_TIME.value)
#             funding_dict.update({
#                 trading_enums.ExchangeConstantsFundingColumns.LAST_FUNDING_TIME.value:
#                     funding_next_timestamp - self.BYBIT_DEFAULT_FUNDING_TIME,
#                 trading_enums.ExchangeConstantsFundingColumns.FUNDING_RATE.value: decimal.Decimal(
#                     funding_dict.get(trading_enums.ExchangeConstantsFundingColumns.FUNDING_RATE.value, 0)),
#                 trading_enums.ExchangeConstantsFundingColumns.NEXT_FUNDING_TIME.value: funding_next_timestamp
#             })'


    @staticmethod
    def _parse_timestamp(ticker, exchange):
        if not ticker.get(ecoc.TIMESTAMP.value):
            ticker[t_cols.TIMESTAMP.value] = exchange.connector.client.milliseconds()

    @staticmethod
    async def _parse_base_volume(ticker, exchange, symbol):
        if not ticker.get(t_cols.BASE_VOLUME.value):
            if quote_volume := ticker.get(t_cols.QUOTE_VOLUME.value):
                if close_price := ticker.get(t_cols.CLOSE.value):
                    ticker[t_cols.BASE_VOLUME.value] = quote_volume / close_price
                    return
                # try to fetch close price
                try:
                    symbol_prices = await exchange.get_symbol_prices(
                        symbol=symbol,
                        time_frame=commons_enums.TimeFrames.ONE_MINUTE,
                        limit=1,
                    )
                    close_price = symbol_prices[0][4]
                    ticker[t_cols.BASE_VOLUME.value] = quote_volume / close_price
                except KeyError:
                    exchange.logger.exception(
                        f"Failed to calculate ticker base volume using: quote_volume ({quote_volume or 'no quote volume'}) "
                        f"/ close_price (failed to fetch close price)"
                    )
                    raise RuntimeError
                except Exception as e:
                    exchange.logger.exception(
                        e,
                        True,
                        f"Failed to calculate ticker base volume using: quote_volume ({quote_volume or 'no quote volume'}) "
                        f"/ close_price (failed to fetch close price)",
                    )
                    raise RuntimeError

            raise NotImplementedError(
                "Failed to parse ticker base volume: base volume is missing "
                f"and not able to calculate based on quote volume ({quote_volume or 'no quote volume'}) "
                f"/ close_price ({close_price or 'no close price'})"
            )
