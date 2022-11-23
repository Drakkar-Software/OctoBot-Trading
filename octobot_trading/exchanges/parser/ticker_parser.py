from octobot_commons import enums as commons_enums
from octobot_trading.enums import (
    ExchangeConstantsOrderColumns as ecoc,
    ExchangeConstantsTickersColumns as t_cols,
)


class TickerParser:
    """
    overwrite TickerParser class methods if necessary
    always/only include bulletproof custom code into the parser to improve generic support

        parser usage:   parser = TickerParser(exchange)
                        ticker = await parser.parse_trades(raw_ticker)
    """

    async def parse_ticker(self, exchange, ticker, symbol):
        """

        use this method to parse a raw ticker

        :param symbol:
        :param ticker:
        :param exchange:

        :return: formatted ticker

        """
        self._parse_timestamp(ticker, exchange)
        await self._parse_base_volume(ticker, exchange, symbol)
        return ticker

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
