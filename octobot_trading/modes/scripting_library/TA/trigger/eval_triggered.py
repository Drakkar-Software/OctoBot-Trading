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
import octobot_commons.enums as commons_enums
import octobot_commons.dict_util as dict_util
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
        value_key=commons_enums.CacheDatabaseColumns.VALUE.value,
        config_name=None,
        config: dict = None
):
    tentacle_class = tentacles_manager_api.get_tentacle_class_from_string(tentacle_class) \
        if isinstance(tentacle_class, str) else tentacle_class
    if trigger:
        # always trigger when asked to then return the triggered evaluation return
        return await _trigger_single_evaluation(context, tentacle_class, value_key, config_name, config)
    if tentacle_class.use_cache():
        # try reading from cache
        try:
            value, is_missing = await context.get_cached_value(value_key=value_key,
                                                               tentacle_name=tentacle_class.__name__,
                                                               config_name=config_name)
            if is_missing:
                # on ohlcv triggers, eval time stored in matrix is one timeframe after, try with removing it
                trigger_time = context.trigger_cache_timestamp - \
                    commons_enums.TimeFramesMinutes[commons_enums.TimeFrames(time_frame or context.time_frame)] \
                    * commons_constants.MINUTE_TO_SECONDS
                value, is_missing = await context.get_cached_value(value_key=value_key,
                                                                   cache_key=trigger_time,
                                                                   tentacle_name=tentacle_class.__name__,
                                                                   config_name=config_name)
                if not is_missing:
                    return value
            else:
                return value
        except commons_errors.UninitializedCache:
            if tentacle_class is not None and trigger is False:
                raise commons_errors.UninitializedCache(f"Can't read cache from {tentacle_class} before initializing "
                                                        f"it. Either activate this tentacle or set the 'trigger' "
                                                        f"parameter to True") from None

    _ensure_cache_when_set_value_key(value_key, tentacle_class)
    # read from evaluation matrix
    for value in _tentacle_values(context, tentacle_class, time_frame=time_frame, symbol=symbol):
        return value


async def evaluator_get_results(
        context,
        tentacle_class,
        time_frame=None,
        symbol=None,
        trigger=False,
        value_key=commons_enums.CacheDatabaseColumns.VALUE.value,
        limit=-1,
        config_name=None,
        config: dict = None
):
    tentacle_class = tentacles_manager_api.get_tentacle_class_from_string(tentacle_class) \
        if isinstance(tentacle_class, str) else tentacle_class
    if trigger:
        # always trigger when asked to
        eval_result = await _trigger_single_evaluation(context, tentacle_class, value_key, config_name, config)
        if limit == 1:
            # return already if only one value to return
            return eval_result
    if tentacle_class.use_cache():
        try:
            # can return multiple values
            return await context.get_cached_values(value_key=value_key, limit=limit,
                                                   tentacle_name=tentacle_class.__name__, config_name=config_name)
        except commons_errors.UninitializedCache:
            if tentacle_class is not None and trigger is False:
                raise commons_errors.UninitializedCache(f"Can't read cache from {tentacle_class} before initializing "
                                                        f"it. Either activate this tentacle or set the 'trigger' "
                                                        f"parameter to True") from None
    _ensure_cache_when_set_value_key(value_key, tentacle_class)
    if limit == 1:
        # read from evaluation matrix
        for value in _tentacle_values(context, tentacle_class, time_frame=time_frame, symbol=symbol):
            return value
        raise commons_errors.MissingDataError(f"No evaluator value for {tentacle_class.__name__}")
    else:
        raise commons_errors.ConfigEvaluatorError(f"Evaluator cache is required to get more than one historical value "
                                                  f"of an evaluator. Cache is disabled on {tentacle_class.__name__}")


def _ensure_cache_when_set_value_key(value_key, tentacle_class):
    if not tentacle_class.use_cache() and value_key != commons_enums.CacheDatabaseColumns.VALUE.value:
        raise commons_errors.ConfigEvaluatorError(f"Evaluator cache is required to read a value_key different from "
                                                  f"the evaluator output evaluation. "
                                                  f"Cache is disabled on {tentacle_class.__name__}")


async def _trigger_single_evaluation(context, tentacle_class, value_key, config_name, config):
    config = {key.replace(" ", "_"): val for key, val in config.items()} if config else {}
    cleaned_config_name = config_name.replace(" ", "_")
    context.top_level_tentacle.called_nested_evaluators.add(tentacle_class)
    tentacle_config = context.tentacle.specific_config if hasattr(context.tentacle, "specific_config") \
        else context.tentacle.trading_config
    tentacles_setup_config = context.tentacle.tentacles_setup_config \
        if hasattr(context.tentacle, "tentacles_setup_config") else context.exchange_manager.tentacles_setup_config
    with context.local_nested_tentacle_config(config_name, True):
        if config_name is None:
            tentacle_config = tentacles_manager_api.get_tentacle_config(
                tentacles_setup_config,
                tentacle_class)
            # apply forced config if any
            dict_util.check_and_merge_values_from_reference(tentacle_config, config, [], None)
        else:
            try:
                tentacle_config = tentacle_config[cleaned_config_name]
            except KeyError:
                await _init_nested_config(context, tentacle_class, cleaned_config_name,
                                          tentacles_setup_config, tentacle_config, config)
                try:
                    tentacle_config = tentacle_config[cleaned_config_name]
                except KeyError as e:
                    raise commons_errors.ConfigEvaluatorError(f"Missing evaluator configuration with name {e}")
            # apply forced config if any
            dict_util.check_and_merge_values_from_reference(tentacle_config, config, [], None)
            await inputs.save_user_input(
                context,
                config_name,
                commons_constants.NESTED_TENTACLE_CONFIG,
                tentacle_config,
                {},
                is_nested_config=context.nested_depth > 1,
                nested_tentacle=tentacle_class.get_name()
            )
        eval_result = (await tentacle_class.single_evaluation(
            tentacles_setup_config,
            tentacle_config,
            context=context
        ))[0]
        if value_key == commons_enums.CacheDatabaseColumns.VALUE.value:
            return eval_result
        else:
            value, is_missing = await context.get_cached_value(value_key=value_key,
                                                               tentacle_name=tentacle_class.__name__,
                                                               config_name=config_name)
            return None if is_missing else value


async def _init_nested_config(context, tentacle_class, cleaned_config_name,
                              tentacles_setup_config, tentacle_config, config):
    _, evaluator_instance = await tentacle_class.single_evaluation(
        tentacles_setup_config,
        config,
        context=context,
        ignore_cache=True
    )
    tentacle_config[cleaned_config_name] = evaluator_instance.specific_config


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
