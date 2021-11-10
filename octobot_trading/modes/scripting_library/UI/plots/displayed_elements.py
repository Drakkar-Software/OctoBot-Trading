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
import octobot_trading.constants as trading_constants
import octobot_trading.modes.scripting_library.data as scripting_data
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
        "pair": "Pair",
    }

    def __init__(self, element_type=trading_enums.DisplayedElementTypes.CHART.value):
        self.nested_elements = {}
        self.elements = []
        self.type: str = element_type

    async def fill_from_database(self, database_name, exchange_id):
        async with scripting_data.DBReader.database(database_name) as reader:
            graphs_by_parts = {}
            inputs = []
            candles = []
            for table_name in await reader.tables():
                display_data = await reader.all(table_name)
                if table_name == trading_enums.DBTables.INPUTS.value:
                    inputs += display_data
                if table_name == trading_enums.DBTables.CANDLES_SOURCE.value:
                    candles += display_data
                else:
                    try:
                        chart = display_data[0]["chart"]
                        if chart in graphs_by_parts:
                            graphs_by_parts[chart][table_name] = display_data
                        else:
                            graphs_by_parts[chart] = {table_name: display_data}
                    except KeyError:
                        # some table have no chart
                        pass
            await self._add_candles(graphs_by_parts, candles, exchange_id)
            self._plot_graphs(graphs_by_parts)
            self._display_inputs(inputs)

    def _plot_graphs(self, graphs_by_parts):
        for part, datasets in graphs_by_parts.items():
            with self.part(part, element_type=trading_enums.DisplayedElementTypes.CHART.value) as part:
                for title, dataset in datasets.items():
                    x = []
                    y = []
                    open = []
                    high = []
                    low = []
                    close = []
                    volume = []
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
                        x_type="date",
                        y_type=None,
                        mode=data.get("mode", None))

    def _base_schema(self):
        return {
            "type": "object",
            "title": "Inputs",
            "properties": {},
        }

    def _display_inputs(self, inputs):
        with self.part("inputs", element_type=trading_enums.DisplayedElementTypes.INPUT.value) as part:
            config_by_tentacles = {}
            config_schema_by_tentacles = {}
            for user_input_element in inputs:
                tentacle = user_input_element["tentacle"]
                if tentacle not in config_schema_by_tentacles:
                    config_schema_by_tentacles[tentacle] = self._base_schema()
                    config_by_tentacles[tentacle] = {}
                config_by_tentacles[tentacle][user_input_element["name"].replace(" ", "-")] = \
                    user_input_element["value"]
                self._generate_schema(config_schema_by_tentacles[tentacle], user_input_element)
            for tentacle, schema in config_schema_by_tentacles.items():
                part.user_inputs(
                    "Inputs",
                    config_by_tentacles[tentacle],
                    schema,
                    tentacle,
                )

    @staticmethod
    def _generate_schema(main_schema, user_input_element):
        input_type_to_schema_type = {
            "int": "number",
            "float": "number",
            "boolean": "boolean",
            "options": "string",
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
            schema_type = input_type_to_schema_type[input_type]
            if schema_type == "boolean":
                properties["format"] = "checkbox"
            if schema_type == "number":
                if input_type == "float":
                    properties["multipleOf"] = 0.00000001
            if schema_type == "string":
                options = user_input_element.get("options", [])
                properties["format"] = "select"
                properties["default"] = def_val if def_val else options[0] if options else None,
                properties["enum"] = options
            properties["type"] = schema_type
        main_schema["properties"][title.replace(" ", "_")] = properties

    async def _add_candles(self, graphs_by_parts, candles_list, exchange_id):
        for candles_metadata in candles_list:
            try:
                chart = candles_metadata["chart"]
                candles = await self._get_candles_to_display(candles_metadata, exchange_id)
                try:
                    graphs_by_parts[chart][trading_enums.DBTables.CANDLES.value] = candles    # TODO multi candles sets
                except KeyError:
                    graphs_by_parts[chart] = {trading_enums.DBTables.CANDLES.value: candles}    # TODO multi candles sets
            except KeyError:
                # some table have no chart
                pass

    async def _get_candles_to_display(self, candles_metadata, exchange_id):
        if candles_metadata[trading_enums.DBRows.VALUE.value] == trading_constants.LOCAL_BOT_DATA:
            exchange_manager = trading_api.get_exchange_manager_from_exchange_id(exchange_id)
            array_candles = trading_api.get_symbol_historical_candles(
                trading_api.get_symbol_data(
                    exchange_manager,
                    candles_metadata[trading_enums.DBRows.PAIR.value]
                ),
                candles_metadata[trading_enums.DBRows.TIME_FRAME.value]
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
        time_frame = octobot_commons.enums.TimeFrames(candles_metadata[trading_enums.DBRows.TIME_FRAME.value])
        db_candles = await backtesting_api.get_all_ohlcvs(candles_metadata[trading_enums.DBRows.VALUE.value],
                                                          candles_metadata[trading_enums.DBRows.EXCHANGE.value],
                                                          candles_metadata[trading_enums.DBRows.PAIR.value],
                                                          time_frame)
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
        mode="lines",
        own_xaxis=False,
        own_yaxis=False,
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
            mode=mode,
            own_xaxis=own_xaxis,
            own_yaxis=own_yaxis,
            type=trading_enums.DisplayedElementTypes.CHART.value
        )
        self.elements.append(element)

    def user_inputs(
        self,
        name,
        config_values,
        schema,
        tentacle,
    ):
        element = Element(
            None,
            None,
            None,
            title=name,
            schema=schema,
            config_values=config_values,
            tentacle=tentacle,
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

    def to_json(self, name="root"):
        return {
            trading_enums.PlotAttributes.NAME.value: name,
            trading_enums.PlotAttributes.TYPE.value: self.type,
            trading_enums.PlotAttributes.DATA.value: {
                trading_enums.PlotAttributes.SUB_ELEMENTS.value: [
                    element.to_json(key) for key, element in self.nested_elements.items()
                ],
                trading_enums.PlotAttributes.ELEMENTS.value: [
                    element.to_json() for element in self.elements
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
        mode=None,
        own_xaxis=False,
        own_yaxis=False,
        value=None,
        config_values=None,
        schema=None,
        tentacle=None,
        columns=None,
        rows=None,
        searches=None,
        type=trading_enums.DisplayedElementTypes.CHART.value,
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
        self.mode = mode
        self.own_xaxis = own_xaxis
        self.own_yaxis = own_yaxis
        self.value = value
        self.config_values = config_values
        self.schema = schema
        self.tentacle = tentacle
        self.columns = columns
        self.rows = rows
        self.searches = searches
        self.type = type

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
            trading_enums.PlotAttributes.MODE.value: self.mode,
            trading_enums.PlotAttributes.OWN_XAXIS.value: self.own_xaxis,
            trading_enums.PlotAttributes.OWN_YAXIS.value: self.own_yaxis,
            trading_enums.PlotAttributes.VALUE.value: self.value,
            trading_enums.PlotAttributes.CONFIG.value: self.config_values,
            trading_enums.PlotAttributes.SCHEMA.value: self.schema,
            trading_enums.PlotAttributes.TENTACLE.value: self.tentacle,
            trading_enums.PlotAttributes.COLUMNS.value: self.columns,
            trading_enums.PlotAttributes.ROWS.value: self.rows,
            trading_enums.PlotAttributes.SEARCHES.value: self.searches,
            trading_enums.PlotAttributes.TYPE.value: self.type,
        }

    @staticmethod
    def to_list(array, multiplier=1):
        if array is None:
            return None
        return [e * multiplier for e in array]
