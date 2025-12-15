import multiprocessing as mp
import re
import sys
import unittest
from importlib import reload
from multiprocessing import Queue

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
    # we need to release the termination module here, otherwise the new sys.stdout/sys.stderr might not be set correctly
    m = reload(exasol_integration_test_docker_environment.cli.termination_handler)
    with m.TerminationHandler():
        pass


def run_with_unknown_error(queue: Queue) -> None:
    stdout_queue = StdoutQueue(queue)
    sys.stdout = stdout_queue
    sys.stderr = stdout_queue
    # we need to release the termination module here, otherwise the new sys.stdout/sys.stderr might not be set correctly
    m = reload(exasol_integration_test_docker_environment.cli.termination_handler)
    with m.TerminationHandler():
        raise RuntimeError("unknown error")


def get_queue_content(q: Queue) -> list[str]:
    result = []
    while not q.empty():
        result.append(q.get(block=False))
    return result


class TestTerminationHandler(unittest.TestCase):
    """
    Deprecated. Replaced by ./test/unit/test_termination_handler.py
    """

    def test_success(self):
        q = Queue()
        p = mp.Process(target=run_positive, args=(q,))
        p.start()
        p.join()
        res = get_queue_content(q)
        self.assertTrue(
            any(re.match(r"^The command took .+ s$", line) for line in res),
            f"Result {res} doesn't contain 'The command took'",
        )
        self.assertEqual(p.exitcode, 0)

    def test_unknown_error(self):
        q = Queue()
        p = mp.Process(target=run_with_unknown_error, args=(q,))
        p.start()
        p.join()
        res = get_queue_content(q)
        self.assertTrue(
            any(
                re.match(r"^The command failed after .+ s with:$", line) for line in res
            )
        )
        self.assertTrue(any("Caught exception:unknown error" == line for line in res))
        self.assertTrue(
            any('raise RuntimeError("unknown error")' in line for line in res)
        )
        self.assertEqual(p.exitcode, 1)


if __name__ == "__main__":
    unittest.main()
