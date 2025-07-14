import io
from collections.abc import Iterator

import pytest

from exasol_integration_test_docker_environment.lib.models.config.build_config import (
    set_build_config,
)
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    get_test_container_content,
)
from exasol_integration_test_docker_environment.testing.api_test_environment import (
    ApiTestEnvironment,
)
from exasol_integration_test_docker_environment.testing.api_test_environment_context_provider import (
    ApiContextProvider,
    build_api_context_provider,
    build_api_context_provider_with_test_container,
    build_api_isolation,
)
from exasol_integration_test_docker_environment.testing.cli_test_environment_context_provider import (
    CliContextProvider,
    build_cli_context_provider,
    build_cli_isolation,
)
from exasol_integration_test_docker_environment.testing.exaslct_docker_test_environment import (
    ExaslctDockerTestEnvironment,
)
from exasol_integration_test_docker_environment.testing.exaslct_test_environment import (
    ExaslctTestEnvironment,
)


@pytest.fixture
def cli_isolation(request) -> Iterator[ExaslctTestEnvironment]:
    with build_cli_isolation(request) as environment:
        yield environment


@pytest.fixture
def api_isolation(request) -> Iterator[ApiTestEnvironment]:
    with build_api_isolation(request) as environment:
        yield environment


@pytest.fixture(scope="module")
def api_isolation_module(request) -> Iterator[ApiTestEnvironment]:
    with build_api_isolation(request) as environment:
        yield environment


@pytest.fixture
def cli_context(
    cli_isolation,
) -> CliContextProvider:
    """
    Returns a method that test case implementations can use to create a
    context with a database.

    This fixture should be used on function level, in cases where one
    database is required per test.

    The test case optionally can pass a name and additional parameters for
    spawning the database:

    def test_case(cli_context):
        with cli_context(additional_parameters = ["--option"]):
            ...
    """
    return build_cli_context_provider(cli_isolation)


@pytest.fixture
def api_context(api_isolation: ApiTestEnvironment) -> ApiContextProvider:
    """
    Returns a method that test case implementations can use to create a
    context with a database.

    This fixture should be used on function level, in cases where one
    database is required per test.

    The test case optionally can pass a name and additional parameters for
    spawning the database:

    def test_case(api_context):
        with api_context(additional_parameters = ["--option"]):
            ...
    """
    return build_api_context_provider(api_isolation)


@pytest.fixture(scope="module")
def api_default_env(
    api_isolation_module: ApiTestEnvironment,
) -> Iterator[ExaslctDockerTestEnvironment]:
    """
    Provides a default database environment.
    """
    env_context = build_api_context_provider(api_isolation_module)
    with env_context(name=None, additional_parameters=None) as env:
        yield env


@pytest.fixture
def api_context_with_test_container(
    api_isolation: ApiTestEnvironment,
) -> ApiContextProvider:
    """
    Returns a method that test case implementations can use to create a
    context with a database + test container.

    This fixture should be used on function level, in cases where one
    database is required per test.

    The test case optionally can pass a name and additional parameters for
    spawning the database:

    def test_case(api_context_with_test_container):
        with api_context_with_test_container(additional_parameters = ["--option"],
                                              test_container_content = get_test_container_content(runtime_mapping-...)):
            ...
    """
    return build_api_context_provider_with_test_container(
        api_isolation,
        get_test_container_content(),
    )


@pytest.fixture(scope="module")
def api_default_env_with_test_container(
    api_isolation_module: ApiTestEnvironment,
) -> Iterator[ExaslctDockerTestEnvironment]:
    """
    Provides a default database + test container environment.
    """

    env_context = build_api_context_provider_with_test_container(
        test_environment=api_isolation_module,
        default_test_container_content=get_test_container_content(),
    )
    with env_context(name=None, additional_parameters=None) as env:
        yield env


@pytest.fixture
def fabric_stdin(monkeypatch):
    """
    Mock stdin to avoid ThreadException when reading from stdin while
    stdout is captured by pytest: OSError: pytest: reading from stdin while
    output is captured!  Consider using ``-s``.
    See https://github.com/fabric/fabric/issues/2005
    """
    monkeypatch.setattr("sys.stdin", io.StringIO(""))


@pytest.fixture
def luigi_output(tmp_path):
    set_build_config(
        False,
        tuple(),
        False,
        False,
        str(tmp_path),
        str(tmp_path.parent),
        "",
        "test",
    )
    return tmp_path


@pytest.fixture(scope="module")
def default_ubuntu_version():
    return "ubuntu:22.04"


def pytest_collection_modifyitems(items, config):
    markexpr = config.getoption("markexpr", "False")
    if not markexpr:
        config.option.markexpr = f"not gpu"
    elif "gpu" not in markexpr:
        config.option.markexpr = f"not gpu or ({markexpr})"
