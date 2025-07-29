import unittest

import pytest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.exaslct_test_environment import (
    ExaslctTestEnvironment,
)


def _assert_disk_size(env_name: str, size: str) -> None:
    with ContextDockerClient() as docker_client:
        containers = [
            c.name for c in docker_client.containers.list() if env_name in c.name
        ]
        db_container = [c for c in containers if "db_container" in c]
        exit_result = docker_client.containers.get(db_container[0]).exec_run(
            "cat /exa/etc/EXAConf"
        )
        output = exit_result[1].decode("UTF-8")
        return_code = exit_result[0]
        if output == "":
            exit_result = docker_client.containers.get(db_container[0]).exec_run(
                "cat /exa/etc/EXAConf"
            )
            output = exit_result[1].decode("UTF-8")
            return_code = exit_result[0]
        assert return_code == 0
        assert f" Size = {size}" in output


def test_default_db_disk_size(api_context):
    env_name = "test_default_db_disk_size"
    with api_context(
        name=env_name,
    ) as db:
        _assert_disk_size(db.environment_info.name, "2 GiB")


def test_smallest_valid_db_disk_size(api_context):
    additional_parameters = {"db_disk_size": "100 MiB"}
    env_name = "test_smallest_valid_db_disk_size"
    with api_context(
        name=env_name,
        additional_parameters=additional_parameters,
    ) as db:
        _assert_disk_size(db.environment_info.name, "100 MiB")


def test_invalid_db_mem_size(api_context):
    env_name = "test_invalid_db_disk_size"
    additional_parameters = {"db_disk_size": "90 MiB"}
    with pytest.raises(Exception):
        with api_context(
            name=env_name,
            additional_parameters=additional_parameters,
        ) as db:
            pass
