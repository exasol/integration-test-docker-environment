import luigi
from luigi.parameter import ParameterVisibility

from exasol_integration_test_docker_environment.cli.options.docker_repository_options import (
    DEFAULT_DOCKER_REPOSITORY_NAME,
)


class source_docker_repository_config(luigi.Config):
    repository_name = luigi.Parameter(DEFAULT_DOCKER_REPOSITORY_NAME)
    tag_prefix = luigi.Parameter("")
    username = luigi.OptionalParameter(
        None, significant=False, visibility=ParameterVisibility.PRIVATE
    )
    password = luigi.OptionalParameter(
        None, significant=False, visibility=ParameterVisibility.PRIVATE
    )


class target_docker_repository_config(luigi.Config):
    repository_name = luigi.Parameter(DEFAULT_DOCKER_REPOSITORY_NAME)
    tag_prefix = luigi.Parameter("")
    username = luigi.OptionalParameter(
        None, significant=False, visibility=ParameterVisibility.PRIVATE
    )
    password = luigi.OptionalParameter(
        None, significant=False, visibility=ParameterVisibility.PRIVATE
    )


class docker_build_arguments(luigi.Config):
    transparent = luigi.DictParameter(dict())
    image_changing = luigi.DictParameter(dict())
    secret = luigi.DictParameter(
        dict(),
        description="Will not be saved somewhere, but are also assumed to be transparent",
        visibility=ParameterVisibility.PRIVATE,
    )
