import datetime
import decimal
import octobot_commons.timestamp_util as timestamp_util
import octobot_trading.constants as trading_constants
import octobot_trading.enums as enums
import octobot_trading.exchanges.parser.parser_reporter as parser_reporter


class Parser:
    """
    Use Parser as a base if you implement a new parser.
    see OrdersParser as an example
    """

    def __init__(self, exchange, parser_type_name: str):
        self.PARSER_TITLE = self.__class__.__name__
        self.PARSER_TYPE_NAME = (
            parser_type_name  # example for ccxt position parse:  "position"
        )
        self.REQUIRED_FIELDS = []  # keys that need to be in the formatted record
        self.NON_EMPTY_FIELDS = []  # keys that can't be empty in the formatted record

        self.raw_records = {}
        self.exchange = exchange
        self.raw_record = {}
        self.formatted_record = {}
        self.formatted_records = []
        self.multiple_records = False
        self.reporter: parser_reporter.ParserReporter = parser_reporter.ParserReporter(
            exchange.logger, self.PARSER_TITLE, parser_type_name
        )

    def _ensure_details_completeness(self):
        # ensure all REQUIRED_FIELDS are present and all NON_EMPTY_FIELDS are not empty

        return all(
            key in self.formatted_record for key in self.REQUIRED_FIELDS
        ) and all(self.formatted_record[key] for key in self.NON_EMPTY_FIELDS)

    def _log_missing(
        self,
        key_to_set: str,
        error_description: str,
        additional_message: str = "",
        error=None,
        method=None,
    ):
        self.reporter.add_to_debugging_report(
            key_to_set=key_to_set,
            error_description=error_description,
            additional_message=additional_message,
            method=method,
            error=error,
        )

    def _try_to_find_and_set(
        self,
        key_to_set: str,
        keys_to_test: list,
        parse_method=None,
        not_found_val=None,
        not_found_method=None,
        enable_log: bool = True,
        use_dict_root: bool = True,
        use_info_sub_dict: bool = False,
        allowed_falsely_values: tuple = (),
    ) -> bool:
        if (
            value := self._try_to_find(
                key_to_set=key_to_set,
                keys_to_test=keys_to_test,
                not_found_val=not_found_val,
                enable_log=False,
                use_dict_root=use_dict_root,
                use_info_sub_dict=use_info_sub_dict,
                allowed_falsely_values=allowed_falsely_values,
            )
        ) or value in allowed_falsely_values:
            if parse_method:
                try:
                    self.formatted_record[key_to_set] = parse_method(value)
                except ParserKeyNotFoundError:
                    pass  # continue to _handle_not_found
                except Exception as error:
                    self._log_missing(
                        key_to_set=key_to_set,
                        error_description=f"{keys_to_test} - found value {value},"
                        " but failed to parse with method",
                        method=not_found_method,
                        error=error,
                    )
                    return False
            else:
                self.formatted_record[key_to_set] = value
            return True
        return self._handle_not_found(
            not_found_method=not_found_method,
            key_to_set=key_to_set,
            keys_to_test=keys_to_test,
            not_found_val=not_found_val,
            enable_log=enable_log,
        )

    def _handle_not_found(
        self,
        not_found_method,
        key_to_set: str,
        keys_to_test: list,
        not_found_val,
        enable_log: bool,
    ) -> False:
        if not_found_method:
            try:
                self.formatted_record[key_to_set] = not_found_method(not_found_val)
                return False
            except Exception as error:
                self._log_missing(
                    key_to_set=key_to_set,
                    error_description=keys_to_test,
                    method=not_found_method,
                    error=error,
                )
        else:
            self._handle_not_found_value(
                enable_log, keys_to_test, not_found_val, key_to_set
            )

    def _handle_not_found_value(
        self, enable_log, keys_to_test, not_found_val, key_to_set
    ):
        if not_found_val:
            self.formatted_record[key_to_set] = not_found_val
        elif enable_log:
            self._log_missing(
                key_to_set=key_to_set,
                error_description=keys_to_test,
            )
        return False

    def _try_to_find_and_set_decimal(
        self,
        key_to_set: str,
        keys_to_test: list,
        not_found_val: float or int = 0,
        parse_method=None,
        not_found_method=None,
        enable_log: bool = True,
        use_dict_root: bool = True,
        use_info_sub_dict: bool = False,
        allow_zero: bool = False,
    ) -> bool:
        not_found_val = not_found_val or 0
        value = self._try_to_find_decimal(
            key_to_set,
            keys_to_test,
            not_found_val,
            use_dict_root,
            use_info_sub_dict,
            allow_zero,
        )
        if value or (allow_zero and value == trading_constants.ZERO):
            return self.set_decimal(
                key_to_set, parse_method(value) if parse_method else value
            )
        if not_found_method:
            try:
                return self.set_decimal(
                    key_to_set,
                    not_found_method(not_found_val),
                )
            except Exception as error:
                self._log_missing(
                    key_to_set=key_to_set,
                    error_description=keys_to_test,
                    method=not_found_method,
                    error=error,
                )
                return False
        return self._handle_not_found_decimal_value(
            enable_log, keys_to_test, not_found_val, key_to_set
        )

    async def _try_to_find_and_set_decimal_async(
        self,
        key_to_set: str,
        keys_to_test: list,
        not_found_val: float or int = 0,
        parse_method=None,
        parse_method_is_async: bool = False,
        not_found_method=None,
        not_found_method_is_async: bool = False,
        enable_log: bool = True,
        use_dict_root: bool = True,
        use_info_sub_dict: bool = False,
        allow_zero: bool = False,
    ) -> bool:
        if (
            value := self._try_to_find_decimal(
                key_to_set,
                keys_to_test,
                not_found_val,
                use_dict_root,
                use_info_sub_dict,
                allow_zero,
            )
        ) or (allow_zero and value == trading_constants.ZERO):
            if parse_method:
                value = (
                    await parse_method(value)
                    if parse_method_is_async
                    else parse_method(value)
                )
            return self.set_decimal(key_to_set, value)
        if not_found_method:
            try:
                return self.set_decimal(
                    key_to_set,
                    (
                        await not_found_method(not_found_val)
                        if not_found_method_is_async
                        else not_found_method(not_found_val)
                    ),
                )
            except Exception as error:
                self._log_missing(
                    key_to_set=key_to_set,
                    error_description=keys_to_test,
                    method=not_found_method,
                    error=error,
                )
                return False
        return self._handle_not_found_decimal_value(
            enable_log, keys_to_test, not_found_val, key_to_set
        )

    def set_decimal(self, key_to_set, value):
        value = value or 0
        self.formatted_record[key_to_set] = (
            value if type(value) is decimal.Decimal else decimal.Decimal(str(value))
        )

    def _try_to_find_decimal(
        self,
        key_to_set,
        keys_to_test,
        not_found_val,
        use_dict_root,
        use_info_sub_dict,
        allow_zero,
    ):
        return decimal.Decimal(
            str(
                self._try_to_find(
                    key_to_set=key_to_set,
                    keys_to_test=keys_to_test,
                    not_found_val=not_found_val or 0,
                    enable_log=False,
                    use_dict_root=use_dict_root,
                    use_info_sub_dict=use_info_sub_dict,
                    allowed_falsely_values=(0, 0.0) if allow_zero else (),
                )
            )
        )

    def _handle_not_found_decimal_value(
        self, enable_log, keys_to_test, not_found_val, key_to_set
    ):
        if not_found_val is not None:
            self.set_decimal(key_to_set, not_found_val)
        elif enable_log:
            self._log_missing(
                key_to_set=key_to_set,
                error_description=keys_to_test,
            )
        return False

    def _try_to_find(
        self,
        key_to_set: str,
        keys_to_test: list,
        not_found_val=None,
        enable_log: bool = True,
        use_dict_root: bool = True,
        use_info_sub_dict: bool = False,
        allowed_falsely_values: tuple = (),
    ):
        value = None
        potential_value = None
        for key in keys_to_test:
            try:
                if use_dict_root:
                    value = self.raw_record[key]
                    if value:
                        return value
                    if value in allowed_falsely_values:
                        potential_value = value
            except KeyError:
                pass
            try:
                if use_info_sub_dict:
                    value = self.raw_record[
                        enums.ExchangePositionCCXTColumns.INFO.value
                    ][key]
                    if value:
                        return value
                    if value in allowed_falsely_values:
                        potential_value = value
            except KeyError:
                pass
        if potential_value is not None:
            return potential_value
        if not_found_val is not None:
            return not_found_val

        if enable_log:
            self._log_missing(
                key_to_set=key_to_set,
                error_description=keys_to_test,
            )
        return None

    def _ensure_dict(self, raw_record):
        if type(raw_record) is dict:
            self.formatted_record = {}  # clear record first
            self.raw_record = raw_record
            if not self.multiple_records:
                self.reporter.clear_reporter()
        else:
            raise NotImplementedError(
                self.reporter.debugging_report_main_template(
                    f"{self.PARSER_TITLE} parser received an invalid format\n"
                    "type should be a dict\n"
                    f"received raw data type:  {type(raw_record) or 'no data type'}\n"
                    f"received raw data:  {raw_record or 'no data'}\n"
                )
            )

    def _ensure_list(self, raw_records):
        if type(raw_records) is list:
            self.raw_records = raw_records
            self.multiple_records = True
            self.reporter.clear_reporter()
        else:
            raise NotImplementedError(
                self.reporter.debugging_report_main_template(
                    f"{self.PARSER_TITLE} parser received an invalid format\n"
                    f"type should be a list of multiple {self.PARSER_TITLE}\n"
                    f"received raw data type:  {type(raw_records) or 'no raw data type'}\n"
                    f"received raw data: {raw_records or 'no raw data'}"
                )
            )


def convert_any_time_to_seconds(raw_timestamp):
    if raw_timestamp:
        try:
            return convert_timestamp_to_seconds(raw_timestamp)
        except ParserTimestampNotSecondsError:
            if seconds := convert_date_time_str_to_seconds(raw_timestamp):
                return seconds
        except ParserInvalidTimestampError:
            pass
    raise ParserInvalidTimestampError(
        f"Invalid timestamp ({raw_timestamp or 'no time provided'})"
    )


def convert_date_time_str_to_seconds(raw_timestamp: str) -> int or None:
    if type(raw_timestamp) is str and "T" in raw_timestamp and "Z" in raw_timestamp:
        return int(
            datetime.datetime.timestamp(
                datetime.datetime.strptime(raw_timestamp, "%Y-%m-%dT%H:%M:%SZ")
            )
        )


def convert_timestamp_to_seconds(raw_timestamp: int or float or str) -> int:
    try:
        _time = int(raw_timestamp)
    except:
        raise ParserTimestampNotSecondsError
    # change this before the year 5138
    if _time < 100000000000:
        return _time
    _time = int(_time / 1000)
    if timestamp_util.is_valid_timestamp(_time):
        return _time
    raise ParserInvalidTimestampError


class ParserInvalidTimestampError(Exception):
    pass


class ParserTimestampNotSecondsError(Exception):
    pass


class ParserKeyNotFoundError(Exception):
    pass
