import inspect
import unittest

from exasol_integration_test_docker_environment.cli import commands
from exasol_integration_test_docker_environment.lib import api

from exasol_integration_test_docker_environment.testing.api_consistency_utils import \
    param_names_of_click_call, get_click_and_api_functions, defaults_of_click_call, get_click_and_api_function_names
from exasol_integration_test_docker_environment.testing.utils import multiassert


class ClickApiConsistencyTest(unittest.TestCase):

    def test_api_arguments(self):
        """
        Validate that the argument lists for all commands match!
        """
        self.maxDiff = None

        click_commands, api_functions = get_click_and_api_functions(commands, api)
        # Now iterate over the list and compare consistency
        for cli_call, api_call in zip(click_commands, api_functions):
            cli_spec = inspect.getfullargspec(cli_call.callback)
            api_spec = inspect.getfullargspec(api_call)

            # We don't compare the annotation for the return type as this is allowed to be different between CLI and API
            if "return" in api_spec.annotations:
                del api_spec.annotations["return"]

            multiassert([lambda: self.assertEqual(api_spec.args, cli_spec.args),
                         lambda: self.assertEqual(api_spec.annotations, cli_spec.annotations),
                         lambda: self.assertEqual(api_spec.args, param_names_of_click_call(cli_call))], self)

    def test_api_default_values(self):
        """
        Validate that the default values for all commands match!
        """

        click_commands, api_functions = get_click_and_api_functions(commands, api)

        # Now iterate over the list and compare consistency
        for cli_call, api_call in zip(click_commands, api_functions):
            api_spec_defaults = inspect.getfullargspec(api_call).defaults or tuple()
            cli_defaults = defaults_of_click_call(cli_call)

            self.assertEqual(len(cli_defaults), len(api_spec_defaults))
            for api_default_value, cli_default in zip(api_spec_defaults, cli_defaults):
                cli_param_name, cli_default_value = cli_default
                if api_default_value != cli_default_value:
                    self.fail(f"Default value for parameter '{cli_param_name}' "
                              f"for method '{api_call.__name__}' does not match. "
                              f"API method has default value '{api_default_value}' "
                              f"while CLI method has default value '{cli_default_value}'")

    def test_same_functions(self):
        """
        Validate that Click commands and API functions match!
        For that we use inspect to get all classes of type click.Command in module 'commands',
        and on the other hand get all functions in module 'api'. The list of names from both most be identical.
        """
        click_command_names, api_function_names = get_click_and_api_function_names(commands, api)
        self.assertEqual(click_command_names, api_function_names)


if __name__ == '__main__':
    unittest.main()
