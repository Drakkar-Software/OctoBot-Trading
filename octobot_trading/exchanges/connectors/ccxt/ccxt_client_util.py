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
import asyncio
import aiohttp
import copy
import logging
import typing
import ccxt
import ccxt.pro as ccxt_pro
import ccxt.async_support as async_ccxt

import octobot_commons.time_frame_manager as time_frame_manager
import octobot_commons.aiohttp_util as aiohttp_util
import octobot_commons.logging as commons_logging
import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.errors as errors
import octobot_trading.exchanges.connectors.ccxt.enums as ccxt_enums
import octobot_trading.exchanges.connectors.ccxt.ccxt_clients_cache as ccxt_clients_cache
import octobot_trading.exchanges.config.proxy_config as proxy_config_import
import octobot_trading.exchanges.util.exchange_util as exchange_util


def create_client(
    exchange_class, exchange_manager, logger, options, headers,
    additional_config, should_authenticate, unauthenticated_exchange_fallback=None,
    keys_adapter=None, allow_request_counter: bool = True
):
    """
    Exchange instance creation
    :return: the created ccxt (pro, async or sync) client
    """
    is_authenticated = False
    if not exchange_manager.exchange_only:
        # avoid logging version on temporary exchange_only exchanges
        exchange_type = exchange_util.get_exchange_type(exchange_manager)
        logger.info(f"Creating {exchange_class.__name__} {exchange_type.name} "
                    f"exchange with ccxt in version {ccxt.__version__}")
    if exchange_manager.ignore_config or exchange_manager.check_config(exchange_manager.exchange_name):
        try:
            auth_token_header_prefix = None
            key, secret, password, uid, auth_token = exchange_manager.get_exchange_credentials(
                exchange_manager.exchange_name
            )
            if keys_adapter:
                key, secret, password, uid, auth_token, auth_token_header_prefix = keys_adapter(
                    key, secret, password, uid, auth_token
                )
            if not (key and secret) and not exchange_manager.is_simulated and not exchange_manager.ignore_config:
                logger.warning(f"No exchange API key set for {exchange_manager.exchange_name}. "
                               f"Enter your account details to enable real trading on this exchange.")
            if should_authenticate and not exchange_manager.is_backtesting:
                client = instantiate_exchange(
                    exchange_class,
                    _get_client_config(
                        options, headers, additional_config,
                        api_key=key, secret=secret, password=password, uid=uid,
                        auth_token=auth_token, auth_token_header_prefix=auth_token_header_prefix
                    ),
                    exchange_manager.exchange_name,
                    exchange_manager.proxy_config,
                    allow_request_counter=allow_request_counter
                )
                is_authenticated = True
                if exchange_manager.check_credentials:
                    client.check_required_credentials()
            else:
                client = instantiate_exchange(
                    exchange_class,
                    _get_client_config(options, headers, additional_config),
                    exchange_manager.exchange_name,
                    exchange_manager.proxy_config,
                    allow_request_counter=allow_request_counter
                )
        except (ccxt.AuthenticationError, Exception) as e:
            if unauthenticated_exchange_fallback is None:
                return get_unauthenticated_exchange(
                    exchange_class, options, headers, additional_config,
                    exchange_manager.exchange_name, exchange_manager.proxy_config
                ), False
            return unauthenticated_exchange_fallback(e), False
    else:
        client = get_unauthenticated_exchange(
            exchange_class, options, headers, additional_config,
            exchange_manager.exchange_name, exchange_manager.proxy_config
        )
        logger.error("configuration issue: missing login information !")
    client.logger.setLevel(logging.INFO)
    return client, is_authenticated


async def close_client(client):
    await client.close()
    client.markets = {}
    client.markets_by_id = {}
    client.ids = []
    client.last_json_response = {}
    client.last_http_response = ""
    client.last_response_headers = {}
    client.markets_loading = None
    client.currencies = {}
    client.baseCurrencies = {}
    client.quoteCurrencies = {}
    client.currencies_by_id = {}
    client.codes = []
    client.symbols = {}
    client.accounts = []
    client.accounts_by_id = {}
    client.ohlcvs = {}
    client.trades = {}
    client.orderbooks = {}


def get_unauthenticated_exchange(
    exchange_class, options, headers, additional_config, identifier: str, proxy_config: proxy_config_import.ProxyConfig
) -> async_ccxt.Exchange:
    return instantiate_exchange(
        exchange_class, _get_client_config(options, headers, additional_config), identifier, proxy_config
    )


def instantiate_exchange(
    exchange_class, config: dict, identifier: str, proxy_config: proxy_config_import.ProxyConfig,
    allow_request_counter: bool = True
) -> async_ccxt.Exchange:
    client = exchange_class(config)
    _use_proxy_if_necessary(client, proxy_config)
    if constants.ENABLE_CCXT_REQUESTS_COUNTER and allow_request_counter:
        _use_request_counter(identifier, client)
    return client


def set_sandbox_mode(exchange_connector, is_sandboxed):
    try:
        exchange_connector.client.setSandboxMode(is_sandboxed)
    except ccxt.NotSupported as e:
        default_type = exchange_connector.client.options.get('defaultType', None)
        additional_info = f" in type {default_type}" if default_type else ""
        exchange_connector.logger.warning(f"{exchange_connector.name} does not support sandboxing {additional_info}: {e}")
        # raise exception to stop this exchange and prevent dealing with a real funds exchange
        raise e
    return None


def load_markets_from_cache(client, market_filter: typing.Union[None, typing.Callable[[dict], bool]] = None):
    client.set_markets(
        market
        for market in ccxt_clients_cache.get_exchange_parsed_markets(ccxt_clients_cache.get_client_key(client))
        if market_filter is None or market_filter(market)
    )


def set_markets_cache(client):
    if client.markets:
        ccxt_clients_cache.set_exchange_parsed_markets(
            ccxt_clients_cache.get_client_key(client), copy.deepcopy(list(client.markets.values()))
        )


def get_ccxt_client_login_options(exchange_manager):
    """
    :return: ccxt client login option dict, can be overwritten to custom exchange login
    """
    if exchange_manager.is_future:
        return {'defaultType': 'future'}
    if exchange_manager.is_margin:
        return {'defaultType': 'margin'}
    return {'defaultType': 'spot'}


def get_symbols(client, active_only):
    try:
        if active_only:
            return set(
                symbol
                for symbol in client.symbols
                if client.markets.get(symbol, {}).get(
                    enums.ExchangeConstantsMarketStatusColumns.ACTIVE.value, True
                ) in (True, None)
            )
        return set(client.symbols)
    except (AttributeError, TypeError):
        # ccxt exchange load_markets failed
        return set()


def get_time_frames(client):
    try:
        if isinstance(client, ccxt_pro.Exchange):
            # ccxt pro exchanges might have different timeframes in options
            options_time_frames = client.safe_value(client.options, 'timeframes')
            if options_time_frames:
                values = set([
                    time_frame
                    for time_frame in options_time_frames
                    if time_frame_manager.is_time_frame(time_frame)
                ])
                if values:
                    return values
        # use normal client timeframes (values of rest exchange)
        return set(client.timeframes)
    except (AttributeError, TypeError):
        # ccxt exchange describe() is invalid
        return set()


def get_exchange_pair(client, pair) -> str:
    if pair in client.symbols:
        try:
            return client.market(pair)["id"]
        except KeyError:
            pass
    raise ValueError(f'{pair} is not supported')


def get_pair_cryptocurrency(client, pair) -> str:
    if pair in client.symbols:
        try:
            return client.market(pair)["base"]
        except KeyError:
            pass
    raise ValueError(f'{pair} is not supported')


def get_contract_size(client, pair) -> float:
    return client.markets[pair][ccxt_enums.ExchangeConstantsMarketStatusCCXTColumns.CONTRACT_SIZE.value]


def get_fees(market_status) -> dict:
    return {
        enums.ExchangeConstantsMarketPropertyColumns.TAKER.value:
            market_status.get(enums.ExchangeConstantsMarketPropertyColumns.TAKER.value,
                              constants.CONFIG_DEFAULT_FEES),
        enums.ExchangeConstantsMarketPropertyColumns.MAKER.value:
            market_status.get(enums.ExchangeConstantsMarketPropertyColumns.MAKER.value,
                              constants.CONFIG_DEFAULT_FEES),
        enums.ExchangeConstantsMarketPropertyColumns.FEE.value:
            market_status.get(enums.ExchangeConstantsMarketPropertyColumns.FEE.value,
                              constants.CONFIG_DEFAULT_FEES)
    }


def add_headers(client, headers_dict):
    """
    Add new headers to ccxt client
    :param headers_dict: the additional header keys and values as dict
    """
    for header_key, header_value in headers_dict.items():
        client.headers[header_key] = header_value


def add_options(client, options_dict):
    """
    Add new options to ccxt client
    :param options_dict: the additional option keys and values as dict
    """
    for option_key, option_value in options_dict.items():
        client.options[option_key] = option_value


def converted_ccxt_common_errors(f):
    async def converted_ccxt_common_errors_wrapper(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except ccxt.RateLimitExceeded as err:
            raise errors.RateLimitExceeded(err) from err
        except ccxt.NotSupported as err:
            raise errors.NotSupported(err) from err
    return converted_ccxt_common_errors_wrapper


def _use_proxy_if_necessary(client, proxy_config: proxy_config_import.ProxyConfig):
    client.aiohttp_trust_env = proxy_config.aiohttp_trust_env
    if proxy_config.http_proxy:
        client.http_proxy = proxy_config.http_proxy
    if proxy_config.http_proxy_callback:
        client.http_proxy_callback = proxy_config.http_proxy_callback
    if proxy_config.https_proxy:
        client.https_proxy = proxy_config.https_proxy
    if proxy_config.https_proxy_callback:
        client.https_proxy_callback = proxy_config.https_proxy_callback
    if proxy_config.socks_proxy:
        client.socks_proxy = proxy_config.socks_proxy
    if proxy_config.socks_proxy_callback:
        client.socks_proxy_callback = proxy_config.socks_proxy_callback


def _get_client_config(
    options, headers, additional_config,
    api_key=None, secret=None, password=None, uid=None,
    auth_token=None, auth_token_header_prefix=None
):
    if auth_token:
        headers["Authorization"] = f"{auth_token_header_prefix or ''}{auth_token}"
    config = {
        'verbose': constants.ENABLE_CCXT_VERBOSE,
        'enableRateLimit': constants.ENABLE_CCXT_RATE_LIMIT,
        'timeout': constants.DEFAULT_REQUEST_TIMEOUT,
        'options': options,
        'headers': headers
    }
    if api_key is not None:
        config['apiKey'] = api_key
    if secret is not None:
        config['secret'] = secret
    if password is not None:
        config['password'] = password
    if uid is not None:
        config['uid'] = uid
    config.update(additional_config or {})
    return config


def _use_request_counter(identifier: str, ccxt_client: async_ccxt.Exchange):
    """
    Replaces the given exchange async session by an aiohttp_util.CounterClientSession
    WARNING: should only be called right after creating the exchange and on the same async loop as
    the one the exchange will be using (to avoid interrupting open requests from current session and loop errors)
    """
    # use session with request counter
    try:
        # 1. create ssl context and other required elements if necessary
        ccxt_client.open()
        previous_session = ccxt_client.session
        # 2. create patched session using the same params as a normal one
        # same as in ccxt.async_support.exchange.py#open()
        # connector = aiohttp.TCPConnector(ssl=self.ssl_context, loop=self.asyncio_loop, enable_cleanup_closed=True)
        new_connector = aiohttp.TCPConnector(
            ssl=ccxt_client.ssl_context, loop=ccxt_client.asyncio_loop, enable_cleanup_closed=True
        )
        counter_session = aiohttp_util.CounterClientSession(
            identifier,
            loop=ccxt_client.asyncio_loop,
            connector=new_connector,
            trust_env=previous_session.trust_env,
        )
        # 3. replace session
        ccxt_client.session = counter_session
        # 4. close replaced session in task to avoid making this function a coroutine
        asyncio.create_task(previous_session.close())
        commons_logging.get_logger(__name__).info(f"Request counter enabled for {identifier}")
    except Exception as err:
        commons_logging.get_logger(__name__).exception(
            err, True, f"Error when initializing {identifier} request counter: {err}"
        )


def ccxt_exchange_class_factory(exchange_name):
    return getattr(async_ccxt, exchange_name)
