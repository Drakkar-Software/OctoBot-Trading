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

test_method_hooks = {}


def setup_hook_on_method(module, method_name, hook_method):
    test_method_hooks[method_name] = getattr(module, method_name), hook_method
    restore_hook_on_method(module, method_name)


def restore_origin_method(module, method_name):
    setattr(module, method_name, test_method_hooks[method_name][0])


def restore_hook_on_method(module, method_name):
    setattr(module, method_name, test_method_hooks[method_name][1])
