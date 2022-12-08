from octobot_trading.enums import (
    ExchangePositionCCXTColumns as ExchangeCols,
)
from octobot_trading.exchanges.parser import positions_parser


class CCXTPositionsParser(positions_parser.PositionsParser):
    """
    overwrite CCXTPositionsParser class methods if necessary

    only include code according to ccxt standards

    parser usage:   parser = PositionParser(exchange)
                    positions = parser.parse_positions(raw_positions)
                    position = parser.parse_position(raw_position)

    """

    MODE_KEYS: list = []
    ONEWAY_VALUES: list = []
    HEDGE_VALUES: list = []

    SYMBOL_KEYS: list = [ExchangeCols.SYMBOL.value]
    NOTIONAL_KEYS: list = [ExchangeCols.NOTIONAL.value]
    LEVERAGE_KEYS: list = [ExchangeCols.LEVERAGE.value]
    REALIZED_PNL_KEYS: list = [ExchangeCols.REALIZED_PNL.value]
    UNREALIZED_PNL_KEYS: list = [ExchangeCols.UNREALIZED_PNL.value]
    STATUS_KEYS: list = []
    LIQUIDATION_PRICE_KEYS: list = [ExchangeCols.LIQUIDATION_PRICE.value]
    BANKRUPTCY_PRICE_KEYS: list = []
    VALUE_KEYS: list = []
    ENTRY_PRICE_KEYS: list = [ExchangeCols.ENTRY_PRICE.value]
    CLOSING_FEE_KEYS: list = []
    INITIAL_MARGIN_KEYS: list = [ExchangeCols.INITIAL_MARGIN.value]
    MARK_PRICE_KEYS: list = [ExchangeCols.MARK_PRICE.value]
    COLLATERAL_KEYS: list = [ExchangeCols.COLLATERAL.value]
    MARGIN_TYPE_KEYS: list = [
        ExchangeCols.MARGIN_MODE.value,
        ExchangeCols.MARGIN_TYPE.value,
    ]
    SIDE_KEYS: list = [ExchangeCols.SIDE.value]
    QUANTITY_KEYS: list = [ExchangeCols.CONTRACT_SIZE.value]
    SIZE_KEYS: list = [ExchangeCols.CONTRACTS.value]
    TIMESTAMP_KEYS: list = [ExchangeCols.TIMESTAMP.value]

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "ccxt positions"
