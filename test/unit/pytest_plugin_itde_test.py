import pytest

from pytest_itde import TestSchemas
from pytest_itde.config import Option, OptionGroup
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports

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
    assert option.env == expected


@pytest.mark.parametrize(
    "option,expected", zip(OPTIONS, ("--exasol-port", "--exasol-url"))
)
def test_get_cli_argument_name_for_option(option, expected):
    assert option.cli == expected


@pytest.mark.parametrize("option,expected", zip(OPTIONS, ("exasol_port", "exasol_url")))
def test_get_pytest_option_name_for_option(option, expected):
    assert option.pytest == expected


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


@pytest.mark.parametrize(
    "definition,expected",
    (
        ("", []),
        ("TEST", ["TEST"]),
        ("TEST1,TEST2", ["TEST1", "TEST2"]),
        ("TEST1, TEST2", ["TEST1", "TEST2"]),
        ("TEST1, TEST2,", ["TEST1", "TEST2"]),
        ("TEST1, TEST2, TEST3", ["TEST1", "TEST2", "TEST3"]),
    ),
)
def test_test_schema_parser(definition, expected):
    actual = TestSchemas(definition)
    assert set(actual) == set(expected)


EXASOL_OPTIONS = (
    {
        "name": "host",
        "type": str,
        "default": "localhost",
        "help_text": "Host to connect to",
    },
    {
        "name": "port",
        "type": int,
        "default": Ports.default_ports.database,
        "help_text": "Port on which the exasol db is listening",
    },
    {
        "name": "username",
        "type": str,
        "default": "SYS",
        "help_text": "Username used to authenticate against the exasol db",
    },
    {
        "name": "password",
        "type": str,
        "default": "exasol",
        "help_text": "Password used to authenticate against the exasol db",
    },
)

BUCKETFS_OPTIONS = (
    {
        "name": "url",
        "type": str,
        "default": f"http://127.0.0.1:{Ports.default_ports.bucketfs}",
        "help_text": "Base url used to connect to the bucketfs service",
    },
    {
        "name": "username",
        "type": str,
        "default": "w",
        "help_text": "Username used to authenticate against the bucketfs service",
    },
    {
        "name": "password",
        "type": str,
        "default": "write",
        "help_text": "Password used to authenticate against the bucketfs service",
    },
)


@pytest.mark.parametrize(
    "group,expected",
    (
        (OptionGroup(prefix="exasol", options=EXASOL_OPTIONS), "exasol"),
        (OptionGroup(prefix="bucket", options=BUCKETFS_OPTIONS), "bucket"),
    ),
)
def test_option_group_prefix_property(group, expected):
    actual = group.prefix
    assert actual == expected


@pytest.mark.parametrize(
    "group,expected",
    (
        (
            OptionGroup(prefix="exasol", options=EXASOL_OPTIONS),
            (
                Option(
                    prefix="exasol",
                    name="host",
                    type=str,
                    default="localhost",
                    help_text="Host to connect to",
                ),
                Option(
                    prefix="exasol",
                    name="port",
                    type=int,
                    default=Ports.default_ports.database,
                    help_text="Port on which the exasol db is listening",
                ),
                Option(
                    prefix="exasol",
                    name="username",
                    type=str,
                    default="SYS",
                    help_text="Username used to authenticate against the exasol db",
                ),
                Option(
                    prefix="exasol",
                    name="password",
                    type=str,
                    default="exasol",
                    help_text="Password used to authenticate against the exasol db",
                ),
            ),
        ),
    ),
)
def test_option_group_options_property(group, expected):
    actual = group.options
    assert set(actual) == set(expected)


class PyTestArgs:
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)


@pytest.mark.parametrize(
    "group,env,cli,expected",
    (
        (
            OptionGroup(
                prefix="db",
                options=(
                    {
                        "name": "port",
                        "type": int,
                        "default": 9999,
                        "help_text": "some help",
                    },
                ),
            ),
            {},
            PyTestArgs(),
            {"port": 9999},
        ),
        (
            OptionGroup(
                prefix="db",
                options=(
                    {
                        "name": "port",
                        "type": int,
                        "default": 9999,
                        "help_text": "some help",
                    },
                ),
            ),
            {"DB_PORT": "7777"},
            PyTestArgs(),
            {"port": 7777},
        ),
        (
            OptionGroup(
                prefix="db",
                options=(
                    {
                        "name": "port",
                        "type": int,
                        "default": 9999,
                        "help_text": "some help",
                    },
                ),
            ),
            {"DB_PORT": "7777"},
            PyTestArgs(db_port=8888),
            {"port": 8888},
        ),
    ),
)
def test_option_group_prefix_kwargs_prioritization(group, env, cli, expected):
    actual = dict(group.kwargs(env, cli))
    assert actual == expected
