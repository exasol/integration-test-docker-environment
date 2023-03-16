from pytest_itde.config import Option

EXASOL_PREFIX = "exasol"
EXASOL_OPTIONS = (
    Option(
        name="host",
        prefix=EXASOL_PREFIX,
        type=str,
        default="localhost",
        help_text="Host to connect to",
    ),
    Option(
        name="port",
        prefix=EXASOL_PREFIX,
        type=int,
        default=9999,
        help_text="Port to connect to",
    ),
)


def pytest_addoption(parser):
    group = parser.getgroup(EXASOL_PREFIX)
    for option in EXASOL_OPTIONS:
        group.addoption(
            option.cli_name,
            type=option.type,
            help=option.help,
        )
