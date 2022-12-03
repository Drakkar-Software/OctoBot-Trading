import decimal
import octobot_commons.enums as commons_enums
import octobot_trading.constants as constants
from octobot_trading.enums import (
    ExchangeConstantsPositionColumns as PositioCols,
    ExchangePositionCCXTColumns as ExchangeCols,
    TraderPositionType,
    PositionSide,
    PositionMode,
    PositionStatus,
)
import octobot_trading.exchanges.parser.util as parser_util


class PositionsParser(parser_util.Parser):
    """
    overwrite PositionsParser class methods if necessary
    always/only include bulletproof custom code into the parser to improve generic support

    parser usage:   parser = PositionParser(exchange)
                    positions = parser.parse_positions(raw_positions)
                    position = parser.parse_position(raw_position)

    """

    def __init__(self, exchange):
        super().__init__(exchange=exchange)
        self.PARSER_TITLE = "positions"

        self.MODE_KEY_NAMES: list = ["hedged"]
        self.ONEWAY_VALUES: tuple = (False,)
        self.HEDGE_VALUES: tuple = (True,)

    async def parse_positions(self, raw_positions: list) -> list:
        """
        use this method to format a list of positions
        :param raw_positions: raw positions list
        :return: formatted positions list
        """
        # todo remove duplicates as we try to get positions from different endpoints
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
        self._parse_symbol()
        self._parse_original_side()
        self._parse_position_mode()
        self._parse_side()
        self._parse_size()
        self._parse_contract_type()
        self._parse_margin_type()
        self._parse_leverage()
        self._parse_realized_pnl()
        self._parse_status()
        if self.exchange.CONNECTOR_CONFIG.MARK_PRICE_IN_POSITION:
            await self._parse_mark_price()
        if self.formatted_record[PositioCols.STATUS.value] == PositionStatus.CLOSED:
            # todo check what is required for empty
            # partially parse empty position as we might need it to create contracts
            self._create_debugging_report_for_record()
            return self.formatted_record
        self._parse_quantity()
        self._parse_timestamp()
        self._parse_collateral()
        self._parse_notional()
        self._parse_unrealized_pnl()
        self._parse_liquidation_price()
        self._parse_closing_fee()
        self._parse_value()  # parse after mark_price and quantity
        self._parse_initial_margin()
        self._parse_entry_price()

        self._create_debugging_report_for_record()
        return self.formatted_record

    def _parse_position_mode(self):
        """
        define self.ONEWAY_VALUES and self.HEDGE_VALUES and self.MODE_KEY_NAMES
        to adapt to a new exchange
        """
        if self.ONEWAY_VALUES and self.HEDGE_VALUES and self.MODE_KEY_NAMES:
            self._try_to_find_and_set(
                PositioCols.POSITION_MODE.value,
                self.MODE_KEY_NAMES,
                parse_method=self.mode_found,
                use_info_sub_dict=True,
                allowed_falsely_values=(False,),
            )
        else:
            self._log_missing(
                PositioCols.POSITION_MODE.value, "not implemented for this exchange"
            )

    def _parse_symbol(self):
        # check is get_pair_from_exchange required? isn't ccxt already doing this?
        self._try_to_find_and_set(
            PositioCols.SYMBOL.value,
            [ExchangeCols.SYMBOL.value],
            parse_method=self.exchange.get_pair_from_exchange,
        )

    def _parse_notional(self):
        self._try_to_find_and_set_decimal(
            PositioCols.NOTIONAL.value, [ExchangeCols.NOTIONAL.value]
        )

    def _parse_leverage(self):
        self._try_to_find_and_set_decimal(
            PositioCols.LEVERAGE.value, [ExchangeCols.LEVERAGE.value]
        )

    def _parse_realized_pnl(self):
        self._try_to_find_and_set_decimal(
            PositioCols.REALIZED_PNL.value,
            [ExchangeCols.REALIZED_PNL.value] + RealizedPnlSynonyms.keys,
            use_info_sub_dict=True,
            allow_zero=True,
        )

    def _parse_unrealized_pnl(self):
        self._try_to_find_and_set_decimal(
            PositioCols.UNREALIZED_PNL.value,
            [ExchangeCols.UNREALIZED_PNL.value] + UnrealizedPnlSynonyms.keys,
            allow_zero=True,
        )

    def _parse_status(self):
        # todo improve - add LIQUIDATING, LIQUIDATED and ADL
        if size := self.formatted_record.get(PositioCols.SIZE.value):
            if size > 0 or size < 0:
                self.formatted_record[PositioCols.STATUS.value] = PositionStatus.OPEN
                return
        if size == constants.ZERO:
            self.formatted_record[PositioCols.STATUS.value] = PositionStatus.CLOSED
            return
        self._log_missing(
            PositioCols.STATUS.value,
            f"a valid size ({size or 'no size'}) is required to parse status",
        )

    def _parse_liquidation_price(self):
        self._try_to_find_and_set_decimal(
            PositioCols.LIQUIDATION_PRICE.value,
            [ExchangeCols.LIQUIDATION_PRICE.value] + LiquidationSynonyms.keys,
            use_info_sub_dict=True,
        )

    def _parse_value(self):
        keys_to_find = [PositioCols.VALUE.value] + ValueSynonyms.keys

        def missing_value(_):
            self.handle_missing_value(keys_to_find)

        self._try_to_find_and_set_decimal(
            PositioCols.VALUE.value,
            keys_to_find,
            not_found_method=missing_value,
            use_info_sub_dict=True,
        )

    def _parse_entry_price(self):
        self._try_to_find_and_set_decimal(
            PositioCols.ENTRY_PRICE.value, [ExchangeCols.ENTRY_PRICE.value]
        )

    def _parse_closing_fee(self):
        # optional
        self._try_to_find_and_set_decimal(
            PositioCols.CLOSING_FEE.value,
            ClosingFeeSynonyms.keys,
            enable_log=False,
            use_info_sub_dict=True,
        )

    def _parse_initial_margin(self):
        self._try_to_find_and_set_decimal(
            PositioCols.INITIAL_MARGIN.value, [ExchangeCols.COLLATERAL.value]
        )

    async def _parse_mark_price(self):
        self._try_to_find_and_set_decimal(
            PositioCols.MARK_PRICE.value,
            [ExchangeCols.MARK_PRICE.value],
        )

    def _parse_collateral(self):
        self._try_to_find_and_set_decimal(
            PositioCols.COLLATERAL.value, [ExchangeCols.COLLATERAL.value]
        )

    def _parse_margin_type(self):
        self._try_to_find_and_set(
            PositioCols.MARGIN_TYPE.value,
            [ExchangeCols.MARGIN_TYPE.value, ExchangeCols.MARGIN_MODE.value],
            parse_method=TraderPositionType,
        )

    def _parse_original_side(self):
        self._try_to_find_and_set(
            PositioCols.ORIGINAL_SIDE.value,
            [ExchangeCols.SIDE.value, SideSynonyms.keys],
            use_info_sub_dict=True,
        )

    def _parse_side(self):
        if (
            mode := self.formatted_record.get(PositioCols.POSITION_MODE.value)
        ) is PositionMode.ONE_WAY:
            self.formatted_record[PositioCols.SIDE.value] = PositionSide.BOTH
        elif mode is PositionMode.HEDGE:
            if (
                original_side := self.formatted_record.get(
                    PositioCols.ORIGINAL_SIDE.value
                )
            ) == PositionSide.LONG.value:
                self.formatted_record[PositioCols.SIDE.value] = PositionSide.LONG
            elif original_side == PositionSide.SHORT.value:
                self.formatted_record[PositioCols.SIDE.value] = PositionSide.SHORT
            else:
                self._log_missing(
                    PositioCols.SIDE.value,
                    "position original side is required to parse side",
                )
        else:
            self._log_missing(
                PositioCols.SIDE.value, "position mode is required to parse side"
            )

    def _parse_size(self):
        self._try_to_find_and_set_decimal(
            PositioCols.SIZE.value,
            SizeSynonyms.keys,
            use_info_sub_dict=True,
            allow_zero=True,
        )

    def _parse_quantity(self):
        """
        quantity is the size for a single contract
        """
        self._try_to_find_and_set_decimal(
            PositioCols.QUANTITY.value,
            QuantitySynonyms.keys,
            parse_method=self.quantity_found,
            use_info_sub_dict=True,
        )

    def _parse_contract_type(self):
        if symbol := self.formatted_record.get(PositioCols.SYMBOL.value):
            try:
                self.formatted_record[
                    PositioCols.CONTRACT_TYPE.value
                ] = self.exchange.get_contract_type(symbol)
            except Exception as e:
                self._log_missing(
                    PositioCols.CONTRACT_TYPE.value,
                    f"Failed to get contract type with symbol: " f"{symbol}",
                    error=e,
                )
        else:
            self._log_missing(
                PositioCols.CONTRACT_TYPE.value,
                "symbol is required to parse contract type",
            )

    def _parse_timestamp(self):
        self._try_to_find_and_set(
            PositioCols.TIMESTAMP.value,
            [ExchangeCols.TIMESTAMP.value],
            parse_method=parser_util.convert_any_time_to_seconds,
            not_found_method=self.timestamp_not_found,
        )

    def mode_found(self, raw_mode):
        if raw_mode in self.ONEWAY_VALUES:
            return PositionMode.ONE_WAY
        if raw_mode in self.HEDGE_VALUES:
            return PositionMode.HEDGE
        self._log_missing(
            PositioCols.POSITION_MODE.value,
            f"key: {self.MODE_KEY_NAMES}, "
            f"got raw_mode: {raw_mode or 'no raw mode'}, "
            f"allowed oneway values: {self.ONEWAY_VALUES}, "
            f"allowed hedge values: {self.HEDGE_VALUES}",
        )

    def handle_missing_value(self, keys_to_find):
        quantity = None
        if (mark_price := self.formatted_record.get(PositioCols.MARK_PRICE.value)) and (
            quantity := self.formatted_record.get(PositioCols.QUANTITY.value)
        ):
            return quantity / mark_price
        self._log_missing(
            PositioCols.VALUE.value,
            f"keys: {keys_to_find} and using quantity ({quantity or 'no quantity'}) "
            f"/ mark price ({mark_price or 'no mark price'})",
        )

    def quantity_found(self, quantity):
        if quantity == constants.ZERO:
            return quantity
        if side := self.formatted_record.get(PositioCols.ORIGINAL_SIDE.value):
            if side == PositionSide.LONG.value:
                return quantity
            elif side == PositionSide.SHORT.value:
                # short - so we set it to negative if it isn't already
                return -quantity if quantity > 0 else quantity
        self._log_missing(
            PositioCols.QUANTITY.value,
            f"requires valid side ({side or 'no side'}) to parse",
        )

    def timestamp_not_found(self, _):
        try:
            return int(self.exchange.connector.get_exchange_current_time())
        except Exception as e:
            self._log_missing(
                PositioCols.CONTRACT_TYPE.value,
                f"Failed to get time with get_exchange_current_time: "
                f"{self.formatted_record[PositioCols.SYMBOL.value]}",
                error=e,
            )


# only keep keys here from exchanges that are 100% safe with any exchange
class LiquidationSynonyms:
    keys = ["bust_price"]


class RealizedPnlSynonyms:
    keys = [
        "cum_realized_pnl",
        "realized_pnl",
        "cum_realised_pnl",
        "realised_pnl",
        "realisedPnl",
    ]


class UnrealizedPnlSynonyms:
    keys = ["unrealizedPnl"]


class ClosingFeeSynonyms:
    keys = ["occ_closing_fee"]


class ValueSynonyms:
    keys = ["position_value"]


class SizeSynonyms:
    keys = [ExchangeCols.CONTRACTS.value, "positionAmt"]


class QuantitySynonyms:
    keys = [ExchangeCols.CONTRACT_SIZE.value]


class SideSynonyms:
    keys = ["positionSide"]
