import luigi
from luigi.parameter import ParameterVisibility


class source_docker_repository_config(luigi.Config):
    repository_name = luigi.Parameter("exasol/script-language-container")
    tag_prefix = luigi.Parameter("")
    username = luigi.OptionalParameter(None, significant=False, visibility=ParameterVisibility.PRIVATE)
    password = luigi.OptionalParameter(None, significant=False, visibility=ParameterVisibility.PRIVATE)


class target_docker_repository_config(luigi.Config):
    repository_name = luigi.Parameter("exasol/script-language-container")
    tag_prefix = luigi.Parameter("")
    username = luigi.OptionalParameter(None, significant=False, visibility=ParameterVisibility.PRIVATE)
    password = luigi.OptionalParameter(None, significant=False, visibility=ParameterVisibility.PRIVATE)


class docker_build_arguments(luigi.Config):
    transparent = luigi.DictParameter(dict())
    image_changing = luigi.DictParameter(dict())
    secret = luigi.DictParameter(dict(),
                                 description="Will not be saved somewhere, but are also assumed to be transparent",
                                 visibility=ParameterVisibility.PRIVATE)
