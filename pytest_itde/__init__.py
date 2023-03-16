from pytest_itde import config

EXASOL_PREFIX = "exasol"
EXASOL_OPTIONS = (
    config.Option(
        name="host",
        prefix=EXASOL_PREFIX,
        type=str,
        default="localhost",
        help_text="Host to connect to",
    ),
    config.Option(
        name="port",
        prefix=EXASOL_PREFIX,
        type=int,
        default=8888,
        help_text="Port on which the exasol db is listening",
    ),
    config.Option(
        name="username",
        prefix=EXASOL_PREFIX,
        type=str,
        default="SYS",
        help_text="Username used to authenticate against the exasol db",
    ),
    config.Option(
        name="password",
        prefix=EXASOL_PREFIX,
        type=str,
        default="exasol",
        help_text="Password used to authenticate against the exasol db",
    ),
)


def pytest_addoption(parser):
    group = parser.getgroup(EXASOL_PREFIX)
    for option in EXASOL_OPTIONS:
        group.addoption(
            option.cli,
            type=option.type,
            help=option.help,
        )
