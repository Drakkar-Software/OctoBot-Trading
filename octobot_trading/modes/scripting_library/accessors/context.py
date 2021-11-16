#  Drakkar-Software OctoBot-Trading
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.


class Context:
    def __init__(
        self,
        trading_mode,
        exchange_manager,
        trader,
        exchange_name,
        traded_pair,
        matrix_id,
        cryptocurrency,
        signal_symbol,
        time_frame,
        logger,
        writer,
        trading_mode_class,
    ):
        self.trading_mode = trading_mode
        self.exchange_manager = exchange_manager
        self.trader = trader
        self.exchange_name = exchange_name
        self.traded_pair = traded_pair
        self.matrix_id = matrix_id
        self.cryptocurrency = cryptocurrency
        self.signal_symbol = signal_symbol
        self.time_frame = time_frame
        self.logger = logger
        self.writer = writer
        self.trading_mode_class = trading_mode_class

    @staticmethod
    def minimal(trading_mode_class, logger):
        return Context(
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            logger,
            None,
            trading_mode_class,
        )
