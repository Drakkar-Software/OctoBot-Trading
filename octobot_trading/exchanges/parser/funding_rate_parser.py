from octobot_trading.enums import ExchangeConstantsFundingColumns as FundingCols
from octobot_trading.exchanges.parser.util import Parser
import octobot_trading.exchanges.parser.util as parser_util
from octobot_trading import constants as trading_constants
from octobot_commons import constants as commons_constants


class FundingRateParser(Parser):
    """
    overwrite FundingRateParser class methods if necessary
    always/only include bulletproof custom code into the parser to improve generic support

        parser usage:   parser = FundingRateParser(exchange)
                        funding_rate = parser.parse_funding_rate(raw_funding_rate)
                        funding_rates = parser.parse_funding_rates(raw_funding_rates)
    """

    FUNDING_TIME_UPDATE_PERIOD: int = None  # in seconds

    TIMESTAMP_KEYS: list = []
    SYMBOL_KEYS: list = []
    FUNDING_RATE_KEYS: list = []
    PREDICTED_FUNDING_RATE_KEYS: list = []
    NEXT_FUNDING_TIME_KEYS: list = []
    LAST_FUNDING_TIME_KEYS: list = []

    USE_INFO_SUB_DICT_FOR_TIMESTAMP: bool = False
    USE_INFO_SUB_DICT_FOR_SYMBOL: bool = False
    USE_INFO_SUB_DICT_FOR_FUNDING_RATE: bool = False
    USE_INFO_SUB_DICT_FOR_PREDICTED_FUNDING_RATE: bool = False
    USE_INFO_SUB_DICT_FOR_NEXT_FUNDING_TIME: bool = False
    USE_INFO_SUB_DICT_FOR_LAST_FUNDING_TIME: bool = False

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "funding rate"

    def parse_funding_rates(self, raw_funding_rates: list) -> list:
        """
        use this method to format a list of funding rates
        :param raw_funding_rates: raw funding rate list
        :return: formatted funding rate list
        """
        self._ensure_list(raw_funding_rates)
        self.formatted_records = (
            [
                self.parse_funding_rate(raw_funding_rate)
                for raw_funding_rate in raw_funding_rates
            ]
            if self.raw_records
            else []
        )
        self._create_debugging_report()
        return self.formatted_records

    def parse_funding_rate(self, raw_funding_rate: dict, from_ticker=False):
        """
        use this method to parse a raw funding rate
        :param raw_funding_rate:
        :return: formatted funding rate
        """
        self._ensure_dict(raw_funding_rate)
        try:
            if from_ticker:
                self.PARSER_TITLE = "funding rate from ticker"
            else:
                self._parse_timestamp()
                self._parse_symbol()
            self._parse_funding_rate()
            self._parse_predicted_funding_rate()
            self._parse_next_funding_time()
            self._parse_last_funding_time()

        except Exception as e:
            # just in case something bad happens
            # this should never happen, check the parser code
            self._log_missing(
                "failed to parse funding rate",
                "not able to complete funding rate parser",
                error=e,
            )
        self._create_debugging_report_for_record()
        return self.formatted_record

    def _parse_timestamp(self):
        self._try_to_find_and_set(
            FundingCols.TIMESTAMP.value,
            self.TIMESTAMP_KEYS,
            parse_method=parser_util.convert_any_time_to_seconds,
            not_found_method=None
            if self.multiple_records
            else self.timestamp_not_found,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_TIMESTAMP,
        )

    def timestamp_not_found(self, _):
        try:
            return int(self.exchange.connector.get_exchange_current_time())
        except Exception as e:
            self._log_missing(
                FundingCols.TIMESTAMP.value,
                f"{FundingCols.TIMESTAMP.value} not found and failed to get "
                "time with get_exchange_current_time: ",
                error=e,
            )

    def _parse_symbol(self):
        self._try_to_find_and_set(
            FundingCols.SYMBOL.value,
            self.SYMBOL_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_SYMBOL,
        )

    def _parse_funding_rate(self):
        self._try_to_find_and_set_decimal(
            FundingCols.FUNDING_RATE.value,
            self.FUNDING_RATE_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_FUNDING_RATE,
            allow_zero=True,
        )

    def _parse_predicted_funding_rate(self):
        self._try_to_find_and_set_decimal(
            FundingCols.PREDICTED_FUNDING_RATE.value,
            self.PREDICTED_FUNDING_RATE_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_PREDICTED_FUNDING_RATE,
            not_found_val=trading_constants.NaN,
            allow_zero=True,
        )

    def _parse_next_funding_time(self):
        self._try_to_find_and_set(
            FundingCols.NEXT_FUNDING_TIME.value,
            self.NEXT_FUNDING_TIME_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_NEXT_FUNDING_TIME,
            parse_method=parser_util.convert_any_time_to_seconds,
        )

    def _parse_last_funding_time(self):
        self._try_to_find_and_set(
            FundingCols.LAST_FUNDING_TIME.value,
            self.LAST_FUNDING_TIME_KEYS,
            parse_method=parser_util.convert_any_time_to_seconds,
            not_found_method=self.missing_last_funding_time,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_LAST_FUNDING_TIME,
        )

    def missing_last_funding_time(self, _):
        if (
            next_funding := self.formatted_record.get(
                FundingCols.NEXT_FUNDING_TIME.value
            )
        ) and self.FUNDING_TIME_UPDATE_PERIOD:
            return next_funding - self.FUNDING_TIME_UPDATE_PERIOD
        self._log_missing(
            FundingCols.LAST_FUNDING_TIME.value,
            f"{FundingCols.LAST_FUNDING_TIME.value} not found, tried to "
            f"calculate based on {FundingCols.NEXT_FUNDING_TIME.value} which is also missing",
        )
