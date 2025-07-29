import os
import re
import unittest
from typing import (
    Callable,
    Optional,
)

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient

INTEGRATION_TEST_DOCKER_ENVIRONMENT_DEFAULT_BIN = "./start-test-env"


def close_environments(*args):
    for env in args:
        try:
            if env is not None:
                env.close()
        except Exception as e:
            print(e)


def check_db_version_from_env() -> Optional[str]:
    retval = None
    if "EXASOL_VERSION" in os.environ and os.environ["EXASOL_VERSION"] != "default":
        retval = os.environ["EXASOL_VERSION"]
    return retval


def multiassert(assert_list: list[Callable], unit_test: unittest.TestCase):
    failure_log: list[str] = []
    for assert_fn in assert_list:
        try:
            assert_fn()
        except AssertionError as e:
            failure_log.append(f"\nFailure {len(failure_log)}: {str(e)}")

    if len(failure_log) != 0:
        res_failure_log = "\n".join(failure_log)
        unit_test.fail(f"{len(failure_log)} failures within test.\n {res_failure_log}")


def find_docker_container_names(container_name_substr: str) -> list[str]:
    with ContextDockerClient() as docker_client:
        containers = [
            c.name
            for c in docker_client.containers.list()
            if container_name_substr in c.name
        ]
        return containers


def normalize_request_name(name: str):
    name = name.split("/")[-1]
    name = re.sub(r"[\[\]._]+", "_", name)
    return name.strip("_")
