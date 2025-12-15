import contextlib
from collections.abc import Callable
from collections.abc import Iterator
from typing import (
    ContextManager,
    Optional,
)

from typing import TypeAlias  # Needed for Python3.9

from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.exaslct_test_environment import (
    ExaslctTestEnvironment,
)
from exasol_integration_test_docker_environment.testing.spawned_test_environments import (
    SpawnedTestEnvironments,
)

CliContextProvider: TypeAlias = Callable[
    [Optional[str], Optional[list[str]]], ContextManager[SpawnedTestEnvironments]
]


@contextlib.contextmanager
def build_cli_isolation(
        env_name, executable: str = "itde"
) -> Iterator[ExaslctTestEnvironment]:
    """
    Builds an ExaslctTestEnvironment instance with a proper name based on the pytest request fixture.
    Cleans up the environment automatically on shutdown.
    """
    environment = ExaslctTestEnvironment(
        test_object=None,
        executable=executable,
        clean_images_at_close=True,
        name=env_name,
    )
    yield environment
    utils.close_environments(environment)


def build_cli_context_provider(
        test_environment: ExaslctTestEnvironment,
) -> CliContextProvider:
    """
    Returns a context provider function which can be used to spawn a Docker DB with custom name
    and custom additional db parameters.
    Cleans up the docker db automatically on shutdown when context provider closes.
    """

    @contextlib.contextmanager
    def create_context(
            name: str | None = None,
            additional_parameters: list[str] | None = None,
    ) -> Iterator[SpawnedTestEnvironments]:
        name = name if name else test_environment.name
        spawned = test_environment.spawn_docker_test_environments(
            name=name,
            additional_parameter=additional_parameters,
        )
        yield spawned
        utils.close_environments(spawned)

    return create_context
