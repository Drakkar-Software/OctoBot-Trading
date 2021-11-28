import decimal
import re
from octobot_trading.modes.scripting_library.data.reading.exchange_public_data import current_price
from octobot_trading.modes.scripting_library.data.reading.exchange_private_data.open_positions \
    import average_open_pos_entry


async def get_offset(context=None,
                     offset_in=None,
                     side="buy"):
    offset_in = str(offset_in)  # if user types in an int or float
    offset_type = re.sub(r"\d|\.", "", offset_in)  # todo different offsets @65100 5% e5%  e500 500
    offset_value = decimal.Decimal(offset_in.replace(offset_type, ""))

    if offset_type == "":
        test = await current_price(context)
        current_price_val = decimal.Decimal(await current_price(context))
        if side == "buy":
            return current_price_val + offset_value
        else:
            return current_price_val - offset_value

    elif offset_type == "%":
        current_price_val = decimal.Decimal(await current_price(context))
        if side == "buy":
            return current_price_val * (1 + (offset_value / 100))
        else:
            return current_price_val * (1 - (offset_value / 100))

    elif offset_type == "e%":
        average_open_pos_entry_val = await average_open_pos_entry(context)
        if side == "buy":
            return average_open_pos_entry_val * (1 + (offset_value / 100))
        else:
            return average_open_pos_entry_val * (1 - (offset_value / 100))

    elif offset_type == "e":
        average_open_pos_entry_val = await average_open_pos_entry(context)
        if side == "buy":
            return average_open_pos_entry_val + offset_value
        else:
            return average_open_pos_entry_val - offset_value

    elif offset_type == "@":
        return offset_value

    else:
        raise RuntimeError(
            "make sure to use a supported syntax for offset, supported parameters are: @65100 5% e5% e500")
