import octobot_trading.constants as constants
from octobot_trading.enums import (
    ExchangeConstantsPositionColumns as PositionCols,
    TraderPositionType,
    PositionSide,
    PositionMode,
    PositionStatus,
)
import octobot_trading.exchanges.parser.util as parser_util


class PositionsParser(parser_util.Parser):
    """
    override PositionsParser if you add a parser for a non ccxt exchange

    parser usage:   parser = PositionParser(exchange)
                    positions = parser.parse_positions(raw_positions)
                    position = parser.parse_position(raw_position)

    """

    MODE_KEYS: list = []
    ONEWAY_VALUES: list = []
    HEDGE_VALUES: list = []

    SYMBOL_KEYS: list = []
    LEVERAGE_KEYS: list = []
    REALIZED_PNL_KEYS: list = []
    UNREALIZED_PNL_KEYS: list = []
    STATUS_KEYS: list = []
    LIQUIDATION_PRICE_KEYS: list = []
    BANKRUPTCY_PRICE_KEYS: list = []
    VALUE_KEYS: list = []
    ENTRY_PRICE_KEYS: list = []
    CLOSING_FEE_KEYS: list = []
    INITIAL_MARGIN_KEYS: list = []
    MARK_PRICE_KEYS: list = []
    COLLATERAL_KEYS: list = []
    MARGIN_TYPE_KEYS: list = []
    SIDE_KEYS: list = []
    CONTRACT_SIZE_KEYS: list = []
    POSITION_SIZE_KEYS: list = []
    TIMESTAMP_KEYS: list = []

    USE_INFO_SUB_DICT_FOR_SYMBOL: bool = False
    USE_INFO_SUB_DICT_FOR_POSITION_VALUE: bool = False
    USE_INFO_SUB_DICT_FOR_LEVERAGE: bool = False
    USE_INFO_SUB_DICT_FOR_REALIZED_PNL: bool = False
    USE_INFO_SUB_DICT_FOR_UNREALIZED_PNL: bool = False
    USE_INFO_SUB_DICT_FOR_STATUS: bool = False
    USE_INFO_SUB_DICT_FOR_LIQUIDATION_PRICE: bool = False
    USE_INFO_SUB_DICT_FOR_BANKRUPTCY_PRICE: bool = False
    USE_INFO_SUB_DICT_FOR_VALUE: bool = False
    USE_INFO_SUB_DICT_FOR_ENTRY_PRICE: bool = False
    USE_INFO_SUB_DICT_FOR_CLOSING_FEE: bool = False
    USE_INFO_SUB_DICT_FOR_INITIAL_MARGIN: bool = False
    USE_INFO_SUB_DICT_FOR_MARK_PRICE: bool = False
    USE_INFO_SUB_DICT_FOR_COLLATERAL: bool = False
    USE_INFO_SUB_DICT_FOR_MARGIN_TYPE: bool = False
    USE_INFO_SUB_DICT_FOR_SIDE: bool = False
    USE_INFO_SUB_DICT_FOR_CONTRACT_SIZE: bool = False
    USE_INFO_SUB_DICT_FOR_MODE: bool = False
    USE_INFO_SUB_DICT_FOR_POSITION_SIZE: bool = False
    USE_INFO_SUB_DICT_FOR_TIMESTAMP: bool = False

    STATUS_STATIC_MAP: dict = {
        PositionStatus.OPEN.value: PositionStatus.OPEN.value,
        PositionStatus.ADL.value: PositionStatus.ADL.value,
        PositionStatus.LIQUIDATING.value: PositionStatus.LIQUIDATING.value,
        PositionStatus.CLOSED.value: PositionStatus.CLOSED.value,
        PositionStatus.LIQUIDATING.value: PositionStatus.LIQUIDATING.value,
    }

    STATUS_OPEN_MAP: dict = {}
    STATUS_CLOSED_MAP: dict = {}

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "positions"

    async def parse_positions(self, raw_positions: list) -> list:
        """
        use this method to format a list of positions
        :param raw_positions: raw positions list
        :return: formatted positions list
        """
        self._ensure_list(raw_positions)
        self.formatted_records = (
            [await self.parse_position(position) for position in raw_positions]
            if self.raw_records
            else []
        )
        self._create_debugging_report()
        return self.formatted_records

    async def parse_position(self, raw_position: dict) -> dict:
        """
        use this method to format a single position
        :param raw_position: raw position dict with eventually missing data
        :return: formatted position dict
        """
        self._ensure_dict(raw_position)
        try:
            self._parse_symbol()
            self._parse_original_side()
            self._parse_position_mode()
            self._parse_side()
            self._parse_position_size()
            self._parse_contract_type()
            self._parse_margin_type()
            self._parse_leverage()
            self._parse_realized_pnl()
            self._parse_contract_size()
            self._parse_status()
            if self.exchange.CONNECTOR_CONFIG.MARK_PRICE_IN_POSITION:
                await self._parse_mark_price()
            if (
                self.formatted_record[PositionCols.STATUS.value]
                == PositionStatus.CLOSED
            ):
                # todo check what is required for empty
                # partially parse empty position as we might need it to create contracts
                self._create_debugging_report_for_record()
                return self.formatted_record
            self._parse_timestamp()
            self._parse_collateral()
            self._parse_unrealized_pnl()
            self._parse_liquidation_price()
            self._parse_closing_fee()
            self._parse_value()  # parse after mark_price and quantity
            self._parse_initial_margin()
            self._parse_entry_price()
        except Exception as e:
            # just in case something bad happens
            # this should never happen, check the parser code
            self._log_missing(
                "failed to parse positions",
                "not able to complete positions parser",
                error=e,
            )
        self._create_debugging_report_for_record()
        return self.formatted_record

    def _parse_position_mode(self):
        """
        define self.ONEWAY_VALUES and self.HEDGE_VALUES and self.MODE_KEYS
        to adapt to a new exchange
        """
        if self.ONEWAY_VALUES and self.HEDGE_VALUES and self.MODE_KEYS:
            self._try_to_find_and_set(
                PositionCols.POSITION_MODE.value,
                self.MODE_KEYS,
                parse_method=self.mode_found,
                use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_MODE,
                allowed_falsely_values=(False,),
            )
        else:
            self._log_missing(
                PositionCols.POSITION_MODE.value, "not implemented for this exchange"
            )

    def mode_found(self, raw_mode):
        if raw_mode in self.ONEWAY_VALUES:
            return PositionMode.ONE_WAY
        if raw_mode in self.HEDGE_VALUES:
            return PositionMode.HEDGE
        self._log_missing(
            PositionCols.POSITION_MODE.value,
            f"key: {self.MODE_KEYS}, "
            f"got raw_mode: {raw_mode or 'no raw mode'}, "
            f"allowed oneway values: {self.ONEWAY_VALUES}, "
            f"allowed hedge values: {self.HEDGE_VALUES}",
        )

    def _parse_symbol(self):
        # check is get_pair_from_exchange required? isn't ccxt already doing this?
        self._try_to_find_and_set(
            PositionCols.SYMBOL.value,
            self.SYMBOL_KEYS,
            parse_method=self.exchange.get_pair_from_exchange,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_SYMBOL,
        )

    def _parse_leverage(self):
        self._try_to_find_and_set_decimal(
            PositionCols.LEVERAGE.value,
            self.LEVERAGE_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_LEVERAGE,
        )

    def _parse_realized_pnl(self):
        self._try_to_find_and_set_decimal(
            PositionCols.REALIZED_PNL.value,
            self.REALIZED_PNL_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_REALIZED_PNL,
            allow_zero=True,
        )

    def _parse_unrealized_pnl(self):
        self._try_to_find_and_set_decimal(
            PositionCols.UNREALIZED_PNL.value,
            self.UNREALIZED_PNL_KEYS,
            allow_zero=True,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_UNREALIZED_PNL,
        )

    def _parse_status(self):
        self._try_to_find_and_set(
            PositionCols.STATUS.value,
            self.STATUS_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_STATUS,
            parse_method=self._status_found,
            not_found_method=self._missing_status,
        )

    def _status_found(self, raw_status):
        try:
            return PositionStatus(self.STATUS_STATIC_MAP[raw_status])
        except (KeyError, ValueError):
            try:
                if self.formatted_record.get(PositionCols.POSITION_SIZE.value):
                    return PositionStatus(self.STATUS_OPEN_MAP[raw_status])
                else:
                    return PositionStatus(self.STATUS_CLOSED_MAP[raw_status])
            except (KeyError, ValueError):
                return self._missing_status(None)

    def _missing_status(self, _):
        if size := self.formatted_record.get(PositionCols.POSITION_SIZE.value):
            if size > 0 or size < 0:
                return PositionStatus.OPEN
        if size == constants.ZERO:
            return PositionStatus.CLOSED
        self._log_missing(
            PositionCols.STATUS.value,
            f"not found and also not able to set based on a valid size ({size or 'no size'}) is required to parse status",
        )

    def _parse_liquidation_price(self):
        self._try_to_find_and_set_decimal(
            PositionCols.LIQUIDATION_PRICE.value,
            self.LIQUIDATION_PRICE_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_LIQUIDATION_PRICE,
        )

    def _parse_bankruptcy_price(self):
        self._try_to_find_and_set_decimal(
            PositionCols.BANKRUPTCY_PRICE.value,
            self.BANKRUPTCY_PRICE_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_BANKRUPTCY_PRICE,
            enable_log=False,
        )

    def _parse_value(self):
        self._try_to_find_and_set_decimal(
            PositionCols.POSITION_VALUE.value,
            self.VALUE_KEYS,
            not_found_method=self._missing_value,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_VALUE,
        )

    def _missing_value(self, _):
        size = mark_price = quantity = None
        if (size := self.formatted_record.get(PositionCols.POSITION_SIZE.value)) and (
            quantity := self.formatted_record.get(PositionCols.CONTRACT_SIZE.value)
        ):
            if not (
                mark_price := self.formatted_record.get(PositionCols.MARK_PRICE.value)
            ):
                mark_price = None  # add get and wait for mark price from channel
            if mark_price:
                return size * quantity * mark_price
        self._log_missing(
            PositionCols.POSITION_VALUE.value,
            f"keys: {self.VALUE_KEYS} and using size ({size or 'no size'}) "
            f"* contract_size ({quantity or 'no quantity'}) "
            f"* mark price ({mark_price or 'no mark price'})",
        )

    def _parse_entry_price(self):
        self._try_to_find_and_set_decimal(
            PositionCols.ENTRY_PRICE.value, self.ENTRY_PRICE_KEYS
        )

    def _parse_closing_fee(self):
        # optional
        self._try_to_find_and_set_decimal(
            PositionCols.CLOSING_FEE.value,
            self.CLOSING_FEE_KEYS,
            enable_log=False,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_CLOSING_FEE,
        )

    def _parse_initial_margin(self):
        self._try_to_find_and_set_decimal(
            PositionCols.INITIAL_MARGIN.value,
            self.COLLATERAL_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_INITIAL_MARGIN,
        )

    async def _parse_mark_price(self):
        self._try_to_find_and_set_decimal(
            PositionCols.MARK_PRICE.value,
            self.MARK_PRICE_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_MARK_PRICE,
        )

    def _parse_collateral(self):
        self._try_to_find_and_set_decimal(
            PositionCols.COLLATERAL.value,
            self.COLLATERAL_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_COLLATERAL,
        )

    def _parse_margin_type(self):
        self._try_to_find_and_set(
            PositionCols.MARGIN_TYPE.value,
            self.MARGIN_TYPE_KEYS,
            parse_method=TraderPositionType,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_MARGIN_TYPE,
        )

    def _parse_original_side(self):
        self._try_to_find_and_set(
            PositionCols.ORIGINAL_SIDE.value,
            self.SIDE_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_SIDE,
        )

    def _parse_side(self):
        if (
            mode := self.formatted_record.get(PositionCols.POSITION_MODE.value)
        ) is PositionMode.ONE_WAY:
            self.formatted_record[PositionCols.SIDE.value] = PositionSide.BOTH
        elif mode is PositionMode.HEDGE:
            if (
                original_side := self.formatted_record.get(
                    PositionCols.ORIGINAL_SIDE.value
                )
            ) == PositionSide.LONG.value:
                self.formatted_record[PositionCols.SIDE.value] = PositionSide.LONG
            elif original_side == PositionSide.SHORT.value:
                self.formatted_record[PositionCols.SIDE.value] = PositionSide.SHORT
            else:
                self._log_missing(
                    PositionCols.SIDE.value,
                    "position original side is required to parse side",
                )
        else:
            self._log_missing(
                PositionCols.SIDE.value, "position mode is required to parse side"
            )

    def _parse_position_size(self):
        self._try_to_find_and_set_decimal(
            PositionCols.POSITION_SIZE.value,
            self.POSITION_SIZE_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_POSITION_SIZE,
            parse_method=self.size_found,
            allow_zero=True,
        )

    def size_found(self, quantity):
        if quantity == constants.ZERO:
            return quantity
        if side := self.formatted_record.get(PositionCols.ORIGINAL_SIDE.value):
            if side == PositionSide.LONG.value:
                return quantity
            elif side == PositionSide.SHORT.value:
                # short - so we set it to negative if it isn't already
                return -quantity if quantity > 0 else quantity
        self._log_missing(
            PositionCols.POSITION_SIZE.value,
            f"requires valid side ({side or 'no side'}) to parse",
        )

    def _parse_contract_size(self):
        """
        quantity is the size for a single contract
        """
        self._try_to_find_and_set_decimal(
            PositionCols.CONTRACT_SIZE.value,
            self.CONTRACT_SIZE_KEYS,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_CONTRACT_SIZE,
        )

    def _parse_contract_type(self):
        if symbol := self.formatted_record.get(PositionCols.SYMBOL.value):
            try:
                self.formatted_record[
                    PositionCols.CONTRACT_TYPE.value
                ] = self.exchange.get_contract_type(symbol)
            except Exception as e:
                self._log_missing(
                    PositionCols.CONTRACT_TYPE.value,
                    f"Failed to get contract type with symbol: " f"{symbol}",
                    error=e,
                )
        else:
            self._log_missing(
                PositionCols.CONTRACT_TYPE.value,
                "symbol is required to parse contract type",
            )

    def _parse_timestamp(self):
        self._try_to_find_and_set(
            PositionCols.TIMESTAMP.value,
            self.TIMESTAMP_KEYS,
            parse_method=parser_util.convert_any_time_to_seconds,
            not_found_method=self.timestamp_not_found,
            use_info_sub_dict=self.USE_INFO_SUB_DICT_FOR_TIMESTAMP,
        )

    def timestamp_not_found(self, _):
        try:
            return int(self.exchange.connector.get_exchange_current_time())
        except Exception as e:
            self._log_missing(
                PositionCols.CONTRACT_TYPE.value,
                f"Failed to get time with get_exchange_current_time: "
                f"{self.formatted_record[PositionCols.SYMBOL.value]}",
                error=e,
            )
