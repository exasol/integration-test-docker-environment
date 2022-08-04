from inspect import cleandoc
from typing import Optional

from exasol_integration_test_docker_environment.doctor import health_checkup, recommend_mitigation
from exasol_integration_test_docker_environment.lib.api.api_errors import HealthProblem


def health():
    """
    Check the health of the execution environment.

    If no issues have been found, using the library or executing the test should work just fine.
    For all found issues there will be a proposed fix/solution.

    If the environment was found to be healthy it will return None, otherwise a description of the found issues.
    :raises HealthProblem
    """

    problems = set(health_checkup())
    if not problems:
        return

    suggestion_template = cleandoc(
        """
        * {problem}
          Fix: {suggestion}
        """
    )
    message = cleandoc(
        """
        {count} problem(s) have been identified.

        {problems}
        """
    ).format(
        count=len(problems),
        problems="\n".join(
            (
                suggestion_template.format(
                    problem=icd.value, suggestion=recommend_mitigation(icd)
                )
                for icd in problems
            )
        ),
    )
    raise HealthProblem(message)
