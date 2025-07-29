import pytest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


def _assert_mem_size(container_name: str, size: str):
    with ContextDockerClient() as docker_client:
        containers = [
            c.name for c in docker_client.containers.list() if container_name in c.name
        ]
        db_container = [c for c in containers if "db_container" in c]
        exit_result = docker_client.containers.get(db_container[0]).exec_run(
            "cat /exa/etc/EXAConf"
        )
        output = exit_result[1].decode("UTF-8")
        if output == "":
            exit_result = docker_client.containers.get(db_container[0]).exec_run(
                "cat /exa/etc/EXAConf"
            )
            output = exit_result[1].decode("UTF-8")
            return_code = exit_result[0]
        return_code = exit_result[0]
        assert return_code == 0
        assert f"MemSize = {size}" in output


def test_default_db_mem_size(api_context):
    with api_context() as db:
        _assert_mem_size(
            db.environment_info.database_info.container_info.container_name, "2 GiB"
        )


def test_smallest_valid_db_mem_size(api_context):
    additional_parameters = {"db_mem_size": "1 GiB"}
    with api_context(
        additional_parameters=additional_parameters,
    ) as db:
        _assert_mem_size(
            db.environment_info.database_info.container_info.container_name, "1 GiB"
        )


def test_invalid_db_mem_size(api_context):
    additional_parameters = {"db_mem_size": "999 MiB"}
    with pytest.raises(Exception) as context:
        with api_context(
            additional_parameters=additional_parameters,
        ) as db:
            pass
