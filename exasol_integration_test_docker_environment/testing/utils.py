import json
import os
import socket
import unittest
from contextlib import ExitStack
from typing import Optional, List, Callable

import requests

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient

INTEGRATION_TEST_DOCKER_ENVIRONMENT_DEFAULT_BIN = "./start-test-env"


def find_free_ports(num_ports: int) -> List[int]:

    ret_val = list()
    with ExitStack() as stack:
        sockets = [stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) for dummy in range(num_ports)]
        for s in sockets:
            s.bind(('', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            ret_val.append(s.getsockname()[1])
    with ExitStack() as stack:
        # Create an array of tuples of new socket + port to use
        sockets = [(stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM)), port) for port in ret_val]
        for socket_port in sockets:
            s = socket_port[0]
            port = socket_port[1]
            s.bind(('', port))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return ret_val


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
        res_failure_log = '\n'.join(failure_log)
        unit_test.fail(f"{len(failure_log)} failures within test.\n {res_failure_log}")
