"""Test-only access to the ConfD JSON-RPC authentication secret."""

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.models.data.environment_info import (
    EnvironmentInfo,
)
from exasol_integration_test_docker_environment.lib.utils.api_function_decorators import (
    no_cli_function,
)

_AUTHENTICATION_TOKEN_COMMAND = [
    "awk",
    '$1 == "AuthenticationToken" { print $3 }',
    "/exa/etc/EXAConf",
]


@no_cli_function
def extract_confd_bearer_token(environment_info: EnvironmentInfo) -> str:
    """Return the disposable Docker-DB ConfD bearer token without logging it.

    This capability is intentionally limited to an ITDE-created Docker-DB
    container. The token is read directly from its private EXAConf volume and
    is neither stored in :class:`EnvironmentInfo` nor included in task output.
    Callers must treat the returned value as a secret and must not log it.
    """
    container_info = environment_info.database_info.container_info
    if container_info is None:
        raise ValueError(
            "ConfD bearer tokens are available only for Docker-DB environments"
        )

    with ContextDockerClient() as docker_client:
        result = docker_client.containers.get(container_info.container_name).exec_run(
            _AUTHENTICATION_TOKEN_COMMAND
        )

    token = result.output.decode("utf-8").strip()
    if result.exit_code != 0 or not token:
        # Never include command output here: it could contain the token.
        raise RuntimeError("Could not extract the ConfD bearer token")
    return token
