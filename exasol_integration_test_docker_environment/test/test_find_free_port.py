import unittest

from exasol_integration_test_docker_environment.testing.utils import find_free_ports


class FindFreePortTest(unittest.TestCase):

    def run_it(self, num_ports: int):
        ports = find_free_ports(num_ports)
        self.assertNotIn(0, ports)
        self.assertEqual(len(ports), num_ports)
        #Check that there are no duplicates!
        ports_set = set(ports)
        self.assertEqual(len(ports), len(ports_set))

    def test_find_ports(self):
        num_ports = [1, 2, 100, 1000]
        for num_port in num_ports:
            self.run_it(num_port)


if __name__ == '__main__':
    unittest.main()
