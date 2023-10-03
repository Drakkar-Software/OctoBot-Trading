# pylint: disable=E0611
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
import contextlib
import decimal
import ccxt.async_support as ccxt
import typing
import inspect

import octobot_commons.enums
import octobot_commons.symbols as commons_symbols

import octobot_trading
import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.errors
import octobot_trading.exchanges as exchanges
import octobot_trading.exchanges.abstract_exchange as abstract_exchange
import octobot_trading.exchanges.util.symbol_details as symbol_details_import
import octobot_trading.exchanges.connectors.ccxt.ccxt_adapter as ccxt_adapter
import octobot_trading.exchanges.connectors.ccxt.ccxt_client_util as ccxt_client_util
import octobot_trading.exchanges.connectors.ccxt.enums as ccxt_enums
import octobot_trading.exchanges.connectors.ccxt.constants as ccxt_constants
import octobot_trading.personal_data as personal_data
from octobot_trading.enums import ExchangeConstantsOrderColumns as ecoc


class CCXTConnector(abstract_exchange.AbstractExchange):
    """
    CCXT library connector. Everything ccxt related should be in this connector.
    When possible, each call is supposed to create only one request to the exchange.
    Uses self.adapter to parse (and fix if necessary) ccxt raw data.

    Always returns adapted data. Always throws octobot_trading errors
    Never returns row ccxt data or throw ccxt errors
    """

    def __init__(
        self, config, exchange_manager, adapter_class=None, additional_config=None, rest_name=None, force_auth=False
    ):
        super().__init__(config, exchange_manager)
        self.client = None
        self.exchange_type = None
        self.adapter = self.get_adapter_class(adapter_class)(self)
        self.all_currencies_price_ticker = None
        self.is_authenticated = False
        self.rest_name = rest_name or self.exchange_manager.exchange_class_string
        self.force_authentication = force_auth

        # used to save exchange local elements in subclasses
        self.saved_data = {}

        self.additional_config = additional_config
        self.headers = {}
        self.options = {}
        # add default options
        self.add_options(
            ccxt_client_util.get_ccxt_client_login_options(self.exchange_manager)
        )
        # add specific options
        if self.additional_config:
            specific_options = self.additional_config.pop(ccxt_constants.CCXT_OPTIONS, None)
            if specific_options:
                self.add_options(specific_options)

        self._create_exchange_type()
        self._create_client()

    async def initialize_impl(self):
        try:
            if self.exchange_manager.exchange.is_supporting_sandbox():
                ccxt_client_util.set_sandbox_mode(
                    self, self.exchange_manager.is_sandboxed
                )
                
            if self.force_authentication or (
                self._should_authenticate() and not self.exchange_manager.exchange_only
            ):
                await self._ensure_auth()

            with self.error_describer():
                await self.load_symbol_markets(forced_markets=self.exchange_manager.forced_markets)

            # initialize symbols and timeframes
            self.symbols = self.get_client_symbols()
            self.time_frames = self.get_client_time_frames()

        except (ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as e:
            raise octobot_trading.errors.UnreachableExchange() from e
        except ccxt.AuthenticationError:
            raise ccxt.AuthenticationError

    def get_adapter_class(self, adapter_class):
        return adapter_class or ccxt_adapter.CCXTAdapter

    @classmethod
    def load_user_inputs_from_class(cls, tentacles_setup_config, tentacle_config):
        # no user input in connector
        pass

    async def load_symbol_markets(self, reload=False, forced_markets=None):
        if forced_markets is not None:
            if forced_markets:
                # only set markets if there are markets to be set
                ccxt_client_util.set_markets_from_forced_markets(self.client, forced_markets)
        else:
            try:
                await self.client.load_markets(reload=reload)
            except ccxt.ExchangeNotAvailable as err:
                raise octobot_trading.errors.FailedRequest(
                    f"Failed to get_symbol_prices: {err.__class__.__name__} on {err}"
                ) from err

    def update_symbol_details(self, symbol_details: symbol_details_import.SymbolDetails, symbol: str) -> str:
        """
        Update the given symbol_details with connector symbol details
        :return: the symbol id
        """
        market = self.client.markets[symbol]
        if self.supports_markets_as_raw_info():
            symbol_details.ccxt.info = market[enums.ExchangeConstantsMarketStatusColumns.INFO.value]
        else:
            symbol_details.ccxt.parsed = market
        return market[enums.ExchangeConstantsMarketStatusColumns.ID.value]

    def get_client_symbols(self):
        return ccxt_client_util.get_symbols(self.client)

    def get_client_time_frames(self):
        return ccxt_client_util.get_time_frames(self.client)

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return isinstance(exchange_candidate_name, str)

    def _create_exchange_type(self):
        if self.is_supporting_exchange(self.rest_name):
            self.exchange_type = getattr(ccxt, self.rest_name)
        else:
            self.exchange_type = self.rest_name

    def add_headers(self, headers_dict):
        """
        Add new headers to ccxt client
        :param headers_dict: the additional header keys and values as dict
        """
        self.headers.update(headers_dict)
        if self.client is not None:
            ccxt_client_util.add_headers(self.client, headers_dict)

    def add_options(self, options_dict):
        """
        Add new options to ccxt client
        :param options_dict: the additional option keys and values as dict
        """
        self.options.update(options_dict)
        if self.client is not None:
            ccxt_client_util.add_options(self.client, options_dict)

    async def _ensure_auth(self):
        try:
            await self.get_balance()
        except ccxt.AuthenticationError as e:
            await self.client.close()
            self.unauthenticated_exchange_fallback(e)
        except Exception as e:
            # Is probably handled in exchange tentacles, important thing here is that authentication worked
            self.logger.debug(f"Error when checking exchange connection: {e}. This should not be an issue.")

    def _create_client(self):
        self.client, self.is_authenticated = ccxt_client_util.create_client(
            self.exchange_type, self.exchange_manager, self.logger,
            self.options, self.headers, self.additional_config,
            self._should_authenticate(), self.unauthenticated_exchange_fallback
        )

    def _should_authenticate(self):
        return self.force_authentication or not (
            self.exchange_manager.is_simulated or
            self.exchange_manager.is_backtesting
        )

    def unauthenticated_exchange_fallback(self, err):
        self.handle_token_error(err)
        return ccxt_client_util.get_unauthenticated_exchange(
            self.exchange_type,
            self.options, self.headers, self.additional_config
        )

    def get_market_status(self, symbol, price_example=None, with_fixer=True):
        try:
            if with_fixer:
                return exchanges.ExchangeMarketStatusFixer(self.client.market(symbol), price_example).market_status
            return self.client.market(symbol)
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except Exception as e:
            self.logger.error(f"Fail to get market status of {symbol}: {e}")
            return {}

    async def get_balance(self, **kwargs: dict):
        """
        fetch balance (free + used) by currency
        :return: balance dict
        """
        if not kwargs:
            kwargs = {}
        try:
            with self.error_describer():
                return self.adapter.adapt_balance(
                    await self.client.fetch_balance(params=kwargs)
                )
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported

    async def get_symbol_prices(self,
                                symbol: str,
                                time_frame: octobot_commons.enums.TimeFrames,
                                limit: int = None,
                                since: int = None,
                                **kwargs: dict) -> typing.Optional[list]:
        try:
            with self.error_describer():
                return self.adapter.adapt_ohlcv(
                    await self.client.fetch_ohlcv(symbol, time_frame.value, limit=limit, since=since, params=kwargs)
                )
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
            raise octobot_trading.errors.FailedRequest(
                f"Failed to get_symbol_prices of {symbol} on {time_frame.value}: {e.__class__.__name__} on {e}"
            ) from e

    async def get_kline_price(self,
                              symbol: str,
                              time_frame: octobot_commons.enums.TimeFrames,
                              **kwargs: dict) -> typing.Optional[list]:
        try:
            with self.error_describer():
                limit = kwargs.pop("limit", 1)
                since = kwargs.pop("since", None)
                return self.adapter.adapt_kline(
                    await self.client.fetch_ohlcv(symbol, time_frame.value, limit=limit, since=since, params=kwargs)
                )
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
            raise octobot_trading.errors.FailedRequest(f"Failed to get_kline_price {e}")

    # return up to ten bidasks on each side of the order book stack
    async def get_order_book(self, symbol: str, limit: int = 5, **kwargs: dict) -> typing.Optional[dict]:
        try:
            with self.error_describer():
                return self.adapter.adapt_order_book(
                    await self.client.fetch_order_book(symbol, limit=limit, params=kwargs)
                )
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
            raise octobot_trading.errors.FailedRequest(f"Failed to get_order_book {e}")

    async def get_recent_trades(self, symbol: str, limit: int = 50, **kwargs: dict) -> typing.Optional[list]:
        try:
            with self.error_describer():
                return self.adapter.adapt_public_recent_trades(
                    await self.client.fetch_trades(symbol, limit=limit, params=kwargs)
                )
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
            raise octobot_trading.errors.FailedRequest(f"Failed to get_recent_trades {e}")

    # A price ticker contains statistics for a particular market/symbol for some period of time in recent past (24h)
    async def get_price_ticker(self, symbol: str, **kwargs: dict) -> typing.Optional[dict]:
        try:
            with self.error_describer():
                return self.adapter.adapt_ticker(
                    await self.client.fetch_ticker(symbol, params=kwargs)
                )
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
            raise octobot_trading.errors.FailedRequest(f"Failed to get_price_ticker {e}")

    async def get_all_currencies_price_ticker(self, **kwargs: dict) -> typing.Optional[dict[str, dict]]:
        try:
            with self.error_describer():
                symbols = kwargs.pop("symbols", None)
                self.all_currencies_price_ticker = {
                    symbol: self.adapter.adapt_ticker(ticker)
                    for symbol, ticker in (await self.client.fetch_tickers(symbols, params=kwargs)).items()
                }
            return self.all_currencies_price_ticker
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except ccxt.BaseError as e:
            raise octobot_trading.errors.FailedRequest(f"Failed to get_all_currencies_price_ticker {e}")

    # ORDERS
    async def get_order(self, exchange_order_id: str, symbol: str = None, **kwargs: dict) -> dict:
        if self.client.has['fetchOrder']:
            try:
                with self.error_describer():
                    return self.adapter.adapt_order(
                        await self.client.fetch_order(exchange_order_id, symbol, params=kwargs),
                        symbol=symbol
                    )
            except ccxt.OrderNotFound:
                # some exchanges are throwing this error when an order is cancelled (ex: coinbase pro)
                pass
            except ccxt.NotSupported as e:
                # some exchanges are throwing this error when an order is cancelled (ex: coinbase pro)
                raise octobot_trading.errors.NotSupported from e
            except ccxt.ExchangeError as e:
                # something went wrong and ccxt did not expect it
                raise octobot_trading.errors.FailedRequest from e
        else:
            # When fetch_order is not supported, uses get_open_orders and extract order id
            open_orders = await self.get_open_orders(symbol=symbol)
            for order in open_orders:
                if order.get(ecoc.EXCHANGE_ID.value, None) == exchange_order_id:
                    return order
        return None  # OrderNotFound

    async def get_all_orders(self, symbol: str = None, since: int = None,
                             limit: int = None, **kwargs: dict) -> list:
        if self.client.has['fetchOrders']:
            with self.error_describer():
                return self.adapter.adapt_orders(
                    await self.client.fetch_orders(symbol=symbol, since=since, limit=limit, params=kwargs),
                    symbol=symbol
                )
        else:
            raise octobot_trading.errors.NotSupported("This exchange doesn't support fetchOrders")

    async def get_open_orders(self, symbol: str = None, since: int = None,
                              limit: int = None, **kwargs: dict) -> list:
        if self.client.has['fetchOpenOrders']:
            with self.error_describer():
                return self.adapter.adapt_orders(
                    await self.client.fetch_open_orders(symbol=symbol, since=since, limit=limit, params=kwargs),
                    symbol=symbol
                )
        else:
            raise octobot_trading.errors.NotSupported("This exchange doesn't support fetchOpenOrders")

    async def get_closed_orders(self, symbol: str = None, since: int = None,
                                limit: int = None, **kwargs: dict) -> list:
        try:
            with self.error_describer():
                return self.adapter.adapt_orders(
                    await self.client.fetch_closed_orders(symbol=symbol, since=since, limit=limit, params=kwargs),
                    symbol=symbol
                )
        except ccxt.NotSupported as e:
            # fetch_closed_orders is not supported
            raise octobot_trading.errors.NotSupported from e

    async def get_my_recent_trades(self, symbol: str = None, since: int = None,
                                   limit: int = None, **kwargs: dict) -> list:
        if self.client.has['fetchMyTrades'] or self.client.has['fetchTrades']:
            with self.error_describer():
                method = self.client.fetch_my_trades if self.client.has['fetchMyTrades'] else self.client.fetch_trades
                trades = self.adapter.adapt_trades(await method(symbol=symbol, since=since, limit=limit, params=kwargs))
                if trades or not self.exchange_manager.exchange.ALLOW_TRADES_FROM_CLOSED_ORDERS:
                    return trades
                # on some exchanges, recent trades are only fetching very recent trade. also try closed orders
                return await self.exchange_manager.exchange.get_closed_orders(
                    symbol=symbol,
                    since=since,
                    limit=limit,
                    **kwargs
                )
        else:
            raise octobot_trading.errors.NotSupported("This exchange doesn't support fetchMyTrades nor fetchTrades")

    async def create_market_buy_order(self, symbol, quantity, price=None, params=None) -> dict:
        return self.adapter.adapt_order(
            # use create_order instead of create_market_buy_order to pass the price argument
            await self.client.create_order(
                symbol, enums.TradeOrderType.MARKET.value, enums.TradeOrderSide.BUY.value, quantity,
                price=price, params=params
            ),
            symbol=symbol, quantity=quantity
        )

    async def create_limit_buy_order(self, symbol, quantity, price=None, params=None) -> dict:
        return self.adapter.adapt_order(
            await self.client.create_limit_buy_order(symbol, quantity, price, params=params),
            symbol=symbol, quantity=quantity
        )

    async def create_market_sell_order(self, symbol, quantity, price=None, params=None) -> dict:
        return self.adapter.adapt_order(
            # use create_order instead of create_market_sell_order to pass the price argument
            await self.client.create_order(
                symbol, enums.TradeOrderType.MARKET.value, enums.TradeOrderSide.SELL.value, quantity,
                price=price, params=params
            ),
            symbol=symbol, quantity=quantity
        )

    async def create_limit_sell_order(self, symbol, quantity, price=None, params=None) -> dict:
        return self.adapter.adapt_order(
            await self.client.create_limit_sell_order(symbol, quantity, price, params=params),
            symbol=symbol, quantity=quantity
        )

    async def create_market_stop_loss_order(self, symbol, quantity, price, side, current_price, params=None) -> dict:
        if self.client.has.get("createStopMarketOrder"):
            try:
                return self.adapter.adapt_order(
                    await self.client.createStopMarketOrder(
                        symbol,
                        side=side,
                        amount=quantity,
                        stopPrice=price,
                        params=params,
                    ),
                    symbol=symbol, quantity=quantity
                )
            except ccxt.OrderImmediatelyFillable:
                # make sure stop always stops
                created_order = await self.exchange_manager.exchange.create_order(
                    order_type=(enums.TraderOrderType.BUY_MARKET
                                if side == enums.TradeOrderSide.BUY.value
                                else enums.TraderOrderType.SELL_MARKET),
                    symbol=symbol,
                    quantity=decimal.Decimal(str(quantity)),
                    price=decimal.Decimal(str(price)),
                    current_price=decimal.Decimal(str(current_price))
                )
                created_order[enums.ExchangeConstantsOrderColumns.TYPE.value] = (
                    enums.TraderOrderType.STOP_LOSS.value
                    )
                return created_order
        raise NotImplementedError("create_market_stop_loss_order is not implemented")

    async def create_limit_stop_loss_order(self, symbol, quantity, price, stop_price, side, params=None) -> dict:
        if self.client.has.get("createStopLimitOrder"):
            return self.adapter.adapt_order(
                await self.client.create_stop_limit_order(
                    symbol,
                    side=side,
                    amount=quantity,
                    price=price,
                    stopPrice=stop_price,
                    params=params,
                ),
                symbol=symbol, quantity=quantity
            )
        raise NotImplementedError("create_limit_stop_loss_order is not implemented")

    async def create_market_take_profit_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("create_market_take_profit_order is not implemented")

    async def create_limit_take_profit_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("create_limit_take_profit_order is not implemented")

    async def create_market_trailing_stop_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("create_market_trailing_stop_order is not implemented")

    async def create_limit_trailing_stop_order(self, symbol, quantity, price=None, side=None, params=None) -> dict:
        raise NotImplementedError("create_limit_trailing_stop_order is not implemented")

    async def edit_order(self, exchange_order_id: str, order_type: enums.TraderOrderType, symbol: str,
                         quantity: float, price: float, stop_price: float = None, side: str = None,
                         current_price: float = None, params: dict = None):
        ccxt_order_type = self.get_ccxt_order_type(order_type)
        price_to_use = price
        if ccxt_order_type == enums.TradeOrderType.MARKET.value:
            # can't set price in market orders
            price_to_use = None
        # do not use keyword arguments here as default ccxt edit order is passing *args (and not **kwargs)
        return self.adapter.adapt_order(
            await self.client.edit_order(
                exchange_order_id, symbol, ccxt_order_type, side, quantity, price_to_use, params
            ),
            symbol=symbol, quantity=quantity
        )

    async def cancel_order(
        self, exchange_order_id: str, symbol: str, order_type: enums.TraderOrderType, **kwargs: dict
    ) -> enums.OrderStatus:
        try:
            with self.error_describer():
                await self.client.cancel_order(exchange_order_id, symbol=symbol, params=kwargs)
                # no exception, cancel worked
            try:
                # make sure order is canceled
                cancelled_order = await self.exchange_manager.exchange.get_order(
                    exchange_order_id, symbol=symbol
                )
                if cancelled_order is None or personal_data.parse_is_cancelled(cancelled_order):
                    return enums.OrderStatus.CANCELED
                elif personal_data.parse_is_open(cancelled_order):
                    return enums.OrderStatus.PENDING_CANCEL
                # cancel command worked but order is still existing and is not open or canceled. unhandled case
                # log error and consider it canceling. order states will manage the
                self.logger.error(f"Unexpected order status after cancel for order: {cancelled_order}. "
                                  f"Considered as {enums.OrderStatus.PENDING_CANCEL.value}")
                return enums.OrderStatus.PENDING_CANCEL
            except ccxt.OrderNotFound:
                # Order is not found: it has successfully been cancelled (some exchanges don't allow to
                # get a cancelled order).
                return enums.OrderStatus.CANCELED
        except ccxt.OrderNotFound as e:
            self.logger.debug(f"Trying to cancel order with id {exchange_order_id} but order was not found")
            raise octobot_trading.errors.OrderCancelError from e
        except (ccxt.NotSupported, octobot_trading.errors.NotSupported) as e:
            raise octobot_trading.errors.NotSupported from e
        except Exception as e:
            self.logger.exception(e, True, f"Unexpected error when cancelling order with exchange id: "
                                           f"{exchange_order_id} failed to cancel | {e} ({e.__class__.__name__})")
            raise e

    async def get_positions(self, symbols=None, **kwargs: dict) -> list:
        try:
            return [
                self.adapter.adapt_position(position)
                for position in await self.client.fetch_positions(symbols=symbols, params=kwargs)
            ]
        except ccxt.NotSupported as err:
            raise NotImplementedError from err

    async def get_position(self, symbol: str, **kwargs: dict) -> dict:
        try:
            return self.adapter.adapt_position(
                await self.client.fetch_position(symbol=symbol, params=kwargs)
            )
        except ccxt.NotSupported as err:
            raise NotImplementedError from err

    async def get_mocked_empty_position(self, symbol: str, **kwargs: dict) -> dict:
        return self.adapter.adapt_position(
            self.client.parse_position({}, market=self.client.market(symbol)),
            force_empty=True
        )

    async def get_funding_rate(self, symbol: str, **kwargs: dict) -> dict:
        return self.adapter.adapt_funding_rate(
            await self.client.fetch_funding_rate(symbol=symbol, params=kwargs)
        )

    async def get_funding_rate_history(self, symbol: str, limit: int = 1, **kwargs: dict) -> list:
        return self.adapter.adapt_funding_rate(
            await self.client.fetch_funding_rate_history(symbol=symbol, limit=limit, params=kwargs)
        )

    async def get_leverage_tiers(self, symbols: list = None, **kwargs: dict) -> dict:
        if self.client.has.get("fetchLeverageTiers"):
            return self.adapter.adapt_leverage_tiers(
                await self.client.fetch_leverage_tiers(symbols=symbols, params=kwargs)
            )
        raise NotImplementedError("get_leverage_tiers is not supported")

    def get_contract_size(self, symbol: str):
        return decimal.Decimal(str(ccxt_client_util.get_contract_size(self.client, symbol)))

    async def get_symbol_leverage(self, symbol: str, **kwargs: dict):
        return self.adapter.adapt_leverage(
            await self.client.fetch_leverage(symbol=symbol, params=kwargs)
        )

    async def set_symbol_leverage(self, symbol: str, leverage: float, **kwargs: dict):
        return await self.client.set_leverage(leverage=int(leverage), symbol=symbol, params=kwargs)

    async def set_symbol_margin_type(self, symbol: str, isolated: bool, **kwargs: dict):
        return await self.client.set_margin_mode(
            ccxt_enums.ExchangeMarginTypes.ISOLATED.value if isolated else ccxt_enums.ExchangeMarginTypes.CROSS.value,
            symbol=symbol,
            params=kwargs,
        )

    async def set_symbol_position_mode(self, symbol: str, one_way: bool):
        return await self.client.set_position_mode(self, hedged=not one_way, symbol=symbol)

    async def set_symbol_partial_take_profit_stop_loss(self, symbol: str, inverse: bool,
                                                       tp_sl_mode: enums.TakeProfitStopLossMode):
        raise NotImplementedError("set_symbol_partial_take_profit_stop_loss is not implemented")

    def get_ccxt_order_type(self, order_type: enums.TraderOrderType):
        if order_type in (enums.TraderOrderType.BUY_LIMIT, enums.TraderOrderType.SELL_LIMIT,
                          enums.TraderOrderType.STOP_LOSS_LIMIT, enums.TraderOrderType.TAKE_PROFIT_LIMIT,
                          enums.TraderOrderType.TRAILING_STOP_LIMIT):
            return enums.TradeOrderType.LIMIT.value
        if order_type in (enums.TraderOrderType.BUY_MARKET, enums.TraderOrderType.SELL_MARKET,
                          enums.TraderOrderType.STOP_LOSS, enums.TraderOrderType.TAKE_PROFIT,
                          enums.TraderOrderType.TRAILING_STOP):
            return enums.TradeOrderType.MARKET.value
        raise RuntimeError(f"Unknown order type: {order_type}")

    def get_trade_fee(self, symbol, order_type, quantity, price, taker_or_maker):
        fees = self.client.calculate_fee(symbol=symbol,
                                         type=order_type,
                                         side=exchanges.get_order_side(order_type),
                                         amount=float(quantity),
                                         price=float(price),
                                         takerOrMaker=taker_or_maker)
        fees[enums.FeePropertyColumns.IS_FROM_EXCHANGE.value] = False
        fees[enums.FeePropertyColumns.COST.value] = decimal.Decimal(str(fees[enums.FeePropertyColumns.COST.value]))
        if self.exchange_manager.is_future:
            # fees on futures are wrong
            rate = fees[enums.FeePropertyColumns.RATE.value]
            # avoid using ccxt computed fees as they are often wrong
            # see https://docs.ccxt.com/en/latest/manual.html#trading-fees
            parsed_symbol = commons_symbols.parse_symbol(symbol)
            if self.exchange_manager.exchange.get_pair_future_contract(symbol).is_inverse_contract():
                fees[enums.FeePropertyColumns.COST.value] = decimal.Decimal(str(rate)) * quantity
                fees[enums.FeePropertyColumns.CURRENCY.value] = parsed_symbol.base
            else:
                fees[enums.FeePropertyColumns.COST.value] = decimal.Decimal(str(rate)) * quantity * price
                fees[enums.FeePropertyColumns.CURRENCY.value] = parsed_symbol.quote
        return fees

    def get_fees(self, symbol):
        try:
            return ccxt_client_util.get_fees(self.client.market(symbol))
        except ccxt.NotSupported:
            raise octobot_trading.errors.NotSupported
        except Exception as e:
            self.logger.error(f"Fees data for {symbol} was not found ({e})")
            return {
                enums.ExchangeConstantsMarketPropertyColumns.TAKER.value: constants.CONFIG_DEFAULT_FEES,
                enums.ExchangeConstantsMarketPropertyColumns.MAKER.value: constants.CONFIG_DEFAULT_FEES,
                enums.ExchangeConstantsMarketPropertyColumns.FEE.value: constants.CONFIG_DEFAULT_FEES
            }

    def get_exchange_current_time(self):
        return self.get_uniform_timestamp(self.client.milliseconds())

    def get_uniform_timestamp(self, timestamp):
        return self.adapter.get_uniformized_timestamp(timestamp)

    async def stop(self) -> None:
        self.logger.debug(f"Closing connection.")
        await ccxt_client_util.close_client(self.client)
        self.logger.debug(f"Connection closed.")
        self.client = None
        self.exchange_manager = None

    def get_pair_from_exchange(self, pair) -> typing.Optional[str]:
        try:
            return self.client.market(pair)["symbol"]
        except ccxt.BadSymbol:
            try:
                return self.client.markets_by_id[pair]["symbol"]
            except KeyError:
                self.logger.error(f"Failed to get market of {pair}")
        return None

    def get_split_pair_from_exchange(self, pair) -> (str, str):
        try:
            market_data: dict = self.client.market(pair)
            return market_data["base"], market_data["quote"]
        except ccxt.BadSymbol:
            try:
                return self.client.markets_by_id[pair]["base"], self.client.markets_by_id[pair]["quote"]
            except KeyError:
                self.logger.error(f"Failed to get market of {pair}")
                return None, None

    def get_exchange_pair(self, pair) -> str:
        return ccxt_client_util.get_exchange_pair(self.client, pair)

    def get_pair_cryptocurrency(self, pair) -> str:
        return ccxt_client_util.get_pair_cryptocurrency(self.client, pair)

    def get_default_balance(self):
        return self.client.account()

    def get_rate_limit(self):
        return self.exchange_type.rateLimit / 1000

    def supports_trading_type(self, symbol, trading_type: enums.FutureContractType) -> bool:
        trading_type_to_ccxt_property = {
            enums.FutureContractType.LINEAR_PERPETUAL: "linear",
            enums.FutureContractType.LINEAR_EXPIRABLE: "linear",
            enums.FutureContractType.INVERSE_PERPETUAL: "inverse",
            enums.FutureContractType.INVERSE_EXPIRABLE: "inverse",
        }
        return self.client.safe_string(
            self.client.market(symbol),
            trading_type_to_ccxt_property[trading_type],
            "False"
        ) == "True"

    def is_expirable_symbol(self, symbol) -> bool:
        return self.client.market(symbol).get("expiry") is not None

    def get_pair_market_type(self, pair, property_name, def_value=False):
        return self.client.safe_string(
            self.client.safe_value(self.client.markets, pair, {}), property_name, def_value
        )

    def get_saved_data(self, key):
        return self.saved_data[key]

    def set_saved_data(self, key, value):
        self.saved_data[key] = value

    """
    Parsers todo: remove all parsers
    """

    def parse_balance(self, balance):
        return self.client.parse_balance(balance)

    def parse_trade(self, trade):
        return self.client.parse_trade(trade)

    def parse_order(self, order):
        return self.client.parse_order(order)

    def parse_ticker(self, ticker):
        return self.client.parse_ticker(ticker)

    def parse_ohlcv(self, ohlcv):
        return self.uniformize_candles_if_necessary(self.client.parse_ohlcv(ohlcv))

    def parse_order_book(self, order_book):
        return self.client.parse_order_book(order_book)

    def parse_order_book_ticker(self, order_book_ticker):
        return order_book_ticker

    def parse_timestamp(self, data_dict, timestamp_key, default_value=None, ms=False):
        parsed_timestamp = self.client.parse8601(self.client.safe_string(data_dict, timestamp_key))
        return (parsed_timestamp if ms else parsed_timestamp * 10 ** -3) if parsed_timestamp else default_value

    def parse_currency(self, currency):
        return self.client.safe_currency_code(currency)

    def parse_exhange_order_id(self, order):
        return order.get(ecoc.EXCHANGE_ID.value, None)

    def parse_order_symbol(self, order):
        return order.get(ecoc.SYMBOL.value, None)

    def parse_side(self, side):
        return enums.TradeOrderSide.BUY if side == self.BUY_STR else enums.TradeOrderSide.SELL

    def parse_account(self, account):
        return enums.AccountTypes[account]

    def parse_funding(self, funding_dict, from_ticker=False) -> dict:
        return self.adapter.adapt_funding_rate(funding_dict, from_ticker=from_ticker)

    def parse_mark_price(self, mark_price_dict, from_ticker=False) -> dict:
        return self.adapter.adapt_mark_price(mark_price_dict, from_ticker=from_ticker)

    def get_max_handled_pair_with_time_frame(self) -> int:
        """
        Override when necessary
        :return: the maximum number of simultaneous pairs * time_frame that this exchange can handle.
        """
        # 15 pairs, each on 3 time frames
        return 45

    def supports_markets_as_raw_info(self) -> bool:
        return ccxt_client_util.supports_markets_as_raw_info(self.client)

    def log_ddos_error(self, error):
        self.logger.error(
            f"DDoSProtection triggered [{error} ({error.__class__.__name__})]. "
            f"Last response headers: {self.client.last_response_headers} "
            f"Last json response: {self.client.last_json_response}"
        )

    @contextlib.contextmanager
    def error_describer(self):
        try:
            yield
        except ccxt.DDoSProtection as e:
            # raised upon rate limit issues, last response data might have details on what is happening
            if self.exchange_manager.exchange.should_log_on_ddos_exception(e):
                self.log_ddos_error(e)
            raise
        except ccxt.InvalidNonce as err:
            # use 2 index to get the caller of the context manager
            caller_function_name = inspect.stack()[2].function
            exchanges.log_time_sync_error(self.logger, self.name, err, caller_function_name)
            raise octobot_trading.errors.FailedRequest from err
        except ccxt.RequestTimeout as e:
            raise octobot_trading.errors.FailedRequest(f"Request timeout: {e}") from e
