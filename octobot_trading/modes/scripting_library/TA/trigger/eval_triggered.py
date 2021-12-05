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
        evaluator_name,
        value,
        time_frames=None,
        symbols=None,
):
    symbols = [context.symbol] or symbols
    time_frames = [context.time_frame] or time_frames
    for symbol in symbols:
        for time_frame in time_frames:
            for evaluated_ta_node in matrix.get_tentacles_value_nodes(
                    context.matrix_id,
                    matrix.get_tentacle_nodes(context.matrix_id,
                                              exchange_name=context.exchange_name,
                                              tentacle_type=evaluators_enums.EvaluatorMatrixTypes.TA.value,
                                              tentacle_name=evaluator_name.get_name()),
                    symbol=symbol,
                    time_frame=time_frame):
                try:
                    if evaluated_ta_node.node_value >= value:
                        return True
                except:
                    raise RuntimeError("Evaluator doesnt support Evaluation Value. Try evaluator_get_result instead. "
                                       "Read the documentaion for more informations")
    return False


def is_evaluation_lower_than(
        context,
        evaluator_name,
        value,
        time_frames=None,
        symbols=None,
):
    symbols = [context.symbol] or symbols
    time_frames = [context.time_frame] or time_frames
    for symbol in symbols:
        for time_frame in time_frames:
            for evaluated_ta_node in matrix.get_tentacles_value_nodes(
                    context.matrix_id,
                    matrix.get_tentacle_nodes(context.matrix_id,
                                              exchange_name=context.exchange_name,
                                              tentacle_type=evaluators_enums.EvaluatorMatrixTypes.TA.value,
                                              tentacle_name=evaluator_name.get_name()),
                    symbol=symbol,
                    time_frame=time_frame):
                try:
                    if evaluated_ta_node.node_value <= value:
                        return True
                except:
                    raise RuntimeError("Evaluator doesnt support Evaluation Value. Try evaluator_get_result instead. "
                                       "Read the documentaion for more informations")
    return False


def evaluator_buy(
        context,
        evaluator_name,
        time_frames=None,
        symbols=None,
):
    symbols = [context.symbol] or symbols
    time_frames = [context.time_frame] or time_frames
    for symbol in symbols:
        for time_frame in time_frames:
            for evaluated_ta_node in matrix.get_tentacles_value_nodes(
                    context.matrix_id,
                    matrix.get_tentacle_nodes(context.matrix_id,
                                              exchange_name=context.exchange_name,
                                              tentacle_type=evaluators_enums.EvaluatorMatrixTypes.TA.value,
                                              tentacle_name=evaluator_name.get_name()),
                    symbol=symbol,
                    time_frame=time_frame):
                try:
                    if evaluated_ta_node.node_value == -1:
                        return True
                except:
                    raise RuntimeError("Evaluator doesnt support Evaluation Value. Try evaluator_get_result instead. "
                                       "Read the documentaion for more informations")
    return False


def evaluator_sell(
        context,
        evaluator_name=None,
        time_frames=None,
        symbols=None,
):
    symbols = [context.symbol] or symbols
    time_frames = [context.time_frame] or time_frames
    for symbol in symbols:
        for time_frame in time_frames:
            for evaluated_ta_node in matrix.get_tentacles_value_nodes(
                    context.matrix_id,
                    matrix.get_tentacle_nodes(context.matrix_id,
                                              exchange_name=context.exchange_name,
                                              tentacle_type=evaluators_enums.EvaluatorMatrixTypes.TA.value,
                                              tentacle_name=evaluator_name.get_name()),
                    symbol=symbol,
                    time_frame=time_frame):
                try:
                    if evaluated_ta_node.node_value == 1:
                        return True
                except:
                    raise RuntimeError("Evaluator doesnt support Evaluation Value. Try evaluator_get_result instead. "
                                       "Read the documentaion for more informations")
    return False


def evaluator_buy_or_sell(
        context,
        evaluator_name=None,
        time_frames=None,
        symbols=None,
):
    symbols = [context.symbol] or symbols
    time_frames = [context.time_frame] or time_frames
    for symbol in symbols:
        for time_frame in time_frames:
            for evaluated_ta_node in matrix.get_tentacles_value_nodes(
                    context.matrix_id,
                    matrix.get_tentacle_nodes(context.matrix_id,
                                              exchange_name=context.exchange_name,
                                              tentacle_type=evaluators_enums.EvaluatorMatrixTypes.TA.value,
                                              tentacle_name=evaluator_name.get_name()),
                    symbol=symbol,
                    time_frame=time_frame):
                try:
                    if evaluated_ta_node.node_value == 1 or evaluated_ta_node.node_value == -1:
                        return True
                except:
                    raise RuntimeError("Evaluator doesnt support Evaluation Value. Try evaluator_get_result instead. "
                                       "Read the documentaion for more informations")
    return False


def evaluator_get_result(
        context,
        evaluator_name,
        time_frame=None,
        symbol=None,
):
    symbol = context.symbol or symbol
    time_frame = context.time_frame or time_frame
    for evaluated_ta_node in matrix.get_tentacles_value_nodes(
            context.matrix_id,
            matrix.get_tentacle_nodes(context.matrix_id,
                                      exchange_name=context.exchange_name,
                                      tentacle_type=evaluators_enums.EvaluatorMatrixTypes.TA.value,
                                      tentacle_name=evaluator_name.get_name()),
            symbol=symbol,
            time_frame=time_frame):
        return evaluated_ta_node.node_value
    return
