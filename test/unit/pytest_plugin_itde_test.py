import pytest

from pytest_itde.config import Option

OPTIONS = (
    Option(
        name="port", prefix="exasol", type=int, default=9999, help="Port to connect to"
    ),
    Option(
        name="URL", prefix="exasol", type=str, default="http://foo.bar", help="A url"
    ),
)


@pytest.mark.parametrize("option,expected", zip(OPTIONS, ("EXASOL_PORT", "EXASOL_URL")))
def test_get_environment_variable_name_for_option(option, expected):
    assert option.env_name == expected


@pytest.mark.parametrize(
    "option,expected", zip(OPTIONS, ("--exasol-port", "--exasol-url"))
)
def test_get_cli_argument_name_for_option(option, expected):
    assert option.cli_name == expected
