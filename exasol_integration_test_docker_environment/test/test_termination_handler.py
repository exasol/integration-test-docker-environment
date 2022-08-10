import sys
import unittest
from multiprocessing import Queue
from typing import List

import multiprocessing as mp
import re
from importlib import reload

from exasol_integration_test_docker_environment.lib.api.api_errors import TaskRuntimeError
import exasol_integration_test_docker_environment.cli.termination_handler


class StdoutQueue:
    def __init__(self, wrapped_queue: Queue):
        self.queue = wrapped_queue
        self.old_stdout = sys.stdout

    def write(self, msg):
        self.queue.put(msg)

    def flush(self):
        self.old_stdout.flush()


def run_positive(queue: Queue) -> None:
    stdout_queue = StdoutQueue(queue)
    sys.stdout = stdout_queue
    sys.stderr = stdout_queue
    m = reload(exasol_integration_test_docker_environment.cli.termination_handler)
    with m.TerminationHandler():
        pass


def run_with_task_error(queue: Queue) -> None:
    stdout_queue = StdoutQueue(queue)
    sys.stdout = stdout_queue
    sys.stderr = stdout_queue
    m = reload(exasol_integration_test_docker_environment.cli.termination_handler)
    with m.TerminationHandler():
        raise TaskRuntimeError(msg="test", inner=["task runtime error test"])


def run_with_unknown_error(queue: Queue) -> None:
    stdout_queue = StdoutQueue(queue)
    sys.stdout = stdout_queue
    sys.stderr = stdout_queue
    m = reload(exasol_integration_test_docker_environment.cli.termination_handler)
    with m.TerminationHandler():
        raise RuntimeError("unknown error")


def get_queue_content(q: Queue) -> List[str]:
    result = list()
    while not q.empty():
        result.append(q.get(block=False))
    return result


class TestTerminationHandler(unittest.TestCase):

    def test_success(self):
        q = Queue()
        p = mp.Process(target=run_positive, args=(q,))
        p.start()
        p.join()
        res = get_queue_content(q)
        print(f"Debug - result: {res}", file=sys.stderr)
        self.assertTrue(any(re.match(r"^The command took .+ s$", line) for line in res))
        self.assertEqual(p.exitcode, 0)

    def test_task_runtime_error(self):
        q = Queue()
        p = mp.Process(target=run_with_task_error, args=(q,))
        p.start()
        p.join()
        res = get_queue_content(q)
        print(f"Debug - result: {res}", file=sys.stderr)
        self.assertTrue(any(re.match(r"^The command failed after .+ s with:$", line) for line in res))
        self.assertTrue(any("task runtime error test" == line for line in res))
        self.assertFalse(any(line.startswith("Caught exception:") for line in res))
        self.assertEqual(p.exitcode, 1)

    def test_unknown_error(self):
        q = Queue()
        p = mp.Process(target=run_with_unknown_error, args=(q,))
        p.start()
        p.join()
        res = get_queue_content(q)
        print(f"Debug - result: {res}", file=sys.stderr)
        self.assertTrue(any(re.match(r"^The command failed after .+ s with:$", line) for line in res))
        self.assertTrue(any("Caught exception:unknown error" == line for line in res))
        self.assertTrue(any('raise RuntimeError("unknown error")' in line for line in res))
        self.assertEqual(p.exitcode, 1)


if __name__ == '__main__':
    unittest.main()
