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

import octobot_commons.enums
import octobot_trading.enums as trading_enums
import octobot_commons.enums as commons_enums
import octobot_commons.errors as commons_errors
import octobot_commons.constants as commons_constants
import octobot_commons.databases as databases
import octobot_commons.logging as logging
import octobot_backtesting.api as backtesting_api
import octobot_trading.api as trading_api


class DisplayedElements:
    TABLE_KEY_TO_COLUMN = {
        "x": "Time",
        "y": "Value",
        "z": "Value",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
        "symbol": "Symbol",
    }

    def __init__(self, element_type=trading_enums.DisplayedElementTypes.CHART.value):
        self.nested_elements = {}
        self.elements = []
        self.type: str = element_type
        self.logger = logging.get_logger(self.__class__.__name__)

    async def fill_from_database(self, database_manager, exchange_name, symbol, time_frame, exchange_id, with_inputs=True):

        async with databases.MetaDatabase.database(database_manager) as meta_db:
            graphs_by_parts = {}
            inputs = []
            candles = []
            cached_values = []
            dbs = [meta_db.get_run_db(), meta_db.get_orders_db(), meta_db.get_trades_db()]
            if exchange_name:
                dbs.append(meta_db.get_symbol_db(exchange_name, symbol))
            for db in dbs:
                for table_name in await db.tables():
                    display_data = await db.all(table_name)
                    if table_name == trading_enums.DBTables.INPUTS.value:
                        inputs += display_data
                    if table_name == trading_enums.DBTables.CANDLES_SOURCE.value:
                        candles += display_data
                    if table_name == trading_enums.DBTables.CACHE_SOURCE.value:
                        cached_values += display_data
                    else:
                        try:
                            filtered_data = [display_element
                                             for display_element in display_data
                                             if display_element.get("symbol", symbol) == symbol
                                             and display_element.get("time_frame", time_frame) == time_frame]
                            chart = display_data[0]["chart"]
                            if chart in graphs_by_parts:
                                graphs_by_parts[chart][table_name] = filtered_data
                            else:
                                graphs_by_parts[chart] = {table_name: filtered_data}
                        except (IndexError, KeyError):
                            # some table have no chart
                            pass
            await self._add_candles(graphs_by_parts, candles, exchange_name, exchange_id, symbol, time_frame)
            await self._add_cached_values(graphs_by_parts, cached_values, time_frame)
            self._plot_graphs(graphs_by_parts)
            if with_inputs:
                self._display_inputs(inputs)

    def _plot_graphs(self, graphs_by_parts):
        for part, datasets in graphs_by_parts.items():
            with self.part(part, element_type=trading_enums.DisplayedElementTypes.CHART.value) as part:
                for title, dataset in datasets.items():
                    if not dataset:
                        continue
                    x = []
                    y = []
                    open = []
                    high = []
                    low = []
                    close = []
                    volume = []
                    text = []
                    color = []
                    size = []
                    shape = []
                    if dataset[0].get("x", None) is None:
                        x = None
                    if dataset[0].get("y", None) is None:
                        y = None
                    if dataset[0].get("open", None) is None:
                        open = None
                    if dataset[0].get("high", None) is None:
                        high = None
                    if dataset[0].get("low", None) is None:
                        low = None
                    if dataset[0].get("close", None) is None:
                        close = None
                    if dataset[0].get("volume", None) is None:
                        volume = None
                    if dataset[0].get("text", None) is None:
                        text = None
                    if dataset[0].get("color", None) is None:
                        color = None
                    if dataset[0].get("size", None) is None:
                        size = None
                    if dataset[0].get("shape", None) is None:
                        shape = None
                    own_yaxis = dataset[0].get("own_yaxis", False)
                    for data in dataset:
                        if x is not None:
                            x.append(data["x"])
                        if y is not None:
                            y.append(data["y"])
                        if open is not None:
                            open.append(data["open"])
                        if high is not None:
                            high.append(data["high"])
                        if low is not None:
                            low.append(data["low"])
                        if close is not None:
                            close.append(data["close"])
                        if volume is not None:
                            volume.append(data["volume"])
                        if text is not None:
                            text.append(data["text"])
                        if color is not None:
                            color.append(data["color"])
                        if size is not None:
                            size.append(data["size"])
                        if shape is not None:
                            shape.append(data["shape"])
                    part.plot(
                        kind=data.get("kind", None),
                        x=x,
                        y=y,
                        open=open,
                        high=high,
                        low=low,
                        close=close,
                        volume=volume,
                        title=title,
                        text=text,
                        x_type="date",
                        y_type=None,
                        mode=data.get("mode", None),
                        own_yaxis=own_yaxis,
                        color=color,
                        size=size,
                        symbol=shape)

    def _base_schema(self, tentacle):
        return {
            "type": "object",
            "title": f"{tentacle} inputs",
            "properties": {},
        }

    def _display_inputs(self, inputs):
        with self.part("inputs", element_type=trading_enums.DisplayedElementTypes.INPUT.value) as part:
            config_by_tentacles = {}
            config_schema_by_tentacles = {}
            tentacle_type_by_tentacles = {}
            for user_input_element in inputs:
                try:
                    tentacle = user_input_element["tentacle"]
                    tentacle_type_by_tentacles[tentacle] = user_input_element["tentacle_type"]
                    if tentacle not in config_schema_by_tentacles:
                        config_schema_by_tentacles[tentacle] = self._base_schema(tentacle)
                        config_by_tentacles[tentacle] = {}
                    config_by_tentacles[tentacle][user_input_element["name"].replace(" ", "_")] = \
                        user_input_element["value"]
                    self._generate_schema(config_schema_by_tentacles[tentacle], user_input_element)
                except KeyError as e:
                    self.logger.error(f"Error when loading user inputs for {tentacle}: missing {e}")
            for tentacle, schema in config_schema_by_tentacles.items():
                part.user_inputs(
                    "Inputs",
                    config_by_tentacles[tentacle],
                    schema,
                    tentacle,
                    tentacle_type_by_tentacles[tentacle],
                )

    def _generate_schema(self, main_schema, user_input_element):
        input_type_to_schema_type = {
            "int": "number",
            "float": "number",
            "boolean": "boolean",
            "options": "string",
            "multiple-options": "array",
        }
        properties = {}
        if title := user_input_element.get("name"):
            properties["title"] = title
        if def_val := user_input_element.get("def_val"):
            properties["default"] = def_val
        if min_val := user_input_element.get("min_val"):
            properties["minimum"] = min_val
        if max_val := user_input_element.get("max_val"):
            properties["maximum"] = max_val
        if input_type := user_input_element.get("input_type"):
            try:
                schema_type = input_type_to_schema_type[input_type]
                if schema_type == "boolean":
                    properties["format"] = "checkbox"
                if schema_type == "number":
                    if input_type == "float":
                        properties["multipleOf"] = 0.00000001
                if schema_type in ("string", "array"):
                    options = user_input_element.get("options", [])
                    default_value = def_val if def_val else options[0] if options else None
                    if schema_type == "string":
                        properties["default"] = default_value,
                        properties["format"] = "select"
                        properties["enum"] = options
                    elif schema_type == "array":
                        properties["format"] = "select2"
                        properties["minItems"] = 1
                        properties["uniqueItems"] = True
                        properties["items"] = {
                            "title": title,
                            "type": "string",
                            "default": default_value,
                            "enum": options
                        }
                properties["type"] = schema_type
            except KeyError as e:
                self.logger.error(f"Unknown input type: {e}")
        main_schema["properties"][title.replace(" ", "_")] = properties

    async def _add_cached_values(self, graphs_by_parts, cached_values, time_frame):
        for cached_value_metadata in cached_values:
            if cached_value_metadata.get(trading_enums.DBRows.TIME_FRAME.value, None) == time_frame:
                try:
                    chart = cached_value_metadata["chart"]
                    values = sorted(await self._get_cached_values_to_display(cached_value_metadata), key=lambda x: x["x"])
                    try:
                        graphs_by_parts[chart][cached_value_metadata[trading_enums.PlotAttributes.TITLE.value]] = values
                    except KeyError:
                        if chart not in graphs_by_parts:
                            graphs_by_parts[chart] = {}
                        try:
                            graphs_by_parts[chart] = \
                                {cached_value_metadata[trading_enums.PlotAttributes.TITLE.value]: values}
                        except KeyError:
                            graphs_by_parts[chart] = {trading_enums.PlotAttributes.TITLE.value: values}
                except KeyError:
                    # some table have no chart
                    pass

    async def _get_cached_values_to_display(self, cached_value_metadata):
        cache_file = cached_value_metadata[trading_enums.PlotAttributes.VALUE.value]
        cache_displayed_value = plotted_displayed_value = cached_value_metadata["cache_value"]
        kind = cached_value_metadata["kind"]
        mode = cached_value_metadata["mode"]
        own_yaxis = cached_value_metadata["own_yaxis"]
        condition = cached_value_metadata.get("condition", None)
        try:
            cache_database = databases.CacheDatabase(cache_file)
            cache_type = (await cache_database.get_metadata())[commons_enums.CacheDatabaseColumns.TYPE.value]
            if cache_type == databases.CacheTimestampDatabase.__name__:
                cache = await cache_database.get_cache()
                for cache_val in cache:
                    try:
                        if isinstance(cache_val[cache_displayed_value], bool):
                            plotted_displayed_value = self._get_cache_displayed_value(cache_val, cache_displayed_value)
                            if plotted_displayed_value is None:
                                self.logger.error(f"Impossible to plot {cache_displayed_value}: unset y axis value")
                                return []
                        else:
                            break
                    except KeyError:
                        pass
                    except Exception as e:
                        print(e)
                plotted_values = []
                for values in cache:
                    try:
                        if condition is None or condition == values[cache_displayed_value]:
                            x = values[commons_enums.CacheDatabaseColumns.TIMESTAMP.value] * 1000
                            y = values[plotted_displayed_value]
                            if not isinstance(x, list) and isinstance(y, list):
                                for y_val in y:
                                    plotted_values.append({
                                        "x": x,
                                        "y": y_val,
                                        "kind": kind,
                                        "mode": mode,
                                        "own_yaxis": own_yaxis,
                                    })
                            else:
                                plotted_values.append({
                                    "x": x,
                                    "y": y,
                                    "kind": kind,
                                    "mode": mode,
                                    "own_yaxis": own_yaxis,
                                })
                    except KeyError:
                        pass
                return plotted_values
            self.logger.error(f"Unhandled cache type to display: {cache_type}")
        except TypeError:
            self.logger.error(f"Missing cache type in {cache_file} metadata file")
        except commons_errors.DatabaseNotFoundError as ex:
            self.logger.warning(f"Missing cache values ({ex})")
        return []

    @staticmethod
    def _get_cache_displayed_value(cache_val, base_displayed_value):
        for key in cache_val.keys():
            separator_split_key = key.split(commons_constants.CACHE_RELATED_DATA_SEPARATOR)
            if base_displayed_value == separator_split_key[0] and len(separator_split_key) == 2:
                return key
        return None

    async def _add_candles(self, graphs_by_parts, candles_list, exchange_name, exchange_id, symbol, time_frame):
        for candles_metadata in candles_list:
            if candles_metadata.get("time_frame") == time_frame:
                try:
                    chart = candles_metadata["chart"]
                    candles = await self._get_candles_to_display(candles_metadata, exchange_name,
                                                                 exchange_id, symbol, time_frame)
                    try:
                        graphs_by_parts[chart][trading_enums.DBTables.CANDLES.value] = candles
                    except KeyError:
                        graphs_by_parts[chart] = {trading_enums.DBTables.CANDLES.value: candles}
                except KeyError:
                    # some table have no chart
                    pass

    async def _get_candles_to_display(self, candles_metadata, exchange_name, exchange_id, symbol, time_frame):
        if candles_metadata[trading_enums.DBRows.VALUE.value] == commons_constants.LOCAL_BOT_DATA:
            exchange_manager = trading_api.get_exchange_manager_from_exchange_id(exchange_id)
            array_candles = trading_api.get_symbol_historical_candles(
                trading_api.get_symbol_data(exchange_manager, symbol, allow_creation=False), time_frame
            )
            return [
                {
                    "x": time * 1000,
                    "open": array_candles[commons_enums.PriceIndexes.IND_PRICE_OPEN.value][index],
                    "high": array_candles[commons_enums.PriceIndexes.IND_PRICE_HIGH.value][index],
                    "low": array_candles[commons_enums.PriceIndexes.IND_PRICE_LOW.value][index],
                    "close": array_candles[commons_enums.PriceIndexes.IND_PRICE_CLOSE.value][index],
                    "volume": array_candles[commons_enums.PriceIndexes.IND_PRICE_VOL.value][index],
                    "kind": "candlestick",
                    "mode": "lines",
                }
                for index, time in enumerate(array_candles[commons_enums.PriceIndexes.IND_PRICE_TIME.value])
            ]
        db_candles = await backtesting_api.get_all_ohlcvs(candles_metadata[trading_enums.DBRows.VALUE.value],
                                                          exchange_name,
                                                          symbol,
                                                          octobot_commons.enums.TimeFrames(time_frame))
        return [
            {
                "x": db_candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value] * 1000,
                "open": db_candle[commons_enums.PriceIndexes.IND_PRICE_OPEN.value],
                "high": db_candle[commons_enums.PriceIndexes.IND_PRICE_HIGH.value],
                "low": db_candle[commons_enums.PriceIndexes.IND_PRICE_LOW.value],
                "close": db_candle[commons_enums.PriceIndexes.IND_PRICE_CLOSE.value],
                "volume": db_candle[commons_enums.PriceIndexes.IND_PRICE_VOL.value],
                "kind": "candlestick",
                "mode": "lines",
            }
            for index, db_candle in enumerate(db_candles)
        ]


    @contextlib.contextmanager
    def part(self, name, element_type=trading_enums.DisplayedElementTypes.CHART.value):
        element = DisplayedElements(element_type=element_type)
        self.nested_elements[name] = element
        yield element

    def plot(
        self,
        kind,
        x,
        y=None,
        open=None,
        high=None,
        low=None,
        close=None,
        volume=None,
        x_type="date",
        y_type=None,
        title=None,
        text=None,
        mode="lines",
        own_xaxis=False,
        own_yaxis=False,
        color=None,
        size=None,
        symbol=None,
    ):
        element = Element(
            kind,
            x,
            y,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
            x_type=x_type,
            y_type=y_type,
            title=title,
            text=text,
            mode=mode,
            own_xaxis=own_xaxis,
            own_yaxis=own_yaxis,
            type=trading_enums.DisplayedElementTypes.CHART.value,
            color=color,
            size=size,
            symbol=symbol
        )
        self.elements.append(element)

    def user_inputs(
        self,
        name,
        config_values,
        schema,
        tentacle,
        tentacle_type,
    ):
        element = Element(
            None,
            None,
            None,
            title=name,
            schema=schema,
            config_values=config_values,
            tentacle=tentacle,
            tentacle_type=tentacle_type,
            type=trading_enums.DisplayedElementTypes.INPUT.value
        )
        self.elements.append(element)

    def table(
        self,
        name,
        columns,
        rows,
        searches
    ):
        element = Element(
            None,
            None,
            None,
            title=name,
            columns=columns,
            rows=rows,
            searches=searches,
            type=trading_enums.DisplayedElementTypes.TABLE.value
        )
        self.elements.append(element)

    def value(self, label, value):
        element = Element(
            None,
            None,
            None,
            title=label,
            value=str(value),
            type=trading_enums.DisplayedElementTypes.VALUE.value
        )
        self.elements.append(element)

    def html_value(self, html):
        element = Element(
            None,
            None,
            None,
            html=html,
            type=trading_enums.DisplayedElementTypes.VALUE.value
        )
        self.elements.append(element)

    def is_empty(self):
        return not (self.nested_elements or self.elements)

    def to_json(self, name="root"):
        return {
            trading_enums.PlotAttributes.NAME.value: name,
            trading_enums.PlotAttributes.TYPE.value: self.type,
            trading_enums.PlotAttributes.DATA.value: {
                trading_enums.PlotAttributes.SUB_ELEMENTS.value: [
                    element.to_json(key)
                    for key, element in self.nested_elements.items()
                    if not element.is_empty()
                ],
                trading_enums.PlotAttributes.ELEMENTS.value: [
                    element.to_json()
                    for element in self.elements
                    if not element.is_empty()
                ]
            }
        }


class Element:

    def __init__(
        self,
        kind,
        x,
        y,
        open=None,
        high=None,
        low=None,
        close=None,
        volume=None,
        x_type=None,
        y_type=None,
        title=None,
        text=None,
        mode=None,
        own_xaxis=False,
        own_yaxis=False,
        value=None,
        config_values=None,
        schema=None,
        tentacle=None,
        tentacle_type=None,
        columns=None,
        rows=None,
        searches=None,
        type=trading_enums.DisplayedElementTypes.CHART.value,
        color=None,
        html=None,
        size=None,
        symbol=None,
    ):
        self.kind = kind
        self.x = x
        self.y = y
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.x_type = x_type
        self.y_type = y_type
        self.title = title
        self.text = text
        self.mode = mode
        self.own_xaxis = own_xaxis
        self.own_yaxis = own_yaxis
        self.value = value
        self.config_values = config_values
        self.schema = schema
        self.tentacle = tentacle
        self.tentacle_type = tentacle_type
        self.columns = columns
        self.rows = rows
        self.searches = searches
        self.type = type
        self.color = color
        self.html = html
        self.size = size
        self.symbol = symbol

    def to_json(self):
        return {
            trading_enums.PlotAttributes.KIND.value: self.kind,
            trading_enums.PlotAttributes.X.value: self.x,
            trading_enums.PlotAttributes.Y.value: self.y,
            trading_enums.PlotAttributes.OPEN.value: self.open,
            trading_enums.PlotAttributes.HIGH.value: self.high,
            trading_enums.PlotAttributes.LOW.value: self.low,
            trading_enums.PlotAttributes.CLOSE.value: self.close,
            trading_enums.PlotAttributes.VOLUME.value: self.volume,
            trading_enums.PlotAttributes.X_TYPE.value: self.x_type,
            trading_enums.PlotAttributes.Y_TYPE.value: self.y_type,
            trading_enums.PlotAttributes.TITLE.value: self.title,
            trading_enums.PlotAttributes.TEXT.value: self.text,
            trading_enums.PlotAttributes.MODE.value: self.mode,
            trading_enums.PlotAttributes.OWN_XAXIS.value: self.own_xaxis,
            trading_enums.PlotAttributes.OWN_YAXIS.value: self.own_yaxis,
            trading_enums.PlotAttributes.VALUE.value: self.value,
            trading_enums.PlotAttributes.CONFIG.value: self.config_values,
            trading_enums.PlotAttributes.SCHEMA.value: self.schema,
            trading_enums.PlotAttributes.TENTACLE.value: self.tentacle,
            trading_enums.PlotAttributes.TENTACLE_TYPE.value: self.tentacle_type,
            trading_enums.PlotAttributes.COLUMNS.value: self.columns,
            trading_enums.PlotAttributes.ROWS.value: self.rows,
            trading_enums.PlotAttributes.SEARCHES.value: self.searches,
            trading_enums.PlotAttributes.TYPE.value: self.type,
            trading_enums.PlotAttributes.COLOR.value: self.color,
            trading_enums.PlotAttributes.HTML.value: self.html,
            trading_enums.PlotAttributes.SIZE.value: self.size,
            trading_enums.PlotAttributes.SYMBOL.value: self.symbol,
        }

    def is_empty(self):
        return False

    @staticmethod
    def to_list(array, multiplier=1):
        if array is None:
            return None
        return [e * multiplier for e in array]
