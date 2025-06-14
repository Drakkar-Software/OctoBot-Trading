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
import ccxt

import octobot_commons.logging as commons_logging
import octobot_commons.html_util as html_util
import octobot_trading.constants as constants
import octobot_trading.errors as errors


def retried_failed_network_request(
    attempts=constants.FAILED_NETWORK_REQUEST_RETRY_ATTEMPTS,
    delay=constants.DEFAULT_FAILED_REQUEST_RETRY_TIME,
):
    # inner level to allow passing params to the decorator
    def inner_retried_failed_network_request(func):
        async def _retried_failed_network_request_wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    resp = await func(*args, **kwargs)
                    if attempt > 0:
                        commons_logging.get_logger(f"retried_failed_network_request").info(
                            f"{func.__name__} succeeded after {attempt+1} attempts."
                        )
                    return resp
                except (
                    ccxt.RequestTimeout, ccxt.ExchangeNotAvailable, ccxt.InvalidNonce, errors.RetriableFailedRequest
                ) as err:
                    commons_logging.get_logger(f"retried_failed_network_request").warning(
                        f"{func.__name__} raised {html_util.get_html_summary_if_relevant(err)} "
                        f"({err.__class__.__name__}) [attempts {attempt+1}/{attempts}]. Retrying in {delay} seconds."
                    )
                    if attempt < attempts - 1:
                        # can happen: retry
                        await asyncio.sleep(delay)
                    else:
                        raise
                # raise any other error
            return None
        return _retried_failed_network_request_wrapper
    return inner_retried_failed_network_request
