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

import octobot_commons.constants as commons_constants
import octobot_commons.errors as commons_errors
import octobot_evaluators.matrix as matrix
import octobot_evaluators.enums as evaluators_enums
import octobot_tentacles_manager.api as tentacles_manager_api
import octobot_trading.modes.scripting_library.UI.inputs as inputs


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


async def evaluator_get_result(
        context,
        tentacle_class,
        time_frame=None,
        symbol=None,
        trigger=False,
        config_name=None
):
    if trigger:
        return await _trigger_single_evaluation(context, tentacle_class, config_name)
    for value in _tentacle_values(context, tentacle_class, time_frame=time_frame, symbol=symbol):
        return value


async def _trigger_single_evaluation(context, tentacle_class, config_name):
    with context.local_nested_config_name(config_name):
        if config_name is None:
            tentacle_config = tentacles_manager_api.get_tentacle_config(
                context.tentacle.tentacles_setup_config,
                tentacle_class)
        else:
            try:
                tentacle_config = context.tentacle.specific_config[commons_constants.NESTED_TENTACLES_CONFIG]\
                    .get(config_name, {})
            except KeyError:
                await _init_nested_config(context, tentacle_class, config_name)
                try:
                    tentacle_config = context.tentacle.specific_config[commons_constants.NESTED_TENTACLES_CONFIG]\
                        .get(config_name, {})
                except KeyError as e:
                    raise commons_errors.ConfigEvaluatorError(f"Missing evaluator configuration with name {e}")
            await inputs.save_user_input(
                context,
                config_name,
                commons_constants.NESTED_TENTACLES_CONFIG,
                tentacle_config,
                {}
            )
        return (await tentacle_class.single_evaluation(
            context.tentacle.tentacles_setup_config,
            tentacle_config,
            context=context
        ))[0]


async def _init_nested_config(context, tentacle_class, config_name):
    _, evaluator_instance = await tentacle_class.single_evaluation(
        context.tentacle.tentacles_setup_config,
        {},
        context=context
    )
    try:
        context.tentacle.specific_config[commons_constants.NESTED_TENTACLES_CONFIG][config_name] = evaluator_instance.specific_config
    except KeyError:
        context.tentacle.specific_config[commons_constants.NESTED_TENTACLES_CONFIG] = {}
        context.tentacle.specific_config[commons_constants.NESTED_TENTACLES_CONFIG][config_name] = evaluator_instance.specific_config


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
