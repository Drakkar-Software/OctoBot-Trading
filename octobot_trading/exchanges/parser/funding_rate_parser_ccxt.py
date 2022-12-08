from octobot_trading.enums import ExchangeConstantsFundingColumns as FundingCols
from octobot_trading.exchanges.parser.util import Parser
import octobot_trading.exchanges.parser.util as parser_util
from octobot_trading import constants as trading_constants
from octobot_commons import constants as commons_constants


class CCXTFundingRateParser(Parser):
    """
    override CCXTFundingRateParser class if necessary

    only include code according to ccxt standards

        parser usage:   parser = FundingRateParser(exchange)
                        funding_rate = parser.parse_funding_rate(raw_funding_rate)
                        funding_rates = parser.parse_funding_rate_list(raw_funding_rates)
    """

    TIMESTAMP_KEYS: list = [FundingCols.TIMESTAMP.value]
    SYMBOL_KEYS: list = [FundingCols.SYMBOL.value]
    FUNDING_RATE_KEYS: list = [FundingCols.FUNDING_RATE.value]
    PREDICTED_FUNDING_RATE_KEYS: list = [FundingCols.PREDICTED_FUNDING_RATE.value]
    NEXT_FUNDING_TIME_KEYS: list = [FundingCols.NEXT_FUNDING_TIME.value]
    LAST_FUNDING_TIME_KEYS: list = [FundingCols.LAST_FUNDING_TIME.value]

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "ccxt funding rate"
