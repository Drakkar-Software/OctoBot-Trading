class ExchangeTestStatus:
    """
    pass either is_fully_tested=True or
    or set it for each separate
    """

    def __init__(
        self,
        is_fully_tested: bool = False,
        spot_real_tested: bool = False,
        spot_testnet_tested: bool = False,
        futures_real_tested: bool = False,
        futures_testnet_tested: bool = False,
    ):
        self.spot_real_tested = is_fully_tested or spot_real_tested
        self.spot_testnet_tested = is_fully_tested or spot_testnet_tested
        self.futures_real_tested = is_fully_tested or futures_real_tested
        self.futures_testnet_tested = is_fully_tested or futures_testnet_tested
        self.is_fully_tested = is_fully_tested or (
            spot_real_tested
            and spot_testnet_tested
            and futures_real_tested
            and futures_testnet_tested
        )
        