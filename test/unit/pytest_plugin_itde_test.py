import pytest

from pytest_itde.config import Option

OPTIONS = (
    Option(
        name="port",
        prefix="exasol",
        type=int,
        default=9999,
        help_text="Port to connect to",
    ),
    Option(
        name="URL",
        prefix="exasol",
        type=str,
        default="http://foo.bar",
        help_text="A url",
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


@pytest.mark.parametrize("option,expected", zip(OPTIONS, ("exasol_port", "exasol_url")))
def test_get_pytest_option_name_for_option(option, expected):
    assert option.pytest_name == expected


def test_help_of_option_without_default_value():
    option = Option(
        name="port",
        prefix="exasol",
        type=int,
        default=9999,
        help_text="Port to connect to",
    )
    expected = "Port to connect to (default: 9999)."
    assert option.help == expected


def test_help_of_option_with_default_value():
    option = Option(
        name="port",
        prefix="exasol",
        type=int,
        help_text="Port to connect to",
    )
    expected = "Port to connect to."
    assert option.help == expected
