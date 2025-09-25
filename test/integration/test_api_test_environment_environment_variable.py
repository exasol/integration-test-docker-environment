import pytest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


def assert_env_variable(env_variables: tuple[str], container_name: str):
    with ContextDockerClient() as docker_client:
        containers = [
            c.name for c in docker_client.containers.list() if container_name in c.name
        ]
        db_container = [c for c in containers if "db_container" in c]
        exit_result = docker_client.containers.get(db_container[0]).exec_run("env")
        output = exit_result[1].decode("UTF-8")
        return_code = exit_result[0]
        assert return_code == 0
        for env_variable in env_variables:
            assert env_variable in output


@pytest.mark.parametrize("env_variables", [("ABC=123",), ("ABC=123", "DEF=456")])
def test_env_variable(api_context, env_variables):
    additional_parameters = {"docker_environment_variable": env_variables}
    with api_context(additional_parameters=additional_parameters) as db:
        assert_env_variable(
            env_variables,
            db.environment_info.database_info.container_info.container_name,
        )
