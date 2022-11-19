

from octobot_trading.enums import ExchangeConstantsOrderColumns as ecoc, \
    ExchangeConstantsTickersColumns as t_cols


class TickerParser:
    """
    overwrite TickerParser class methods if necessary
    always/only include bulletproof custom code into the parser to improve generic support

        parser usage:   parser = TickerParser(exchange)
                        ticker = await parser.parse_trades(raw_ticker)
    """

    def parse_ticker(self, exchange, ticker, symbol):
        """

        use this method to parse a raw ticker

        :param raw_ticker:

        :return: formatted ticker

        """
        self._parse_timestamp(ticker, exchange)
        self._parse_base_volume(ticker, exchange, symbol)
        return ticker

    @staticmethod
    def _parse_timestamp(ticker, exchange):
        if not ticker.get(ecoc.TIMESTAMP.value):
            ticker[t_cols.TIMESTAMP.value] = exchange.connector.client.milliseconds()

    @staticmethod
    def _parse_base_volume(ticker, exchange, symbol):
        if not ticker.get(t_cols.BASE_VOLUME.value):
            try:
                ticker[t_cols.BASE_VOLUME.value] \
                    = ticker[t_cols.QUOTE_VOLUME.value] / ticker[t_cols.CLOSE.value]
            except Exception as e:
                # todo check is it critical?
                exchange.logger.warning(f"Failed to get ticker parameter: "
                                        f"base volume - symbol {symbol} - error: {e}")
        if not ticker.get(ecoc.TIMESTAMP.value):
            ticker[t_cols.TIMESTAMP.value] = exchange.connector.client.milliseconds()