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
import octobot_trading.enums as trading_enums
import octobot_trading.modes.scripting_library.data as scripting_data


class PlottedElements:
    def __init__(self):
        self.nested_elements = {}
        self.elements = []

    async def fill_from_database(self, database_name):
        reader = scripting_data.DBReader(database_name)
        graphs_by_parts = {}
        for table_name in reader.tables():
            graph_data = reader.all(table_name)
            chart = graph_data[0]["chart"]
            if chart in graphs_by_parts:
                graphs_by_parts[chart][table_name] = graph_data
            else:
                graphs_by_parts[chart] = {table_name: graph_data}

        for part, datasets in graphs_by_parts.items():
            with self.part(part) as part:
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

    @contextlib.contextmanager
    def part(self, name):
        element = PlottedElements()
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
        mode="lines"
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
            mode=mode
        )
        self.elements.append(element)

    def to_json(self, name="root"):
        return {
            trading_enums.PlotAttributes.NAME.value: name,
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
        mode=None
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
        }

    @staticmethod
    def to_list(array, multiplier=1):
        if array is None:
            return None
        return [e * multiplier for e in array]
