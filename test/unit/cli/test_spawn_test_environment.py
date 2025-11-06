import itertools
from test.unit.cli.cli_runner import CliRunner
from typing import (
    Any,
    Union,
)
from unittest.mock import (
    MagicMock,
    _Call,
    call,
)

import pytest
from _pytest.monkeypatch import MonkeyPatch

import exasol_integration_test_docker_environment.lib.api as api
from exasol_integration_test_docker_environment.cli.commands.spawn_test_environment import (
    spawn_test_environment as spawn_test_environment_command,
)
from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter import (
    DbOsAccess,
)
from exasol_integration_test_docker_environment.testing.api_consistency_utils import (
    defaults_of_click_call,
)


@pytest.fixture
def cli():
    return CliRunner(spawn_test_environment_command)


@pytest.fixture
def mock_api_spawn_test_environment(monkeypatch: MonkeyPatch) -> MagicMock:
    mock_function_to_mock = MagicMock()
    monkeypatch.setattr(api, "spawn_test_environment", mock_function_to_mock)
    return mock_function_to_mock


def _build_cli_args(cli_arguments: dict[str, str]) -> list[str]:
    gen = (k for pair in cli_arguments.items() for k in (f"--{pair[0]}", pair[1][0]))
    return [k for k in gen if k is not None]


def _gen_db_os_exec_values() -> list[tuple[str, str]]:
    return [(i.name, i.name) for i in DbOsAccess]


def _gen_log_level_values() -> list[tuple[str, str]]:
    return [(i, i) for i in ["DEBUG", "INFO", "WARNING", "ERROR", "FATAL"]]


def _gen_str_values(v: str) -> list[tuple[str, str]]:
    return [(v, v)]


def _gen_int_values(v: int) -> list[tuple[str, int]]:
    return [(str(v), v)]


def _gen_tuple_values(v: str) -> list[tuple[str, tuple[str]]]:
    return [(v, (v,))]


ARGUMENT_VALUE_TYPE = Union[
    list[tuple[str, str]],
    list[tuple[str, int]],
    list[tuple[str, tuple[str]]],
    list[tuple[None, bool]],
    list[tuple[str, bool]],
]

# Sample data as dictionary of all possible argument keys to a list of CLI/API tuple.
# The CLI value is always of type string, the API value is specific for each argument: One of str, bool, int or tuple.
# E.g. argument key "database-port-forward" can have [("1234", 1234), ("678", 1234)]
ARGUMENTS_VALUES: dict[str, ARGUMENT_VALUE_TYPE] = {
    "environment-name": _gen_str_values("test-environment"),
    "database-port-forward": _gen_int_values(1234),
    "bucketfs-port-forward": _gen_int_values(3456),
    "bucketfs-https-port-forward": _gen_int_values(3458),
    "ssh-port-forward": _gen_int_values(5678),
    "db-mem-size": _gen_str_values("64KB"),
    "db-disk-size": _gen_str_values("1MB"),
    "nameserver": _gen_tuple_values("1.1.1.1"),
    "docker-runtime": _gen_str_values("test-docker-runtime"),
    "docker-db-image-version": _gen_str_values("test-db-image-version"),
    "docker-db-image-name": _gen_str_values("test-db-image-name"),
    "db-os-access": _gen_db_os_exec_values(),
    "create-certificates": [(None, True)],
    "no-create-certificates": [(None, False)],
    "additional-db-parameter": _gen_tuple_values("test-db-additional-parameter"),
    "docker-environment-variable": _gen_tuple_values(
        "test-docker-environment-variable"
    ),
    "source-docker-repository-name": _gen_str_values(
        "test-docker-repository-name",
    ),
    "source-docker-tag-prefix": _gen_str_values("test-docker-tag-prefix"),
    "source-docker-username": _gen_str_values(
        "test-docker-username",
    ),
    "source-docker-password": _gen_str_values(
        "<PASSWORD>",
    ),
    "target-docker-repository-name": _gen_str_values("test-docker-repository-name"),
    "target-docker-tag-prefix": _gen_str_values("test-docker-tag-prefix"),
    "target-docker-username": _gen_str_values(
        "test-docker-username",
    ),
    "target-docker-password": _gen_str_values(
        "<TARGET-DOCKER-PASSWORD>",
    ),
    "output-directory": _gen_str_values("test-output-directory"),
    "temporary-base-directory": _gen_str_values("test-temporary-base-directory"),
    "workers": _gen_int_values(9),
    "task-dependencies-dot-file": _gen_str_values("test-task-dependency-file"),
    "log-level": _gen_log_level_values(),
    "use-job-specific-log-file": [("True", True), ("False", False)],
    "accelerator": _gen_tuple_values("nvidia=all"),
}

REQUIRED_ARGS = ("environment-name",)

SOURCE_DOCKER_ARGS = (
    "source-docker-repository-name",
    "source-docker-tag-prefix",
    "source-docker-username",
    "source-docker-password",
)

TARGET_DOCKER_ARGS = (
    "target-docker-repository-name",
    "target-docker-tag-prefix",
    "target-docker-username",
    "target-docker-password",
)

UTILITY_ARGS = (
    "output-directory",
    "temporary-base-directory",
    "workers",
    "task-dependencies-dot-file",
    "log-level",
    "use-job-specific-log-file",
)

DB_ARGS = (
    "database-port-forward",
    "bucketfs-port-forward",
    "bucketfs-https-port-forward",
    "ssh-port-forward",
    "db-mem-size",
    "db-disk-size",
    "nameserver",
    "db-os-access",
    "additional-db-parameter",
    "accelerator",
)

CREATE_CERTIFICATES_ARGS = ("create-certificates",)
NO_CREATE_CERTIFICATE_ARGS = ("no-create-certificates",)

DOCKER_ARGS = (
    "docker-runtime",
    "docker-db-image-version",
    "docker-db-image-name",
    "docker-environment-variable",
)

# Valid combination of keys used for the test.
# REQUIRED_ARGS need to be part in all test sets.
COMBINATIONS_OF_KEYS = [
    REQUIRED_ARGS
    + DB_ARGS
    + UTILITY_ARGS
    + SOURCE_DOCKER_ARGS
    + TARGET_DOCKER_ARGS
    + DOCKER_ARGS
    + CREATE_CERTIFICATES_ARGS,
    REQUIRED_ARGS
    + DB_ARGS
    + UTILITY_ARGS
    + SOURCE_DOCKER_ARGS
    + TARGET_DOCKER_ARGS
    + DOCKER_ARGS
    + NO_CREATE_CERTIFICATE_ARGS,
    REQUIRED_ARGS,
]


def _build_combinations() -> tuple[dict[str, Any], ...]:
    """ "
    Builds the cartesian product of all key : value combinations, by iterating over the COMBINATIONS_OF_KEYS.
    """
    ret_val = []
    for keys in COMBINATIONS_OF_KEYS:
        # No valid type definitions for combinations of argument values (see ARGUMENT_VALUE_TYPE) defined for
        # itertools.product. So we need to suppress type checker here.
        values_product = list(
            itertools.product(*(ARGUMENTS_VALUES[key] for key in keys))  # type: ignore
        )
        ret_val.extend(
            [
                {key: value for key, value in zip(keys, combination)}
                for combination in values_product
            ]
        )
    return tuple(ret_val)


CLICK_DEFAULT_VALUES = {
    key: default
    for key, default in defaults_of_click_call(spawn_test_environment_command)
}


def _build_expected_call(cli_arguments) -> _Call:
    def _get_optional_value(cli_arguments, key):
        if key in cli_arguments:
            return cli_arguments[key][1]
        else:
            return CLICK_DEFAULT_VALUES[key.replace("-", "_")]

    environment_name_value = cli_arguments["environment-name"][1]
    db_forward_value = _get_optional_value(cli_arguments, "database-port-forward")
    bucket_http_forward_value = _get_optional_value(
        cli_arguments, "bucketfs-port-forward"
    )
    bucket_https_forward_value = _get_optional_value(
        cli_arguments, "bucketfs-https-port-forward"
    )
    ssh_forward_value = _get_optional_value(cli_arguments, "ssh-port-forward")
    db_mem_size_value = _get_optional_value(cli_arguments, "db-mem-size")
    db_disk_size_value = _get_optional_value(cli_arguments, "db-disk-size")
    nameserver_value = _get_optional_value(cli_arguments, "nameserver")
    docker_runtime_value = _get_optional_value(cli_arguments, "docker-runtime")
    docker_db_image_version_value = _get_optional_value(
        cli_arguments, "docker-db-image-version"
    )
    docker_db_image_name_value = _get_optional_value(
        cli_arguments, "docker-db-image-name"
    )
    db_os_access_value = _get_optional_value(cli_arguments, "db-os-access")
    additional_db_parameter_value = _get_optional_value(
        cli_arguments, "additional-db-parameter"
    )
    docker_environment_variable_value = _get_optional_value(
        cli_arguments, "docker-environment-variable"
    )
    source_docker_repository_name_value = _get_optional_value(
        cli_arguments, "source-docker-repository-name"
    )
    source_docker_tag_prefix_value = _get_optional_value(
        cli_arguments, "source-docker-tag-prefix"
    )
    source_docker_username_value = _get_optional_value(
        cli_arguments, "source-docker-username"
    )
    source_docker_password = _get_optional_value(
        cli_arguments, "source-docker-password"
    )
    target_docker_repository_name_value = _get_optional_value(
        cli_arguments, "target-docker-repository-name"
    )
    target_docker_tag_prefix_value = _get_optional_value(
        cli_arguments, "target-docker-tag-prefix"
    )
    target_docker_username_value = _get_optional_value(
        cli_arguments, "target-docker-username"
    )
    target_docker_password_value = _get_optional_value(
        cli_arguments, "target-docker-password"
    )
    output_directory_value = _get_optional_value(cli_arguments, "output-directory")
    temporary_base_directory_value = _get_optional_value(
        cli_arguments, "temporary-base-directory"
    )
    workers_value = _get_optional_value(cli_arguments, "workers")
    task_dependencies_dot_file_value = _get_optional_value(
        cli_arguments, "task-dependencies-dot-file"
    )
    log_level_value = _get_optional_value(cli_arguments, "log-level")
    use_job_specific_log_file_value = _get_optional_value(
        cli_arguments, "use-job-specific-log-file"
    )

    accelerator = _get_optional_value(cli_arguments, "accelerator")

    if "create-certificates" in cli_arguments:
        create_certificates_value = cli_arguments["create-certificates"][1]
    elif "no-create-certificates" in cli_arguments:
        create_certificates_value = cli_arguments["no-create-certificates"][1]
    else:
        create_certificates_value = CLICK_DEFAULT_VALUES["create_certificates"]

    return call(
        environment_name_value,
        db_forward_value,
        bucket_http_forward_value,
        bucket_https_forward_value,
        ssh_forward_value,
        db_mem_size_value,
        db_disk_size_value,
        nameserver_value,
        docker_runtime_value,
        docker_db_image_version_value,
        docker_db_image_name_value,
        db_os_access_value,
        create_certificates_value,
        additional_db_parameter_value,
        docker_environment_variable_value,
        accelerator,
        source_docker_repository_name_value,
        source_docker_tag_prefix_value,
        source_docker_username_value,
        source_docker_password,
        target_docker_repository_name_value,
        target_docker_tag_prefix_value,
        target_docker_username_value,
        target_docker_password_value,
        output_directory_value,
        temporary_base_directory_value,
        workers_value,
        task_dependencies_dot_file_value,
        log_level=log_level_value,
        use_job_specific_log_file=use_job_specific_log_file_value,
    )


@pytest.mark.parametrize("cli_arguments", _build_combinations())
def test_spawn_test_environment(cli, mock_api_spawn_test_environment, cli_arguments):
    cli_args = _build_cli_args(cli_arguments)

    cli.run(*cli_args)
    assert cli.succeeded

    # Validate the exact call using mock_calls and IsInstance matcher
    expected_call = _build_expected_call(cli_arguments)
    assert mock_api_spawn_test_environment.mock_calls == [expected_call]


def test_no_environment(cli):
    assert cli.run().failed and "Missing option '--environment-name'" in cli.output
