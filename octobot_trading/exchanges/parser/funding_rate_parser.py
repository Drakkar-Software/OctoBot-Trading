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
                        funding_rates = parser.parse_funding_rate_list(raw_funding_rates)
    """
    
    FUNDING_TIME_UPDATE_PERIOD = 8 * commons_constants.HOURS_TO_SECONDS

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "funding rate"

    def parse_funding_rate_list(self, raw_funding_rates: list) -> list:
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
            self._log_missing(
                "funding rate parser broken",
                "failed to complete funding rate parser, this should "
                "never happen, check the parser code",
                error=e,
            )
        self._create_debugging_report_for_record()
        return self.formatted_record

    def _parse_timestamp(self):
        self._try_to_find_and_set(
            FundingCols.TIMESTAMP.value,
            [FundingCols.TIMESTAMP.value],
            parse_method=parser_util.convert_any_time_to_seconds,
            not_found_method=self.timestamp_not_found,
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
            [FundingCols.SYMBOL.value],
        )

    def _parse_funding_rate(self):
        self._try_to_find_and_set_decimal(
            FundingCols.FUNDING_RATE.value,
            [FundingCols.FUNDING_RATE.value] + FundingRateSynonyms.keys,
            use_info_sub_dict=True,
            allow_zero=True,
        )

    def _parse_predicted_funding_rate(self):
        self._try_to_find_and_set_decimal(
            FundingCols.PREDICTED_FUNDING_RATE.value,
            [FundingCols.PREDICTED_FUNDING_RATE.value],
            use_info_sub_dict=True,
            not_found_val=trading_constants.NaN,
            allow_zero=True,
        )

    def _parse_next_funding_time(self):
        self._try_to_find_and_set(
            FundingCols.NEXT_FUNDING_TIME.value,
            [FundingCols.NEXT_FUNDING_TIME.value] + NextFundingTimeSynonyms.keys,
            use_info_sub_dict=True,
            parse_method=parser_util.convert_any_time_to_seconds,
        )

    def _parse_last_funding_time(self):
        self._try_to_find_and_set(
            FundingCols.LAST_FUNDING_TIME.value,
            [FundingCols.LAST_FUNDING_TIME.value] + LastFundingTimeSynonyms.keys,
            parse_method=parser_util.convert_any_time_to_seconds,
            not_found_method=self.missing_last_funding_time,
            use_info_sub_dict=True,
        )

    def missing_last_funding_time(self, _):
        if next_funding := self.formatted_record.get(
            FundingCols.NEXT_FUNDING_TIME.value
        ):
            return next_funding - self.FUNDING_TIME_UPDATE_PERIOD
        self._log_missing(
            FundingCols.LAST_FUNDING_TIME.value,
            f"{FundingCols.LAST_FUNDING_TIME.value} not found, tried to "
            f"calculate based on {FundingCols.NEXT_FUNDING_TIME.value} which is also missing",
        )


class FundingRateSynonyms:
    keys = ["fundingRate"]


class NextFundingTimeSynonyms:
    keys = ["nextFundingTime"]


class LastFundingTimeSynonyms:
    keys = ["fundingTime"]
