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

import octobot_trading.modes.scripting_library.data.reading.exchange_public_data as exchange_public_data
import octobot_trading.modes.scripting_library.orders.order_types as order_types
import octobot_trading.modes.scripting_library.TA.trigger.tag_triggered as tag_triggered
import octobot_trading.modes.scripting_library.data.reading.exchange_private_data.open_positions as open_positions
import octobot_trading.modes.scripting_library.data.reading.exchange_private_data.account_balance as account_balance
import octobot_trading.modes.scripting_library.UI.inputs.user_inputs as user_inputs
import octobot_trading.modes.scripting_library.data.reading.exchange_private_data as exchange_private_data
import octobot_trading.constants as trading_constants
import octobot_trading.enums as trading_enums
import tulipy as ti  # TODO add requirement or import in if
import random as random


class ManagedOrdersSettings:
    def __init__(self, context):
        self.context = context
        self.entry_types=None
        self.entry_type=None
        self.shotgun_entry_types=None
        self.shotgun_entry_type=None
        self.sl_types = None
        self.position_size_types = None
        self.managed_order_active = None
        self.sl_type = None
        self.sl_low_high_lookback = None
        self.sl_low_high_buffer = None
        self.sl_in_p_value = None
        self.atr_period = None
        self.position_size_type = None
        self.risk_in_d_or_p = None
        self.total_risk_in_d_or_p = None
        self.entry_type = None
        self.slippage_limit = None
        self.market_in_if_limit_fails = None
        self.tp_types = None
        self.tp_type = None
        self.recreate_exits = None
        self.tp_rr = None
        self.tp_in_p = None
        self.use_scaled_tp = None
        self.tp_min_rr = None
        self.tp_max_rr = None
        self.tp_order_count = None
        self.initialized = False

    async def initialize(self):
        self.entry_types = {"market_in": "Market in",
                            "try_limit_in": "Try to limit in",
                            "shotgun_order": "Shotgun entry orders"}
        self.shotgun_entry_types = {"time_grid_orders": "spread entry orders across time",
                                    "scaled_entry": "spread limit orders over a price range"}
        self.sl_types = {"at_low_high_title": "SL at the low/high",
                         "based_on_p_title": "SL based on %",
                         "based_on_atr_title": "Sl based on ATR"}
        self.tp_types = {"no_tp_title": "dont use managed Take Profit",
                         "tp_based_on_rr_title": "Take Profit based on Risk Reward",
                         "tp_based_on_p_title": "Take Profit based on fixed %"}
        self.position_size_types = {"based_on_d": "Position size based on $ risk",
                                    "based_on_p": "Position size based on % risk"}
        self.managed_order_active = True

        # entry type
        self.entry_type = await user_inputs.user_input(self.context, "entry type", "options",
                                                    self.entry_types["market_in"],
                                                    options=[self.entry_types["market_in"],
                                                             self.entry_types["try_limit_in"],
                                                             self.entry_types["shotgun_order"]])
        # entry: try limit in
        if self.entry_type == self.entry_types["try_limit_in"]:
            self.slippage_limit = decimal.Decimal(
                str(await user_inputs.user_input(self.context, "Slippage Limit: can be % or price",
                                                 "float", 40)))
            self.market_in_if_limit_fails = await user_inputs.user_input(self.context, "try to limit in", "boolean",
                                                                         True)
        # shotgun entry
        elif self.entry_type == self.entry_types["shotgun_order"]:
            self.shotgun_entry_type = await user_inputs.user_input(self.context, "shotgun entry type", "options",
                                                           self.shotgun_entry_types["scaled_entry"],
                                                           options=[self.shotgun_entry_types["scaled_entry"],
                                                                    self.shotgun_entry_types["time_grid_orders"]])

        self.recreate_exits = await user_inputs.user_input(self.context,
                                                           "Recreate exit orders on new entrys: When "
                                                           "enabled exit orders will be replaced with "
                                                           "new ones based on the current candle", "boolean", False)
        # SL
        self.sl_type = await user_inputs.user_input(self.context, "SL type", "options",
                                                    self.sl_types["based_on_p_title"],
                                                    options=[self.sl_types["at_low_high_title"],
                                                             self.sl_types["based_on_p_title"],
                                                             self.sl_types["based_on_atr_title"]])
        # SL based on low/high
        if self.sl_type == self.sl_types["at_low_high_title"]:
            self.sl_low_high_lookback = decimal.Decimal(
                str(await user_inputs.user_input(self.context, "SL at low/high lookback period",
                                                 "int", 3)))
            self.sl_low_high_buffer = decimal.Decimal(
                str(await user_inputs.user_input(self.context, "SL at low/high buffer in %",
                                                 "float", 0.2)))
        # sl based on percent
        elif self.sl_type == self.sl_types["based_on_p_title"]:
            self.sl_in_p_value = decimal.Decimal(
                str(await user_inputs.user_input(self.context, "SL in %", "float", 0.5)))

        elif self.sl_type == self.sl_types["based_on_atr_title"]:
            self.atr_period = decimal.Decimal(str(await user_inputs.user_input(self.context, "ATR Period", "int", 4)))

        # position size
        self.position_size_type = await user_inputs.user_input(self.context, "position Size Type", "options",
                                                               self.position_size_types["based_on_p"],
                                                               options=[
                                                                   self.position_size_types["based_on_p"],
                                                                   self.position_size_types["based_on_d"]]
                                                               )
        self.risk_in_d_or_p = decimal.Decimal(str(await user_inputs.user_input(self.context,
                                                                               "risk per trade in % or $",
                                                                               "float", 0.5)))
        self.total_risk_in_d_or_p = decimal.Decimal(str(await user_inputs.user_input(self.context,
                                                                                     "total risk in % or $",
                                                                                     "float", 2)))


        # TP
        self.tp_type = await user_inputs.user_input(self.context, "Take profit type", "options",
                                                    self.tp_types["tp_based_on_rr_title"],
                                                    options=[self.tp_types["no_tp_title"],
                                                             self.tp_types["tp_based_on_rr_title"],
                                                             self.tp_types["tp_based_on_p_title"]])

        if self.tp_type == self.tp_types["tp_based_on_rr_title"]:
            self.use_scaled_tp = await user_inputs.user_input(self.context,
                                                              "Scaled limit take profit. (spreads limit orders "
                                                              "from min RR to max RR)", "boolean",
                                                              False)
            if not self.use_scaled_tp:
                self.tp_rr = decimal.Decimal(
                    str(await user_inputs.user_input(self.context, "TP Risk Reward target", "float", 2)))

            else:
                self.tp_min_rr = decimal.Decimal(
                    str(await user_inputs.user_input(self.context, "TP min Risk Reward target", "float", 1)))
                self.tp_max_rr = decimal.Decimal(
                    str(await user_inputs.user_input(self.context, "TP max Risk Reward target", "float", 3)))
                self.tp_order_count = decimal.Decimal(
                    str(await user_inputs.user_input(self.context, "TP order count", "int", 3, 3)))
        elif self.tp_type == self.tp_types["tp_based_on_p_title"]:
            self.tp_in_p = await user_inputs.user_input(self.context, "TP in %", "float", 2, 0)

        self.initialized = True


async def activate_managed_orders(ctx):
    orders_settings = ManagedOrdersSettings(ctx)
    await orders_settings.initialize()
    return orders_settings


async def managed_order(ctx, side="long", orders_settings=None):
    managed_orders_settings = orders_settings or ManagedOrdersSettings(ctx)
    if not managed_orders_settings.initialized:
        await managed_orders_settings.initialize()

    # SL
    sl_price = trading_constants.ZERO
    sl_in_p = trading_constants.ZERO
    current_price_val = decimal.Decimal(str(exchange_public_data.Close(ctx)[-1]))

    # SL based on low/high
    if managed_orders_settings.sl_type == managed_orders_settings.sl_types["at_low_high_title"]:
        if side == "long":
            sl_price = decimal.Decimal(
                str(ti.min(exchange_public_data.Low(ctx), int(managed_orders_settings.sl_low_high_lookback))[-1]))\
                       * (1 - (managed_orders_settings.sl_low_high_buffer / 100))
            sl_in_p = (current_price_val - sl_price) / current_price_val * 100

        elif side == "short":
            sl_price = decimal.Decimal(
                str(ti.max(exchange_public_data.High(ctx), int(managed_orders_settings.sl_low_high_lookback))[-1]))\
                       * (1 + (managed_orders_settings.sl_low_high_buffer / 100))
            sl_in_p = (sl_price - current_price_val) / current_price_val * 100
        else:
            raise RuntimeError('Side needs to be "long" or "short" for your managed order')

    # SL based on percent
    elif managed_orders_settings.sl_type == managed_orders_settings.sl_types["based_on_p_title"]:
        if side == "long":
            sl_in_p = managed_orders_settings.sl_in_p_value
            sl_price = current_price_val * (1 - (sl_in_p / 100))
        elif side == "short":
            sl_in_p = managed_orders_settings.sl_in_p_value
            sl_price = current_price_val * (1 + (sl_in_p / 100))
        else:
            raise RuntimeError('Side needs to be "long" or "short" for your managed order')

    # SL based on ATR
    if managed_orders_settings.sl_type == managed_orders_settings.sl_types["based_on_atr_title"]:
        if side == "long":
            sl_price = current_price_val - decimal.Decimal(
                str(ti.atr(exchange_public_data.High(ctx), exchange_public_data.Low(ctx),
                           exchange_public_data.Close(ctx), int(managed_orders_settings.atr_period))[
                        -1]))
            sl_in_p = (current_price_val - sl_price) / current_price_val * 100

        elif side == "short":
            sl_price = current_price_val + decimal.Decimal(
                str(ti.atr(exchange_public_data.High(ctx), exchange_public_data.Low(ctx),
                           exchange_public_data.Close(ctx), int(managed_orders_settings.atr_period))[
                        -1]))
            sl_in_p = (sl_price - current_price_val) / current_price_val * 100
        else:
            raise RuntimeError('Side needs to be "long" or "short" for your managed order')

    # position size
    position_size_market = trading_constants.ZERO
    position_size_limit = trading_constants.ZERO
    limit_fee = trading_constants.ZERO  # todo get fee also for real trading
    market_fee = decimal.Decimal("0.1")
    # position size based on dollar/reference market risk
    if managed_orders_settings.position_size_type == managed_orders_settings.position_size_types["based_on_d"]:
        position_size_market = (managed_orders_settings.risk_in_d_or_p / (
                sl_in_p + (market_fee + market_fee))) / decimal.Decimal("0.01")
        position_size_limit = (managed_orders_settings.risk_in_d_or_p / (
                sl_in_p + (limit_fee + market_fee))) / decimal.Decimal("0.01")
        max_position_size = (managed_orders_settings.total_risk_in_d_or_p / (
                sl_in_p + (2 * market_fee))) / decimal.Decimal("0.01")

        # cut the position size so that it aligns with target risk
        current_open_position_size = open_positions.open_position_size(ctx, side="both")
        if current_open_position_size + position_size_market > max_position_size:
            position_size_limit = max_position_size - current_open_position_size
            position_size_market = max_position_size - current_open_position_size

    # position size based on percent of total account balance
    elif managed_orders_settings.position_size_type == managed_orders_settings.position_size_types["based_on_p"]:
        current_total_acc_balance = await exchange_private_data.total_account_balance(ctx)
        risk_in_d = (managed_orders_settings.risk_in_d_or_p / 100) * current_total_acc_balance
        total_risk_in_d = (managed_orders_settings.total_risk_in_d_or_p / 100) * current_total_acc_balance
        position_size_market = (risk_in_d / (sl_in_p + (2 * market_fee))) / decimal.Decimal("0.01")
        position_size_limit = (risk_in_d / (sl_in_p + (limit_fee + market_fee))) / decimal.Decimal("0.01")
        current_open_position_size = open_positions.open_position_size(ctx, side="both")
        max_position_size = (total_risk_in_d / (sl_in_p + (2 * market_fee))) / decimal.Decimal("0.01") - (current_open_position_size * (market_fee/100))
        max_buying_power = await account_balance.available_account_balance(ctx, side="buy")
        if max_buying_power < position_size_market:
            position_size_market = max_buying_power
            position_size_limit = max_buying_power

        # cut the position size so that it aligns with target risk
        if current_open_position_size + position_size_market > max_position_size:
            position_size_limit = max_position_size - current_open_position_size
            position_size_market = max_position_size - current_open_position_size

    if position_size_market <= 0:
        # its not logging
        ctx.logger.info("Managed order cant open a new position, maximum position size is reached")

    # create orders
    else:
        if side == "long":
            side = trading_enums.TradeOrderSide.BUY.value
        elif side == "short":
            side = trading_enums.TradeOrderSide.SELL.value

        # either replace existing exits or keep them and add new exits for new entry
        exit_side = None
        exit_amount = None
        exit_target_position = None
        if managed_orders_settings.recreate_exits:
            exit_target_position = 0
            exit_order_tag = f"managed_order {side} exit:"
            entry_order_tag = f"managed_order {side} entry:"
        else:  # keep existing exit orders and only add new exits
            exit_side = "sell" if side == "buy" else "buy"
            exit_amount = position_size_market
            order_tag_id = random.randint(0, 999999999) # {exchange_public_data.current_candle_time(ctx)})"  # todo use something unique to avoid canceling eventual other orders in the same candle
            exit_order_tag = f"managed_order {side} exit (id: {order_tag_id}"
            entry_order_tag = f"managed_order {side} exit (id: {order_tag_id}"

        # entry

        # try limit in
        # todo + handle on backtesting (maybe use always 1m to check if it got filled)
        if managed_orders_settings.entry_type == managed_orders_settings.entry_types["try_limit_in"]:
            await order_types.trailing_limit(ctx, amount=position_size_limit, side=side, min_offset=0, max_offset=0,
                                             slippage_limit=managed_orders_settings.slippage_limit,
                                             tag=entry_order_tag)
            # wait for limit to get filled

            if tag_triggered.tagged_order_unfilled("managed order long entry:"):
                unfilled_amount = tag_triggered.tagged_order_unfilled_amount("managed order long entry:")
                if unfilled_amount != position_size_limit:
                    position_size_market = 50  # todo calc smaller size cause of fees
                await order_types.market(ctx, side=side, amount=position_size_market, tag=entry_order_tag)

        # market in only
        elif managed_orders_settings.entry_type == managed_orders_settings.entry_types["market_in"]:
            await order_types.market(ctx, side=side, amount=position_size_market, tag=entry_order_tag)

        # shotgun orders
        elif managed_orders_settings.entry_type == managed_orders_settings.entry_types["shotgun_order"]:
            if managed_orders_settings.shotgun_entry_type == managed_orders_settings.shotgun_entry_types["time_grid_orders"]:
                print("shotgun orders not implemented yet")
            elif managed_orders_settings.shotgun_entry_type == managed_orders_settings.shotgun_entry_types["scaled_entry"]:
                print("shotgun orders not implemented yet")

        # stop loss
        await order_types.stop_loss(ctx, side=exit_side, amount=exit_amount, target_position=exit_target_position,
                                    offset=f"@{sl_price}", one_cancels_the_other=True, tag=exit_order_tag)
        # take profit
        if managed_orders_settings.tp_type == managed_orders_settings.tp_types["tp_based_on_rr_title"]:
            profit_in_p = managed_orders_settings.tp_rr * sl_in_p
            if not managed_orders_settings.use_scaled_tp:
                await order_types.limit(ctx, side=exit_side, amount=exit_amount, target_position=exit_target_position,
                                        offset=f"{profit_in_p}%e", one_cancels_the_other=True, tag=exit_order_tag)
            else:
                scale_from = 10  # todo
                scale_to = 10  # todo
                await order_types.scaled_limit(ctx, side=exit_side, amount=exit_amount,
                                               target_position=exit_target_position, scale_from=scale_from,
                                               scale_to=scale_to, order_count=managed_orders_settings.tp_order_count,
                                               one_cancels_the_other=True, tag=exit_order_tag)

        # take profit
        elif managed_orders_settings.tp_type == managed_orders_settings.tp_types["tp_based_on_p_title"]:
            await order_types.limit(ctx, side=exit_side, amount=exit_amount, target_position=exit_target_position,
                                    offset=f"{managed_orders_settings.tp_in_p}%e", one_cancels_the_other=True,
                                    tag=exit_order_tag)
