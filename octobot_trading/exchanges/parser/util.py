import decimal
from octobot_trading import constants as trading_constants
from octobot_trading.enums import (
    ExchangePositionCCXTColumns,
)


class Parser:
    """
    overwrite Parser class methods if necessary
    always/only include bulletproof custom code into the parser to improve generic support
    """

    def __init__(self, exchange):
        self.PARSER_TITLE = ""  # example for position parser:  "position"
        self.REQUIRED_FIELDS = []  # keys that need to be in the formatted record
        self.NON_EMPTY_FIELDS = []  # keys that can't be empty in the formatted record

        self.debugging_report_dict = {}
        self.debugging_report_str = ""
        self.missing_attributes_str = ""

        self.raw_records = {}
        self.exchange = exchange  # todo replace with logger
        self.raw_record = {}
        self.formatted_record = {}
        self.formatted_records = []
        self.multiple_records = False

    def _ensure_details_completeness(self):
        # ensure all REQUIRED_FIELDS are present and all NON_EMPTY_FIELDS are not empty

        return all(
            key in self.formatted_record for key in self.REQUIRED_FIELDS
        ) and all(self.formatted_record[key] for key in self.NON_EMPTY_FIELDS)

    def _create_debugging_report_for_record(self):
        if not self.multiple_records:
            self._create_debugging_report()

    def _create_debugging_report(self):
        if self.debugging_report_dict:
            # filter duplicated errors
            debugging_report_str = ""
            missing_attributes_str = ""
            for (
                attribute_name,
                error_messages_list,
            ) in self.debugging_report_dict.items():
                for index in range(len(error_messages_list)):
                    if not error_messages_list[index] in error_messages_list[:index]:
                        debugging_report_str += error_messages_list[index]
                missing_attributes_str += f"{attribute_name}, "

            self.exchange.logger.error(
                self.debugging_report_template(
                    f"Attributes with errors: {missing_attributes_str}\n"
                    "\n"
                    # f"Used exchange: {self.exchange}\n\n"  # todo add exchange name
                    f"Debugging report: \n"
                    "\n"
                    f"{debugging_report_str}\n"
                    f"The raw {self.PARSER_TITLE} response from the exchange: \n"
                    "\n"
                    f"{self.raw_records if self.multiple_records else self.raw_record}\n"
                    "\n"
                    f"Successfully parsed {self.PARSER_TITLE} attributes: \n"
                    f"{self.formatted_records if self.multiple_records else self.formatted_record}\n"
                )
            )
            raise NotImplementedError

    def debugging_report_template(self, report) -> str:
        return (
            f"\n!!!!!!!!!!!!  DEBUGGING REPORT {self.PARSER_TITLE.upper()} START  !!!!!!!!!!!!\n"
            "\n"
            f"Post this report into OctoBot discord -> bug_report\n"
            "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n"
            "This will help us to add support for your exchange\n"
            "\n"
            f"OctoBot is not able to parse all {self.PARSER_TITLE} attributes\n"
            f"{report}"
            "\n"
            f"!!!!!!!!!!!!  DEBUGGING REPORT {self.PARSER_TITLE.upper()} END  !!!!!!!!!!!!"
        )

    def _try_to_find_and_parse_with_method(
        self,
        key_to_set,
        keys_to_test,
        parse_method,
        not_found_val=None,
        not_found_method=None,
        enable_log=True,
        use_dict_root=True,
        use_info_sub_dict=False,
    ) -> bool:
        try:
            if value := self._try_to_find(
                key_to_set=key_to_set,
                keys_to_test=keys_to_test,
                not_found_val=not_found_val,
                enable_log=False,
                use_dict_root=use_dict_root,
                use_info_sub_dict=use_info_sub_dict,
            ):
                self.formatted_record[key_to_set] = parse_method(value)
                return True
        except Exception as e:
            self._log_missing_with_method(
                key_to_set=key_to_set,
                tried_message=keys_to_test,
                method=not_found_method,
                error=e,
            )
        return self._handle_not_found(
            not_found_method=not_found_method,
            not_found_val=not_found_val,
            key_to_set=key_to_set,
            keys_to_test=keys_to_test,
            enable_log=enable_log,
        )

    def _try_to_find_and_set(
        self,
        key_to_set,
        keys_to_test,
        not_found_val=None,
        not_found_method=None,
        enable_log=True,
        use_dict_root=True,
        use_info_sub_dict=False,
    ) -> bool:
        if value := self._try_to_find(
            key_to_set=key_to_set,
            keys_to_test=keys_to_test,
            not_found_val=not_found_val,
            enable_log=False,
            use_dict_root=use_dict_root,
            use_info_sub_dict=use_info_sub_dict,
        ):
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
        self, not_found_method, key_to_set, keys_to_test, not_found_val, enable_log
    ) -> False:
        if not_found_method:
            try:
                self.formatted_record[key_to_set] = not_found_method(not_found_val)
                return False
            except Exception as e:
                self._log_missing_with_method(
                    key_to_set=key_to_set,
                    tried_message=keys_to_test,
                    method=not_found_method,
                    error=e,
                )
        elif enable_log:
            self._log_missing(
                key_to_set=key_to_set,
                tried_message=keys_to_test,
            )
        self.formatted_record[key_to_set] = not_found_val
        return False

    def _try_to_find_and_set_decimal(
        self,
        key_to_set,
        keys_to_test,
        not_found_val=0,
        parse_method=None,
        not_found_method=None,
        enable_log=True,
        use_dict_root=True,
        use_info_sub_dict=False,
    ) -> bool:
        if value := decimal.Decimal(
            str(
                self._try_to_find(
                    key_to_set=key_to_set,
                    keys_to_test=keys_to_test,
                    not_found_val=not_found_val,
                    enable_log=False,
                    use_dict_root=use_dict_root,
                    use_info_sub_dict=use_info_sub_dict,
                )
            )
        ):
            self.formatted_record[key_to_set] = (
                parse_method(value) if parse_method else value
            )
            return True

        if not_found_method:
            try:
                self.formatted_record[key_to_set] = decimal.Decimal(
                    str(not_found_method(not_found_val))
                )
                return False
            except Exception as e:
                self._log_missing_with_method(
                    key_to_set=key_to_set,
                    tried_message=keys_to_test,
                    method=not_found_method,
                    error=e,
                )
                return False
        if enable_log and value != trading_constants.ZERO:
            self._log_missing(
                key_to_set=key_to_set,
                tried_message=keys_to_test,
            )
        self.formatted_record[key_to_set] = decimal.Decimal(str(not_found_val))
        return False

    def _try_to_find(
        self,
        key_to_set,
        keys_to_test,
        not_found_val=None,
        enable_log=True,
        use_dict_root=True,
        use_info_sub_dict=False,
    ):
        value = None
        for key in keys_to_test:
            try:
                if use_dict_root:
                    value = self.raw_record[key]
                    if (value != 0 and value is not None) or value is False:
                        return value
            except:
                pass
            try:
                if use_info_sub_dict:
                    value = self.raw_record[ExchangePositionCCXTColumns.INFO.value][key]
                    if (value != 0 and value is not None) or False:
                        return value
            except:
                pass
        if value != float(0) and enable_log:
            self._log_missing(
                key_to_set=key_to_set,
                tried_message=keys_to_test,
            )
        return not_found_val

    def _ensure_dict(self, raw_record):
        if type(raw_record) is dict:
            self.formatted_record = {}  # clear record first
            self.raw_record = raw_record
        else:
            raise NotImplementedError(
                self.debugging_report_template(
                    f"{self.PARSER_TITLE} parser received an invalid format\n"
                    "type should be a dict\n"
                    f"received raw data type:  {type(raw_record) or 'no data type'}\n"
                    f"received raw data:  {raw_record or 'no data'}\n"
                )
            )

    def _ensure_list(self, raw_records):
        if (_type := type(raw_records)) is list:
            self.raw_records = raw_records
            self.multiple_records = True
        else:
            raise NotImplementedError(
                self.debugging_report_template(
                    f"{self.PARSER_TITLE} parser received an invalid format\n"
                    f"type should be a list of multiple {self.PARSER_TITLE}\n"
                    f"received raw data type:  {_type or 'no raw data type'}\n"
                    f"received raw data: {raw_records or 'no raw data'}"
                )
            )

    def _log_missing(
        self, key_to_set, tried_message, additional_message="", error=None
    ):
        _message = (
            f"> Failed to parse {self.PARSER_TITLE} attribute: {key_to_set} - tried: {tried_message}\n"
            f"{additional_message}{' - Error: '+error if error else ''}\n"
        )
        if key_to_set in self.debugging_report_dict:
            self.debugging_report_dict[key_to_set].append(_message)
        else:
            self.debugging_report_dict[key_to_set] = [_message]

    def _log_missing_with_method(self, key_to_set, tried_message, method, error):
        self._log_missing(
            key_to_set=key_to_set,
            tried_message=tried_message,
            additional_message=f"with method: {type(method).__name__ if method else 'no method provided'} - error: {error}\n",
        )
