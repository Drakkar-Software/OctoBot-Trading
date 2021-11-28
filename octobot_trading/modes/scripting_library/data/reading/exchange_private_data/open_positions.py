import octobot_trading.constants as trading_constants
import octobot_trading.personal_data as trading_personal_data


async def open_position_size(
        context=None,
        side=None
):
    # todo simplify
    trade_data = await trading_personal_data.get_pre_order_data(context.trader.exchange_manager,
                                                                symbol=context.symbol,
                                                                timeout=trading_constants.ORDER_DATA_FETCHING_TIMEOUT)
    current_symbol_holding, current_market_holding, market_quantity, current_price, symbol_market = trade_data

    return current_symbol_holding
    # todo handle reference market change
    # todo handle futures: its account balance from exchange
    # todo handle futures and return negative for shorts


async def average_open_pos_entry(
        context,
        side
                           ):
    return 50
