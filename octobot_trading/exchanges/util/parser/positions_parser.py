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
from .util import Parser


class PositionsParser(Parser):
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
        self.ONEWAY_VALUES: tuple = False
        self.HEDGE_VALUES: tuple = True

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
        if self.formatted_record[PositioCols.SIZE.value] == constants.ZERO:
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
        await self._parse_mark_price()
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

            def mode_found(raw_mode):
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

            self._try_to_find_and_parse_with_method(
                PositioCols.POSITION_MODE.value,
                self.MODE_KEY_NAMES,
                parse_method=mode_found,
                use_info_sub_dict=True,
            )
        else:
            self._log_missing(
                PositioCols.POSITION_MODE.value, "not implemented for this exchange"
            )

    def _parse_symbol(self):
        # check is get_pair_from_exchange required? isn't ccxt already doing this?
        self._try_to_find_and_parse_with_method(
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
        def missing_realized():
            pass
        self._try_to_find_and_set_decimal(
            PositioCols.REALISED_PNL.value,
            [ExchangeCols.REALISED_PNL.value, BYBIT_REALIZED_PNL],
            not_found_val=0,
            use_info_sub_dict=True,
            enable_log=False, # it's optional
        )

    def _parse_unrealized_pnl(self):
        self._try_to_find_and_set_decimal(
            PositioCols.UNREALIZED_PNL.value, [ExchangeCols.UNREALISED_PNL.value]
        )

    def _parse_status(self):
        # todo improve - add LIQUIDATING, LIQUIDATED and ADL
        size = self.formatted_record.get(PositioCols.SIZE.value)
        try:
            if size >= 0:
                self.formatted_record[PositioCols.STATUS.value] = PositionStatus.OPEN
            else:
                self.formatted_record[PositioCols.STATUS.value] = PositionStatus.CLOSED
        except Exception as e:
            self._log_missing(
                PositioCols.SIZE.value,
                f"a valid size ({size or 'no size'}) is required to parse status, error: {e}",
            )

    def _parse_liquidation_price(self):
        # todo is liquidation price different as bankruptcy price? merge?
        self._try_to_find_and_set_decimal(
            PositioCols.LIQUIDATION_PRICE.value,
            [ExchangeCols.LIQUIDATION_PRICE.value, BYBIT_BANKRUPTCY_PRICE],
        )

    def _parse_value(self):
        keys_to_find = [PositioCols.VALUE.value, BYBIT_VALUE]

        def missing_value():
            if (
                mark_price := self.formatted_record.get(PositioCols.MARK_PRICE.value)
            ) and (quantity := self.formatted_record.get(PositioCols.QUANTITY.value)):
                return quantity / mark_price
            self._log_missing(
                PositioCols.VALUE.value,
                f"keys: {keys_to_find} "
                f"and using quantity ({quantity or 'no quantity'}) "
                f"/ mark price ({mark_price or 'no mark price'})",
            )

        self._try_to_find_and_set_decimal(
            PositioCols.VALUE.value,
            keys_to_find,
            not_found_method=missing_value,
            use_info_sub_dict=True,
            enable_log=False,
        )

    def _parse_entry_price(self):
        self._try_to_find_and_set_decimal(
            PositioCols.ENTRY_PRICE.value, [ExchangeCols.ENTRY_PRICE.value]
        )

    def _parse_closing_fee(self):
        # optional
        self._try_to_find_and_set_decimal(
            PositioCols.CLOSING_FEE.value,
            [BYBIT_CLOSING_FEE],
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
            enable_log=False,
        )
        if not self.formatted_record[PositioCols.MARK_PRICE.value]:
            error_message = ""
            if symbol := self.formatted_record[PositioCols.SYMBOL.value]:
                try:
                    # todo replace with get_mark_price
                    kline_data = await self.exchange.get_kline_price(
                        symbol, commons_enums.TimeFrames.ONE_MINUTE
                    )
                    try:
                        self.formatted_record[
                            PositioCols.MARK_PRICE.value
                        ] = decimal.Decimal(str(kline_data[0][4]))
                        return
                    except KeyError:
                        self._log_missing(
                            PositioCols.MARK_PRICE.value,
                            f"key: {PositioCols.MARK_PRICE.value} and using get_kline_price "
                            "(malformed kline data: {kline_data or 'no kline data'})",
                        )
                except Exception as e:
                    error_message = f", error: {e}"
            self._log_missing(
                PositioCols.MARK_PRICE.value,
                f"key: {PositioCols.MARK_PRICE.value} and using get_kline_price{error_message}",
            )

    def _parse_collateral(self):
        self._try_to_find_and_set_decimal(
            PositioCols.COLLATERAL.value, [ExchangeCols.COLLATERAL.value]
        )

    def _parse_margin_type(self):
        self._try_to_find_and_parse_with_method(
            PositioCols.MARGIN_TYPE.value,
            [ExchangeCols.MARGIN_TYPE.value, ExchangeCols.MARGIN_MODE.value],
            parse_method=TraderPositionType,
            not_found_val=TraderPositionType.CROSS,
        )

    def _parse_original_side(self):
        self._try_to_find_and_set(
            PositioCols.ORIGINAL_SIDE.value,
            [ExchangeCols.SIDE.value, BINANCE_POSITION_TYPE],
        )

    def _parse_side(self):
        if (
            self.formatted_record.get(PositioCols.POSITION_MODE.value)
            is PositionMode.ONE_WAY
        ):
            # todo is it good to keep it like that in ONE_WAY mode?
            self.formatted_record[PositioCols.SIDE.value] = PositionSide.BOTH
        else:
            self.formatted_record[PositioCols.SIDE.value] = (
                PositionSide.LONG
                if self.formatted_record.get(PositioCols.ORIGINAL_SIDE.value)
                == PositionSide.LONG.value
                else PositionSide.SHORT
            )

    def _parse_size(self):
        def size_found(_size):
            if (
                self.formatted_record[PositioCols.SIDE.value] == PositionSide.LONG
                or self.formatted_record[PositioCols.SIDE.value] == PositionSide.BOTH
            ):
                return _size
            # short - so we set it to negative if it isn't already
            return -_size if _size > 0 else _size

        self._try_to_find_and_set_decimal(
            PositioCols.SIZE.value,
            [ExchangeCols.CONTRACTS.value, BINANCE_QUANTITY],
            parse_method=size_found,
            not_found_val=constants.ZERO,
        )

    def _parse_quantity(self):
        self._try_to_find_and_set_decimal(
            PositioCols.QUANTITY.value, [ExchangeCols.CONTRACT_SIZE.value]
        )

    def _parse_contract_type(self):
        try:
            self.formatted_record[
                PositioCols.CONTRACT_TYPE.value
            ] = self.exchange.get_contract_type(
                self.formatted_record[PositioCols.SYMBOL.value]
            )
        except Exception as e:
            self.exchange.logger.error(
                f"Failed to parse position attribute: contract type with symbol: "
                f"{self.formatted_record[PositioCols.SYMBOL.value]}"
                f"with get_contract_type - error: {e}"
            )

    def _parse_timestamp(self):
        def timestamp_not_found():
            try:
                return int(self.exchange.connector.get_exchange_current_time())
            except Exception as e:
                self.exchange.logger.error(
                    f"Failed to parse position attribute: timestamp - "
                    f"with get_exchange_current_time - error: {e}"
                )

        self._try_to_find_and_parse_with_method(
            PositioCols.TIMESTAMP.value,
            [ExchangeCols.TIMESTAMP.value],
            int,
            not_found_method=timestamp_not_found,
        )


# keep keys here from exchanges that are 100% safe
BYBIT_BANKRUPTCY_PRICE = "bust_price"
BYBIT_REALIZED_PNL = "cum_realized_pnl"
BYBIT_CLOSING_FEE = "occ_closing_fee"
BYBIT_VALUE = "position_value"

BINANCE_POSITION_TYPE = "positionSide"
BINANCE_QUANTITY = "positionAmt"
