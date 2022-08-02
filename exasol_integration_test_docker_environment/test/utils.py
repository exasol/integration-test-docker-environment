import unittest
from typing import List, Callable


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
