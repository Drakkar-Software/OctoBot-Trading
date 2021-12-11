import octobot_trading.modes.scripting_library.data.reading.exchange_public_data as exchange_public_data
import octobot_trading.modes.scripting_library.orders.order_types as order_types
import octobot_trading.modes.scripting_library.TA.trigger.tag_triggered as tag_triggered
import octobot_trading.modes.scripting_library.data.reading.exchange_private_data.open_positions as open_positions
import octobot_trading.modes.scripting_library.UI.inputs.inputs as inputs
import octobot_trading.modes.scripting_library.data.reading.exchange_private_data as exchange_private_data
import tulipy as ti


async def activate_managed_order(ctx):
    ctx.managed_order.sl_types = {"at_low_high_title": "SL at the low/high",
                                  "based_on_p_title": "SL based on %",
                                  "based_on_atr_title": "Sl based on ATR"}
    ctx.managed_order.position_size_types = {"based_on_d": "Position size based on $ risk",
                                             "based_on_p": "Position size based on % risk"}
    ctx.managed_order.managed_order_active = True

    # SL
    ctx.managed_order.sl_type = await inputs.user_input(ctx, "choose SL type", "options",
                                                        ctx.managed_order.sl_types.at_low_high_title,
                                                        options=[ctx.managed_order.sl_types.at_low_high_title,
                                                                 ctx.managed_order.sl_types.based_on_p_title])
    # SL based on low/high
    if ctx.managed_order.sl_type == ctx.managed_order.sl_types.at_low_high_title:
        ctx.managed_order.sl_low_high_lookback = await inputs.user_input(ctx, "SL at low/highlookback period", "int", 3)
    # sl based on percent
    elif ctx.managed_order.sl_type == ctx.managed_order.sl_types.based_on_p_title:
        ctx.managed_order.sl_in_p_value = await inputs.user_input(ctx, "SL in %", "float", 0.5)

    elif ctx.managed_order.sl_type == ctx.managed_order.sl_types.based_on_atr_title:
        ctx.managed_order.atr_period = await inputs.user_input(ctx, "ATR Period", "int", 4)

    # position size
    ctx.managed_order.position_size_type = await inputs.user_input(ctx, "choose position Size Type", "options",
                                                                   ctx.managed_order.position_size_types.based_on_p,
                                                                   options=[
                                                                       ctx.managed_order.position_size_types.based_on_p,
                                                                       ctx.managed_order.position_size_types.based_on_d]
                                                                   )
    ctx.managed_order.risk_in_d_or_p = await inputs.user_input(ctx, "Risk % or $", "int", 3)

    # try limit in
    # todo handle on backtesting (maybe use always 1m to check if it got filled)
    ctx.managed_order.try_limit_in = await inputs.user_input(ctx, "try to limit in", "boolean", False)
    if ctx.managed_order.try_limit_in:
        ctx.managed_order.slippage_limit = await inputs.user_input(ctx, "Slippage Limit: can be % or price", "float",
                                                                   40)
        ctx.managed_order.market_in_if_limit_fails = await inputs.user_input(ctx, "try to limit in", "boolean", True)

    # TP
    ctx.managed_order.tp_is_activated = await inputs.user_input(ctx, "Activate TP based on Risk Reward", "boolean",
                                                                False)
    if ctx.managed_order.tp_is_activated:
        ctx.managed_order.tp_rr = await inputs.user_input(ctx, "TP Risk Reward target", "float", 2)
        ctx.managed_order.use_scaled_tp = await inputs.user_input(ctx, "Use Scaled Limit for Take Profit. (scales "
                                                                       "from min RR to max RR to reach an average RR "
                                                                       "as defined above in target RR)", "boolean",
                                                                  True)
        if ctx.managed_order.use_scaled_tp:
            ctx.managed_order.tp_min_rr = await inputs.user_input(ctx, "TP min Risk Reward target", "float", 1)
            ctx.managed_order.tp_max_rr = await inputs.user_input(ctx, "TP max Risk Reward target", "float", 3)
            ctx.managed_order.tp_order_count = await inputs.user_input(ctx, "TP order count", "int", 3, 3)


async def execute_managed_order(ctx, side="long"):
    if not ctx.managed_order.managed_order_active:
        raise RuntimeError("managed order needs to be activated first. Use activate_managed_order(ctx) in your script "
                           "and consider reading the documentation")

    # SL
    sl_price = 0
    sl_in_p = 0
    current_price_val = exchange_public_data.Close(ctx)[-1]

    # SL based on low/high
    if ctx.managed_order.sl_type == ctx.managed_order.sl_types.at_low_high_title:
        if side == "long":
            sl_price = ti.min(exchange_public_data.Low(ctx), ctx.managed_order.sl_low_high_lookback)[-1]
            sl_in_p = (current_price_val - sl_price) / current_price_val * 100

        elif side == "short":
            sl_price = ti.max(exchange_public_data.High(ctx), ctx.managed_order.sl_low_high_lookback)[-1]
            sl_in_p = (sl_price - current_price_val) / current_price_val * 100
        else:
            raise RuntimeError('Side needs to be "long" or "short" for your managed order')

    # SL based on percent
    elif ctx.managed_order.sl_type == ctx.managed_order.sl_types.based_on_p_title:
        if side == "long":
            sl_in_p = ctx.managed_order.sl_in_p_val
            sl_price = current_price_val * (1 - (sl_in_p / 100))
        elif side == "short":
            sl_in_p = ctx.managed_order.sl_in_p_val
            sl_price = current_price_val * (1 + (sl_in_p / 100))
        else:
            raise RuntimeError('Side needs to be "long" or "short" for your managed order')

    # SL based on ATR
    if ctx.managed_order.sl_type == ctx.managed_order.sl_types.at_low_high_title:
        if side == "long":
            sl_price = current_price_val - ti.atr(exchange_public_data.High(ctx), exchange_public_data.Low(ctx),
                                                  exchange_public_data.Close(ctx), ctx.managed_order.atr_period)[-1]
            sl_in_p = (current_price_val - sl_price) / current_price_val * 100

        elif side == "short":
            sl_price = current_price_val + ti.atr(exchange_public_data.High(ctx), exchange_public_data.Low(ctx),
                                                  exchange_public_data.Close(ctx), ctx.managed_order.atr_period)[-1]
            sl_in_p = (sl_price - current_price_val) / current_price_val * 100
        else:
            raise RuntimeError('Side needs to be "long" or "short" for your managed order')

        # position size
    position_size_market = 0
    position_size_limit = 0
    limit_fee = 0 # todo get fee also for real trading
    market_fee = 0.1
    # position size based on dollar/reference market risk
    if ctx.managed_order.position_size_type == ctx.managed_order.position_size_types.based_on_d:
        position_size_market = (ctx.managed_order.risk_in_d_or_p / (sl_in_p + (market_fee + market_fee))) / 0.01
        position_size_limit = (ctx.managed_order.risk_in_d_or_p / (sl_in_p + (limit_fee + market_fee))) / 0.01

        # cut the position size so that it aligns with target risk
        current_open_position_size = await open_positions.open_position_size(ctx, side=side)
        position_size_limit = position_size_limit - current_open_position_size
        position_size_market = position_size_market - current_open_position_size
        if position_size_limit or position_size_market < 0:
            raise RuntimeError("Managed order cant open a new position, maximum risk is reached")

    # position size based on percent of total account balance
    elif ctx.managed_order.position_size_type == ctx.managed_order.position_size_types.based_on_p:
        current_total_acc_balance = await exchange_private_data.total_account_balance(ctx)
        risk_in_d = (ctx.managed_order.risk_in_d_or_p / 100) * current_total_acc_balance
        position_size_market = (risk_in_d / (sl_in_p + (2 * market_fee))) / 0.01
        position_size_limit = (ctx.managed_order.risk_in_d_or_p / (sl_in_p + (limit_fee + market_fee))) / 0.01

        # cut the position size so that it aligns with target risk
        current_open_position_size = await open_positions.open_position_size(ctx, side=side)
        position_size_limit = position_size_limit - current_open_position_size
        position_size_market = position_size_market - current_open_position_size
        if position_size_limit or position_size_market < 0:
            raise RuntimeError("Managed order cant open a new position, maximum position size is reached")

    # create orders
    if side == "long":
        side = "buy"
    elif side == "short":
        side = "sell"

    # limit or market in
    if ctx.managed_order.try_limit_in:
        await order_types.trailing_limit(ctx, amount=position_size_limit, side=side, min_offset=0, max_offset=0,
                                         slippage_limit=ctx.managed_order.slippage_limit, tag="try_limit_in")
        # wait for limit to get filled
        if tag_triggered.tagged_order_unfilled("try_limit_in"):
            unfilled_amount = tag_triggered.tagged_order_unfilled_amount("try_limit_in")
            if unfilled_amount != position_size_limit:
                position_size_market = 50  # todo calc smaller size cause of fees
            await order_types.market(ctx, side=side, amount=position_size_market)
    # market in only
    else:
        await order_types.market(ctx, side=side, amount=position_size_market)

    await order_types.stop_loss(ctx, target_position=0, offset=sl_price)

    # take profit
    if ctx.managed_order.tp_is_activated:
        profit_in_p = ctx.managed_order.tp_rr * (sl_in_p * (-1))
        if not ctx.managed_order.use_scaled_tp:
            await order_types.limit(ctx, target_position=0, offset=profit_in_p)
        else:
            scale_from = 10 # todo
            scale_to = 10 # todo
            await order_types.scaled_limit(ctx, target_position=0, side=side, scale_from=scale_from, scale_to=scale_to,
                                           order_count=ctx.managed_order.tp_order_count)
