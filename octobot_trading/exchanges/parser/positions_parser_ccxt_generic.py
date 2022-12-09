from octobot_trading.enums import (
    ExchangeConstantsPositionColumns as PositionCols,
    ExchangePositionCCXTColumns as ExchangeCols,
    PositionStatus,
    ExchangeConstantsMarkPriceColumns as MarkPriceCols,
)
import octobot_trading.exchanges.parser.positions_parser_ccxt as positions_parser_ccxt


class GenericCCXTPositionsParser(positions_parser_ccxt.CCXTPositionsParser):
    """
    dont override this method, use CCXTPositionsParser as a base instead

    only include code that is safe for any ccxt exchange

    parser usage:   parser = GenericCCXTPositionsParser(exchange)
                    positions = parser.parse_positions(raw_positions)
                    position = parser.parse_position(raw_position)

    """

    MODE_KEYS: list = ["hedged"]
    ONEWAY_VALUES: list = [False]
    HEDGE_VALUES: list = [True]

    REALIZED_PNL_KEYS: list = [
        ExchangeCols.REALIZED_PNL.value,
        "cum_realized_pnl",
        "realized_pnl",
        "cum_realised_pnl",
        "realised_pnl",
        "realisedPnl",
    ]
    UNREALIZED_PNL_KEYS: list = [ExchangeCols.UNREALIZED_PNL.value, "unrealizedPnl"]
    STATUS_KEYS: list = ["position_status"]
    BANKRUPTCY_PRICE_KEYS: list = ["bust_price"]
    VALUE_KEYS: list = [ExchangeCols.NOTIONAL.value, "position_value"]
    CLOSING_FEE_KEYS: list = ["occ_closing_fee"]
    MARGIN_TYPE_KEYS: list = [
        ExchangeCols.MARGIN_MODE.value,
        ExchangeCols.MARGIN_TYPE.value,
        PositionCols.MARGIN_TYPE.value,
    ]
    SIDE_KEYS: list = [ExchangeCols.SIDE.value, "positionSide"]
    POSITION_SIZE_KEYS: list = [ExchangeCols.CONTRACTS.value, "positionAmt"]
    MARK_PRICE_KEYS: list = [
        ExchangeCols.MARK_PRICE.value,
        MarkPriceCols.MARK_PRICE.value,
    ]

    USE_INFO_SUB_DICT_FOR_REALIZED_PNL: bool = True
    USE_INFO_SUB_DICT_FOR_UNREALIZED_PNL: bool = True
    USE_INFO_SUB_DICT_FOR_STATUS: bool = True
    USE_INFO_SUB_DICT_FOR_BANKRUPTCY_PRICE: bool = True
    USE_INFO_SUB_DICT_FOR_VALUE: bool = True
    USE_INFO_SUB_DICT_FOR_CLOSING_FEE: bool = True
    USE_INFO_SUB_DICT_FOR_MARGIN_TYPE: bool = True
    USE_INFO_SUB_DICT_FOR_SIDE: bool = True
    USE_INFO_SUB_DICT_FOR_POSITION_SIZE: bool = True
    USE_INFO_SUB_DICT_FOR_MODE: bool = True
    USE_INFO_SUB_DICT_FOR_MARK_PRICE: bool = True

    STATUS_STATIC_MAP: dict = {
        PositionStatus.OPEN.value: PositionStatus.OPEN.value,
        PositionStatus.ADL.value: PositionStatus.ADL.value,
        PositionStatus.LIQUIDATING.value: PositionStatus.LIQUIDATING.value,
        PositionStatus.CLOSED.value: PositionStatus.CLOSED.value,
        PositionStatus.LIQUIDATING.value: PositionStatus.LIQUIDATING.value,
        "Liq": PositionStatus.LIQUIDATING.value,
        "Adl": PositionStatus.ADL.value,
    }

    STATUS_OPEN_MAP: dict = {
        "Normal": PositionStatus.OPEN.value,
    }
    STATUS_CLOSED_MAP: dict = {
        "Normal": PositionStatus.CLOSED.value,
    }

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "generic positions"
