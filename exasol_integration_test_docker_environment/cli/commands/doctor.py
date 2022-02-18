import sys
from inspect import cleandoc

from exasol_integration_test_docker_environment.cli.cli import cli
from exasol_integration_test_docker_environment.doctor import (
    health_checkup,
    recommend_treatment,
)


@cli.command()
def doctor():
    """
    Check the health of the execution environment.

    If no issues have been found, using the library or executing the test should work just fine.
    For all found issues there will be a proposed fix/solution.

    If the environment was found to be healthy the exit code will be 0.
    """
    success, failure = 0, -1

    problems = set(health_checkup())
    if not problems:
        sys.exit(success)

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
        problems='\n'.join(
            (suggestion_template.format(problem=icd.value, suggestion=recommend_treatment(icd))
             for icd in problems)
        )
    )
    print(message)
    sys.exit(failure)
