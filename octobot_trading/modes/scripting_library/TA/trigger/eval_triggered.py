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

import octobot_evaluators.matrix as matrix
import octobot_evaluators.enums as evaluators_enums


def is_evaluation_higher_than(
        context,
        evaluator_class,
        value,
        time_frames=None,
        symbols=None,
):
    for tentacle_value in _tentacle_values(context, evaluator_class, time_frames=time_frames, symbols=symbols):
        try:
            if tentacle_value >= value:
                return True
        except Exception:
            raise RuntimeError("Evaluator doesnt support Evaluation Value. Try evaluator_get_result instead. "
                               "Read the documentaion for more informations")
    return False


def is_evaluation_lower_than(
        context,
        evaluator_class,
        value,
        time_frames=None,
        symbols=None,
):
    for tentacle_value in _tentacle_values(context, evaluator_class, time_frames=time_frames, symbols=symbols):
        try:
            if tentacle_value <= value:
                return True
        except Exception:
            raise RuntimeError("Evaluator doesnt support Evaluation Value. Try evaluator_get_result instead. "
                               "Read the documentaion for more informations")
    return False


def evaluator_buy(
        context,
        evaluator_class,
        time_frames=None,
        symbols=None,
):
    for value in _tentacle_values(context, evaluator_class, time_frames=time_frames, symbols=symbols):
        try:
            if value == -1:
                return True
        except Exception:
            raise RuntimeError("Evaluator doesnt support Evaluation Value. Try evaluator_get_result instead. "
                               "Read the documentaion for more informations")
    return False


def evaluator_sell(
        context,
        evaluator_class=None,
        time_frames=None,
        symbols=None,
):
    for value in _tentacle_values(context, evaluator_class, time_frames=time_frames, symbols=symbols):
        try:
            if value == 1:
                return True
        except Exception:
            raise RuntimeError("Evaluator doesnt support Evaluation Value. Try evaluator_get_result instead. "
                               "Read the documentaion for more informations")
    return False


def evaluator_buy_or_sell(
        context,
        evaluator_class=None,
        time_frames=None,
        symbols=None,
):
    for value in _tentacle_values(context, evaluator_class, time_frames=time_frames, symbols=symbols):
        try:
            if value == 1 or value == -1:
                return True
        except Exception:
            raise RuntimeError("Evaluator doesnt support Evaluation Value. Try evaluator_get_result instead. "
                               "Read the documentaion for more informations")
    return False


def evaluator_get_result(
        context,
        tentacle_class,
        time_frame=None,
        symbol=None,
):
    for value in _tentacle_values(context, tentacle_class, time_frame=time_frame, symbol=symbol):
        return value


def _tentacle_values(context,
                     tentacle_class,
                     time_frames=None,
                     symbols=None,
                     time_frame=None,
                     symbol=None):
    tentacle_name = tentacle_class if isinstance(tentacle_class, str) else tentacle_class.get_name()
    symbols = [context.symbol or symbol] or symbols
    time_frames = [context.time_frame or time_frame] or time_frames
    for symbol in symbols:
        for time_frame in time_frames:
            for tentacle_type in evaluators_enums.EvaluatorMatrixTypes:
                for evaluated_ta_node in matrix.get_tentacles_value_nodes(
                        context.matrix_id,
                        matrix.get_tentacle_nodes(context.matrix_id,
                                                  exchange_name=context.exchange_name,
                                                  tentacle_type=tentacle_type.value,
                                                  tentacle_name=tentacle_name),
                        symbol=symbol,
                        time_frame=time_frame):
                    yield evaluated_ta_node.node_value
