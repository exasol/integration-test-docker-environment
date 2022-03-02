import unittest
from itertools import permutations
from exasol_integration_test_docker_environment.cli import PortMapping


class PortMappingTest(unittest.TestCase):

    def setUp(self) -> None:
        self.equal_objects = (PortMapping(1, 1), PortMapping(1, 1), PortMapping(1, 1))
        self.unequal_objects = (PortMapping(1, 2), PortMapping(2, 1), PortMapping(3, 3))

    def test_eq_returns_true_for_equal_objects(self):
        for obj1, obj2 in permutations(self.equal_objects, 2):
            with self.subTest(obj1=obj1, obj2=obj2):
                self.assertTrue(obj1 == obj2)

    def test_eq_returns_false_for_unequal_objects(self):
        for obj1, obj2 in permutations(self.unequal_objects, 2):
            with self.subTest(obj1=obj1, obj2=obj2):
                self.assertFalse(obj1 == obj2)

    def test_ne_returns_false_for_equal_objects(self):
        for obj1, obj2 in permutations(self.equal_objects, 2):
            with self.subTest(obj1=obj1, obj2=obj2):
                self.assertFalse(obj1 != obj2)

    def test_ne_returns_true_for_unequal_objects(self):
        for obj1, obj2 in permutations(self.unequal_objects, 2):
            with self.subTest(obj1=obj1, obj2=obj2):
                self.assertTrue(obj1 != obj2)

    def test_dunder_repr(self):
        expected = PortMapping(1, 2)
        self.assertTrue(expected == eval(f"{expected!r}"))

    def test_dunder_str(self):
        expected = f'host-port: 5, container-port: 4'
        self.assertEqual(expected, f'{PortMapping(5, 4)}')

    def test_string_format_is_the_expected_one(self):
        expected = "<int>:<int>"
        self.assertEqual(expected, PortMapping.string_format())

    def test_returns_a_valid_port_mapping_for_valid_input_strings(self):
        test_data = (
            ("11:1111", PortMapping(11, 1111)),
            ("01:0111", PortMapping(1, 111)),
            (" 899:899", PortMapping(899, 899)),
            ("899: 899", PortMapping(899, 899)),
            ("899 : 899", PortMapping(899, 899)),
            (" 899 : 899 ", PortMapping(899, 899)),
        )
        for input_data, expected in test_data:
            with self.subTest(expected=expected, input=input_data):
                actual = PortMapping.from_string(input_data)
                self.assertTrue(expected == actual)

    def test_raises_value_error_for_malformed_input_strings(self):
        test_data = ("A1:1111", "11:1B11", "A1:1B11", "_01:0111", " a 899:899")
        for input_data in test_data:
            with self.subTest(input=input_data):
                with self.assertRaises(ValueError) as ex:
                    PortMapping.from_string(input_data)


if __name__ == '__main__':
    unittest.main()
