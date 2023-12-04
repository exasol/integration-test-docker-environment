from inspect import cleandoc

from exasol_integration_test_docker_environment.doctor import health_checkup
from exasol_integration_test_docker_environment.lib.api.api_errors import HealthProblem
from exasol_integration_test_docker_environment.lib.api.common import cli_function


@cli_function
def health():
    """
    Check the health of the execution environment.

    If no issues have been found, using the library or executing the test should work just fine.
    For all found issues there will be a proposed fix/solution.

    If the environment was found to be healthy it will return None, otherwise a description of the found issues.
    :raises HealthProblem
    """

    errors = set(health_checkup())
    if not errors:
        return

    message = cleandoc(
        """
        {count} problem(s) have been identified.

        {problems}
        """
    ).format(
        count=len(errors),
        problems="\n".join(f"{error.value}" for error in errors),
    )
    raise HealthProblem(message)
