import sys

from exasol_integration_test_docker_environment.cli.cli import cli
from exasol_integration_test_docker_environment.lib import api


@cli.command()
def health():
    """
    Check the health of the execution environment.

    If no issues have been found, using the library or executing the test should work just fine.
    For all found issues there will be a proposed fix/solution.

    If the environment was found to be healthy the exit code will be 0, otherwise -1.
    """
    success, failure = 0, -1
    message = api.health()
    if message is None:
        sys.exit(success)
    print(message)
    sys.exit(failure)
