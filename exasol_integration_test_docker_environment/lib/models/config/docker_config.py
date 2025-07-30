import getpass
import os
from typing import (
    Optional,
)

import luigi
from luigi.parameter import ParameterVisibility

from exasol_integration_test_docker_environment.cli.options.docker_repository_options import (
    DEFAULT_DOCKER_REPOSITORY_NAME,
)


class source_docker_repository_config(luigi.Config):
    repository_name: str = luigi.Parameter(default=DEFAULT_DOCKER_REPOSITORY_NAME)
    tag_prefix: str = luigi.Parameter(default="")
    username: Optional[str] = luigi.OptionalParameter(
        default=None, significant=False, visibility=ParameterVisibility.PRIVATE
    )
    password: Optional[str] = luigi.OptionalParameter(
        default=None, significant=False, visibility=ParameterVisibility.PRIVATE
    )


class target_docker_repository_config(luigi.Config):
    repository_name: str = luigi.Parameter(default=DEFAULT_DOCKER_REPOSITORY_NAME)
    tag_prefix: str = luigi.Parameter(default="")
    username: Optional[str] = luigi.OptionalParameter(
        default=None, significant=False, visibility=ParameterVisibility.PRIVATE
    )
    password: Optional[str] = luigi.OptionalParameter(
        default=None, significant=False, visibility=ParameterVisibility.PRIVATE
    )


class docker_build_arguments(luigi.Config):
    transparent: dict[str, str] = luigi.DictParameter(default={})
    image_changing: dict[str, str] = luigi.DictParameter(default={})
    secret: dict[str, str] = luigi.DictParameter(
        default={},
        description="Will not be saved somewhere, but are also assumed to be transparent",
        visibility=ParameterVisibility.PRIVATE,
    )


def set_docker_repository_config(
    docker_password: Optional[str],
    docker_repository_name: Optional[str],
    docker_username: Optional[str],
    tag_prefix: str,
    kind: str,
):
    config_class = f"{kind}_docker_repository_config"
    luigi.configuration.get_config().set(config_class, "tag_prefix", tag_prefix)
    if docker_repository_name is not None:
        luigi.configuration.get_config().set(
            config_class, "repository_name", docker_repository_name
        )
    password_environment_variable_name = f"{kind.upper()}_DOCKER_PASSWORD"
    if docker_username is not None:
        luigi.configuration.get_config().set(config_class, "username", docker_username)
        if docker_password is not None:
            luigi.configuration.get_config().set(
                config_class, "password", docker_password
            )
        elif password_environment_variable_name in os.environ:
            print(
                f"Using password from environment variable {password_environment_variable_name}"
            )
            password = os.environ[password_environment_variable_name]
            luigi.configuration.get_config().set(config_class, "password", password)
        else:
            password = getpass.getpass(
                f"{kind.capitalize()} Docker Registry Password for User %s:"
                % docker_username
            )
            luigi.configuration.get_config().set(config_class, "password", password)
