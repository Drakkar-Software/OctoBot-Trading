import typing
from octobot_commons import enums as commons_enums
from octobot_trading.enums import (
    ExchangeConstantsTickersColumns as TickerCols,
    ExchangeConstantsMiniTickerColumns as mTickerCols,
    ExchangeConstantsMarkPriceColumns as MarkPriceCols,
)
import octobot_trading.exchanges.parser.util as parser_util


class TickerParser(parser_util.Parser):
    """
    overwrite TickerParser class methods if necessary
    always/only include bulletproof custom code into the parser to improve generic support

        parser usage:   parser = TickerParser(exchange)
                        ticker = await parser.parse_trades(raw_ticker)
    """

    fetched_symbol_prices: list = None

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "ticker"

    async def parse_ticker_list(self, raw_tickers: list) -> list:
        """
        use this method to format a list of tickers
        :param raw_tickers: raw tickers list
        :return: formatted tickers list
        """
        self._ensure_list(raw_tickers)
        self.formatted_records = (
            [await self.parse_ticker(ticker) for ticker in raw_tickers]
            if self.raw_records
            else []
        )
        self._create_debugging_report()
        return self.formatted_records

    async def parse_ticker(
        self,
        raw_ticker: dict,
        symbol: str = None,
        also_get_mini_ticker: bool = False,
    ) -> typing.Tuple[dict, dict] or dict:
        """

        use this method to parse a raw ticker

        :param raw_ticker:
        :param symbol:
        :param also_get_mini_ticker:

        :return: formatted ticker or (formatted ticker, formatted mini ticker)

        """
        self._ensure_dict(raw_ticker)
        self.fetched_symbol_prices: list = []  # clear previously fetched data
        try:
            self._parse_symbol(symbol)
            self._parse_timestamp()
            self._parse_average()
            self._parse_bid()
            self._parse_bid_volume()
            self._parse_ask()
            self._parse_ask_volume()
            self._parse_last_price()
            self._parse_previous_close_price()
            self._parse_change()
            self._parse_percentage()
            await self._parse_open_price()
            await self._parse_high_price()
            await self._parse_low_price()
            await self._parse_close_price()
            self._parse_quote_volume()
            self._parse_base_volume()  # parse after mark price and quote volume
            if self.exchange.CONNECTOR_CONFIG.MARK_PRICE_IN_TICKER:
                self._parse_mark_price()
            if self.exchange.exchange_manager.is_future:
                if self.exchange.CONNECTOR_CONFIG.FUNDING_IN_TICKER:
                    self.formatted_record = {
                        **self.formatted_record,
                        **self.exchange.connector.parse_funding_rate(
                            raw_ticker, from_ticker=True
                        ),
                    }

            self._create_debugging_report_for_record()
            if also_get_mini_ticker:
                return self.formatted_record, self._parse_mini_ticker()
        except Exception as e:
            # just in case something bad happens
            # this should never happen, check the parser code
            self._log_missing(
                "failed to parse ticker",
                "not able to complete ticker parser",
                error=e,
            )
        return self.formatted_record

    def _parse_mini_ticker(self) -> dict:
        """
        Mini ticker
        """
        try:
            return {
                mTickerCols.HIGH_PRICE.value: self.formatted_record[
                    TickerCols.HIGH.value
                ],
                mTickerCols.LOW_PRICE.value: self.formatted_record[
                    TickerCols.LOW.value
                ],
                mTickerCols.OPEN_PRICE.value: self.formatted_record[
                    TickerCols.OPEN.value
                ],
                mTickerCols.CLOSE_PRICE.value: self.formatted_record[
                    TickerCols.CLOSE.value
                ],
                mTickerCols.VOLUME.value: self.formatted_record[
                    TickerCols.BASE_VOLUME.value
                ],
                mTickerCols.TIMESTAMP.value: self.formatted_record[
                    TickerCols.TIMESTAMP.value
                ],
            }
        except KeyError:
            # this error should never happen as we already raise if missing before
            self.exchange.logger.error(
                f"Failed to parse mini ticker, raw ticker: {self.formatted_record}"
            )
            return {}

    def _parse_symbol(self, missing_symbol_value):
        self._try_to_find_and_set(
            TickerCols.SYMBOL.value,
            [TickerCols.SYMBOL.value],
            not_found_val=missing_symbol_value,
        )

    def _parse_timestamp(self):
        self._try_to_find_and_set(
            TickerCols.TIMESTAMP.value,
            [TickerCols.TIMESTAMP.value],
            parse_method=parser_util.convert_any_time_to_seconds,
            not_found_method=self.missing_timestamp,
        )

    def missing_timestamp(self, _):
        return self.exchange.connector.client.milliseconds

    def _parse_quote_volume(self):
        self._try_to_find_and_set_decimal(
            TickerCols.QUOTE_VOLUME.value,
            [TickerCols.QUOTE_VOLUME.value],
        )

    def _parse_base_volume(self):
        self._try_to_find_and_set_decimal(
            TickerCols.BASE_VOLUME.value,
            [TickerCols.BASE_VOLUME.value],
            not_found_method=self._missing_base_volume,
        )

    def _missing_base_volume(self, _):
        close_price = None
        if (
            quote_volume := self.formatted_record.get(TickerCols.QUOTE_VOLUME.value)
        ) and (close_price := self.formatted_record.get(TickerCols.CLOSE.value)):
            return quote_volume / close_price
        self._log_missing(
            TickerCols.BASE_VOLUME.value,
            "base volume is missing and not able to calculate based on quote "
            f"volume ({quote_volume or 'no quote volume'}) "
            f"/ close_price ({close_price or 'no close price'})",
        )

    def _parse_average(self):
        # optional
        self._try_to_find_and_set_decimal(
            TickerCols.AVERAGE.value,
            [TickerCols.AVERAGE.value],
            enable_log=False,
        )

    def _parse_bid(self):
        # optional
        self._try_to_find_and_set_decimal(
            TickerCols.BID.value,
            [TickerCols.BID.value],
            enable_log=False,
        )

    def _parse_bid_volume(self):
        # optional
        self._try_to_find_and_set_decimal(
            TickerCols.BID_VOLUME.value,
            [TickerCols.BID_VOLUME.value],
            enable_log=False,
        )

    def _parse_ask(self):
        # optional
        self._try_to_find_and_set_decimal(
            TickerCols.ASK.value,
            [TickerCols.ASK.value],
            enable_log=False,
        )

    def _parse_ask_volume(self):
        # optional
        self._try_to_find_and_set_decimal(
            TickerCols.ASK_VOLUME.value,
            [TickerCols.ASK_VOLUME.value],
            enable_log=False,
        )

    def _parse_last_price(self):
        # optional
        self._try_to_find_and_set_decimal(
            TickerCols.LAST.value,
            [TickerCols.LAST.value],
            enable_log=False,
        )

    def _parse_previous_close_price(self):
        # optional
        self._try_to_find_and_set_decimal(
            TickerCols.PREVIOUS_CLOSE.value,
            [TickerCols.PREVIOUS_CLOSE.value],
            enable_log=False,
        )

    def _parse_change(self):
        # optional
        self._try_to_find_and_set_decimal(
            TickerCols.CHANGE.value,
            [TickerCols.CHANGE.value],
            enable_log=False,
        )

    def _parse_percentage(self):
        # optional
        self._try_to_find_and_set_decimal(
            TickerCols.PERCENTAGE.value,
            [TickerCols.PERCENTAGE.value],
            enable_log=False,
        )

    async def _parse_open_price(self):
        await self._try_to_find_and_set_decimal_async(
            TickerCols.OPEN.value,
            [TickerCols.OPEN.value],
            not_found_method=self.missing_open_price,
            not_found_method_is_async=True,
        )

    async def _parse_high_price(self):
        await self._try_to_find_and_set_decimal_async(
            TickerCols.HIGH.value,
            [TickerCols.HIGH.value],
            not_found_method=self.missing_high_price,
            not_found_method_is_async=True,
        )

    async def _parse_low_price(self):
        await self._try_to_find_and_set_decimal_async(
            TickerCols.LOW.value,
            [TickerCols.LOW.value],
            not_found_method=self.missing_low_price,
            not_found_method_is_async=True,
        )

    async def _parse_close_price(self):
        await self._try_to_find_and_set_decimal_async(
            TickerCols.CLOSE.value,
            [TickerCols.CLOSE.value],
            not_found_method=self.missing_close_price,
            not_found_method_is_async=True,
        )

    def _parse_mark_price(self):
        self._try_to_find_and_set_decimal(
            MarkPriceCols.MARK_PRICE.value,
            [MarkPriceCols.MARK_PRICE.value],
            use_info_sub_dict=True,
        )

    async def missing_open_price(self, _):
        if price := await self._fetch_missing_symbol_prices(index=1):
            return price

    async def missing_high_price(self, _):
        if price := await self._fetch_missing_symbol_prices(index=2):
            return price

    async def missing_low_price(self, _):
        if price := await self._fetch_missing_symbol_prices(index=3):
            return price

    async def missing_close_price(self, _):
        if price := await self._fetch_missing_symbol_prices(index=4):
            return price

    async def _fetch_missing_symbol_prices(self, index) -> list or False:
        if not self.fetched_symbol_prices:
            try:
                self.fetched_symbol_prices = await self.exchange.get_symbol_prices(
                    symbol=self.formatted_record[TickerCols.SYMBOL.value],
                    time_frame=commons_enums.TimeFrames.ONE_MINUTE,
                    limit=1,
                )
            except Exception as e:
                self._log_missing(
                    "fetch_missing_symbol_prices",
                    "Failed to fetch symbol prices",
                    error=e,
                )
                return False
        try:
            return self.fetched_symbol_prices[0][index]
        except KeyError:
            self._log_missing(
                "fetch_missing_symbol_prices",
                "Failed to fetch symbol prices - got an empty response",
            )
            return False
