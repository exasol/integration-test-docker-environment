import inspect
from typing import (
    Any,
    List,
    Optional,
    Tuple,
)

import click


def adjust_default_value_for_multiple(x: Any):
    """
    Click stores default values as list if 'Multiple'=true. However, for plain Python methods we
    need to use (immutable) tuples for declaring default value. Hence, we need to convert lists with tuples
    for comparison.
    Also, default values for none-required parameters of with multiple=true are marked as "None"
    in the command object, but in reality click invokes the command with "tuple()" for that parameter.
    (Note that we use here internal structures of click and don't have guarantee of the behavior)
    """
    def_value = x.default
    if x.multiple:
        if type(def_value) == list:
            return tuple(def_value)
        elif def_value is None:
            return tuple()
    return def_value


def is_click_command(obj: Any) -> bool:
    """
    Returns True if parameter obj is a click command, False otherwise.
    """
    return isinstance(obj, click.Command)


def defaults_of_click_call(
    click_call: click.Command,
) -> List[Tuple[Optional[str], Any]]:
    """
    Returns the default values of all None-required parameters of a click-command.
    """
    return [
        (o.name, adjust_default_value_for_multiple(o))
        for o in click_call.params
        if not o.required
    ]


def param_names_of_click_call(click_call: click.Command) -> List[Optional[str]]:
    """
    Returns names of all parameters of a click call
    """
    return [o.name for o in click_call.params]


def get_click_and_api_functions(
    click_module, api_module
) -> Tuple[List[Any], List[Any]]:
    # Get all click commands in module 'click_module'
    click_commands = [c[1] for c in inspect.getmembers(click_module, is_click_command)]
    # Get all functions in module 'api_module'
    api_functions = [
        f[1]
        for f in inspect.getmembers(api_module, inspect.isfunction)
        if f[1].__cli_function__  # type: ignore
    ]
    return click_commands, api_functions


def get_click_and_api_function_names(
    click_module, api_module
) -> Tuple[List[Any], List[Any]]:
    # Get all click command names in module 'click_module'
    click_command_names = [
        c[0] for c in inspect.getmembers(click_module, is_click_command)
    ]
    # Get all function names in module 'api_module'
    api_function_names = [
        f[0]
        for f in inspect.getmembers(api_module, inspect.isfunction)
        if f[1].__cli_function__  # type: ignore
    ]
    return click_command_names, api_function_names
