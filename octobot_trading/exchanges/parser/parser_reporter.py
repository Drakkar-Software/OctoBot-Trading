import octobot_commons.logging.debugging_report_util as debugging_report_util


class ParserReporter(debugging_report_util.DebuggingReporter):
    THIS_WILL_HELP_US_WITH_MESSAGE = (
        "This will help us to add support for your exchange"
    )

    def __init__(self, logger, parser_title, parser_type_name):
        super().__init__(logger)
        self.REPORT_TITLE = parser_title
        self.PARSER_TYPE_NAME = parser_type_name
        self.ERROR_TITLE_MESSAGE = (
            f"OctoBot is not able to parse all {parser_type_name} attributes:"
        )

    def add_to_debugging_report(
        self,
        key_to_set: str,
        error_description: str,
        additional_message: str = "",
        error=None,
        method=None,
    ):
        method_message = (
            f'with method: {type(method).__name__ if method else "no method provided"}\n'
            if method
            else ""
        )
        additional_message = f"{additional_message}\n" if additional_message else ""
        message = (
            f"> Failed to parse {self.PARSER_TYPE_NAME} attribute:"
            " {key_to_set} - tried: {error_description}\n"
            f"{additional_message}"
            f"{method_message}{' - Error: '+repr(error) if error else ''}\n"
        )
        self._add_to_debugging_report(key_to_set, message)

    def create_debugging_report(self, _parser):
        if self.debugging_report_dict:
            (
                attributes_with_all_errors,
                attributes_with_errors,
            ) = self.remove_duplicated_errors_and_format()

            self._finalize_debugging_report(
                f"Attributes with errors: {attributes_with_errors}\n"
                "\n"
                # f"Used exchange: {self.exchange}\n\n"  # todo add exchange name
                f"Debugging report: \n"
                "\n"
                f"{attributes_with_all_errors}\n"
                f"The raw {_parser.PARSER_TYPE_NAME} response from the exchange: \n"
                "\n"
                f"{_parser.raw_records if _parser.multiple_records else _parser.raw_record}\n"
                "\n"
                f"Successfully parsed {_parser.PARSER_TYPE_NAME} attributes: \n"
                f"{_parser.formatted_records if _parser.multiple_records else _parser.formatted_record}\n"
            )

    def create_debugging_report_for_record(self, _parser):
        if not _parser.multiple_records:
            self.create_debugging_report(_parser)
