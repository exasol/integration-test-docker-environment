import json
import os
import unittest
from typing import (
    Callable,
    List,
    Optional,
)

import requests

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


def multiassert(assert_list: List[Callable], unit_test: unittest.TestCase):
    failure_log: List[str] = []
    for assert_fn in assert_list:
        try:
            assert_fn()
        except AssertionError as e:
            failure_log.append(f"\nFailure {len(failure_log)}: {str(e)}")

    if len(failure_log) != 0:
        res_failure_log = "\n".join(failure_log)
        unit_test.fail(f"{len(failure_log)} failures within test.\n {res_failure_log}")
