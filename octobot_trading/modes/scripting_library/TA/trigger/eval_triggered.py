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
        evaluator_class=None,
        value=None,
        time_frames=None,
        pairs=None,
):
    for pair in pairs or [context.traded_pair]:
        for time_frame in time_frames:
            for evaluated_ta_node in matrix.get_tentacles_value_nodes(
                        context.matrix_id,
                        matrix.get_tentacle_nodes(context.matrix_id,
                                                  exchange_name=context.exchange_name,
                                                  tentacle_type=evaluators_enums.EvaluatorMatrixTypes.TA.value,
                                                  tentacle_name=evaluator_class.get_name()),
                        symbol=pair,
                        time_frame=time_frame):
                if evaluated_ta_node.node_value <= value:
                    return False
    return True


def is_evaluation_lower_than(
        context,
        evaluator_class=None,
        value=None,
        time_frames=None,
        pairs=None,
        currencies=None,
):
    for pair in pairs:
        for time_frame in time_frames:
            for evaluated_ta_node in matrix.get_tentacles_value_nodes(
                        context.matrix_id,
                        matrix.get_tentacle_nodes(context.matrix_id,
                                                  exchange_name=context.exchange_name,
                                                  tentacle_type=evaluators_enums.EvaluatorMatrixTypes.TA.value,
                                                  tentacle_name=evaluator_class.get_name()),
                        symbol=pair,
                        time_frame=time_frame):
                if evaluated_ta_node.node_value >= value:
                    return False
    return True


def evaluator_buy(
        evaluator_class=None,
        time_frames=None,
        pairs=None,
        currencies=None,
        exchange_name=None,
        matrix_id=None
):
    for pair in pairs:
        for time_frame in time_frames:
            for evaluated_ta_node in matrix.get_tentacles_value_nodes(
                        matrix_id,
                        matrix.get_tentacle_nodes(matrix_id,
                                                  exchange_name=exchange_name,
                                                  tentacle_type=evaluators_enums.EvaluatorMatrixTypes.TA.value,
                                                  tentacle_name=evaluator_class.get_name()),
                        symbol=pair,
                        time_frame=time_frame):
                if evaluated_ta_node.node_value != -1:
                    return False
    return True


def evaluator_sell(
        evaluator_class=None,
        time_frames=None,
        pairs=None,
        currencies=None,
        exchange_name=None,
        matrix_id=None
):
    for pair in pairs:
        for time_frame in time_frames:
            for evaluated_ta_node in matrix.get_tentacles_value_nodes(
                        matrix_id,
                        matrix.get_tentacle_nodes(matrix_id,
                                                  exchange_name=exchange_name,
                                                  tentacle_type=evaluators_enums.EvaluatorMatrixTypes.TA.value,
                                                  tentacle_name=evaluator_class.get_name()),
                        symbol=pair,
                        time_frame=time_frame):
                if evaluated_ta_node.node_value != 1:
                    return False
    return True


def evaluator_buy_or_sell(
        evaluator_class=None,
        time_frames=None,
        pairs=None,
        currencies=None,
        exchange_name=None,
        matrix_id=None
):
    for pair in pairs:
        for time_frame in time_frames:
            for evaluated_ta_node in matrix.get_tentacles_value_nodes(
                        matrix_id,
                        matrix.get_tentacle_nodes(matrix_id,
                                                  exchange_name=exchange_name,
                                                  tentacle_type=evaluators_enums.EvaluatorMatrixTypes.TA.value,
                                                  tentacle_name=evaluator_class.get_name()),
                        symbol=pair,
                        time_frame=time_frame):
                if evaluated_ta_node.node_value == 1 or evaluated_ta_node.node_value == -1:
                    return True
    return False
