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
import decimal

import octobot_commons.constants as constants
import octobot_trading.modes.script_keywords.basic_keywords.user_inputs as user_inputs
import octobot_trading.enums as enums
import octobot_trading.errors as errors


async def user_select_leverage(
        ctx,
        def_val=1,
        order=None,
        name="leverage"):
    return await user_inputs.user_input(ctx, name, "int", def_val, order=order)


async def user_select_emit_trading_signals(ctx, identifier, def_val=False):
    await user_inputs.user_input(ctx, constants.CONFIG_TRADING_SIGNALS_STRATEGY, "text", identifier,
                                 show_in_summary=False, show_in_optimizer=False)
    return await user_inputs.user_input(ctx, "emit_trading_signals", "boolean", def_val,
                                        show_in_summary=False, show_in_optimizer=False)


async def set_leverage(ctx, leverage):
    if ctx.exchange_manager.is_future:
        side = None
        try:
            await ctx.exchange_manager.trader.set_leverage(ctx.symbol, side, decimal.Decimal(str(leverage)))
        except errors.ContractExistsError as e:
            ctx.logger.debug(str(e))
        except NotImplementedError as e:
            ctx.logger.exception(e, True, str(e))
        except AttributeError:
            # TODO remove this except when bybit tentacle is up
            ctx.logger.warning("TODO: rebase tentacles when bybit exchange is up")
        except Exception as e:
            ctx.logger.exception(e, True, str(e))


async def set_partial_take_profit_stop_loss(ctx, tp_sl_mode=enums.TakeProfitStopLossMode.PARTIAL.value):
    if ctx.exchange_manager.is_future:
        await ctx.exchange_manager.trader.set_symbol_take_profit_stop_loss_mode(
            ctx.symbol, enums.TakeProfitStopLossMode(tp_sl_mode)
        )
