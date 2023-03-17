from pytest_itde import config

EXASOL = config.OptionGroup(
    prefix="exasol",
    options=(
        {
            "name": "host",
            "type": str,
            "default": "localhost",
            "help_text": "Host to connect to",
        },
        {
            "name": "port",
            "type": int,
            "default": 8888,
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
    ),
)

BUCKETFS = config.OptionGroup(
    prefix="bucketfs",
    options=(
        {
            "name": "url",
            "type": str,
            "default": "http://127.0.0.1:6666",
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
    ),
)


def _test_schemas(value):
    seperator = ","
    if seperator in value:
        schemas = value.split(seperator)
    else:
        schemas = [value]
    schemas = (s.strip() for s in schemas)
    schemas = (s for s in schemas if s != "")
    return list(schemas)


ITDE = config.OptionGroup(
    prefix="itde",
    options=(
        {
            "name": "db-version",
            "type": str,
            "default": "7.1.17",
            "help_text": "DB version to start, if value is 'external' an existing instance will be used",
        },
        {
            "name": "schemas",
            "type": _test_schemas,
            "default": "TEST,TEST_SCHEMA",
            "help_text": "Schemas which should for the session",
        },
    ),
)

OPTION_GROUPS = (EXASOL, BUCKETFS, ITDE)


def _add_option_group(parser, group):
    parser_group = parser.getgroup(group.prefix)
    for option in group.options:
        parser_group.addoption(
            option.cli,
            type=option.type,
            help=option.help,
        )


def pytest_addoption(parser):
    for group in OPTION_GROUPS:
        _add_option_group(parser, group)
