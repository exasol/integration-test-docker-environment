import unittest

from exasol_integration_test_docker_environment.lib.test_environment.db_version import (
    db_version_supports_custom_certificates,
)


class TestDbVersionSupportCustomCertificates(unittest.TestCase):

    def test_default(self):
        self.assertTrue(db_version_supports_custom_certificates("default"))

    def test_none(self):
        self.assertTrue(db_version_supports_custom_certificates(None))

    def test_7_0_5(self):
        self.assertFalse(db_version_supports_custom_certificates("7.0.5"))

    def test_7_0_14(self):
        self.assertTrue(db_version_supports_custom_certificates("7.0.14"))

    def test_6_0_0(self):
        self.assertFalse(db_version_supports_custom_certificates("6.0.0"))

    def test_6_0_0_d_1(self):
        self.assertFalse(db_version_supports_custom_certificates("6.0.0-d1"))

    def test_7_1_3(self):
        self.assertTrue(db_version_supports_custom_certificates("7.1.3"))

    def test_7_1_3_d_1(self):
        self.assertTrue(db_version_supports_custom_certificates("7.1.3-d1"))

    def test_throw_error(self):
        self.assertRaises(ValueError, db_version_supports_custom_certificates, "7abc")


if __name__ == "__main__":
    unittest.main()
