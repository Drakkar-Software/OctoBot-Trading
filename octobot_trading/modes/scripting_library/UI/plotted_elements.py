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


class PlottedElements:
    def __init__(self):
        self.nested_elements = {}
        self.elements = []

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
            trading_enums.PlotAttributes.X.value: self.to_list(self.x, 1000),
            trading_enums.PlotAttributes.Y.value: self.to_list(self.y),
            trading_enums.PlotAttributes.OPEN.value: self.to_list(self.open),
            trading_enums.PlotAttributes.HIGH.value: self.to_list(self.high),
            trading_enums.PlotAttributes.LOW.value: self.to_list(self.low),
            trading_enums.PlotAttributes.CLOSE.value: self.to_list(self.close),
            trading_enums.PlotAttributes.VOLUME.value: self.to_list(self.volume),
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
