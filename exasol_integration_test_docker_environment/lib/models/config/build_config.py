import json
from typing import (
    List,
    Optional,
    Tuple,
)

import luigi

from exasol_integration_test_docker_environment.cli.options.system_options import (
    DEFAULT_OUTPUT_DIRECTORY,
)


class build_config(luigi.Config):
    force_pull: bool = luigi.BoolParameter(False)  # type: ignore
    force_load: bool = luigi.BoolParameter(False)  # type: ignore
    force_rebuild: bool = luigi.BoolParameter(False)  # type: ignore
    force_rebuild_from: List[str] = luigi.ListParameter([])  # type: ignore
    log_build_context_content: bool = luigi.BoolParameter(False)  # type: ignore
    # keep_build_context = luigi.BoolParameter(False)
    temporary_base_directory: Optional[str] = luigi.OptionalParameter(None)  # type: ignore
    output_directory: str = luigi.Parameter(DEFAULT_OUTPUT_DIRECTORY)  # type: ignore
    cache_directory: Optional[str] = luigi.OptionalParameter("")  # type: ignore
    build_name: Optional[str] = luigi.OptionalParameter("")  # type: ignore


def set_output_directory(output_directory: Optional[str]):
    if output_directory is not None:
        luigi.configuration.get_config().set(
            "build_config", "output_directory", output_directory
        )


def set_build_config(
    force_rebuild: bool,
    force_rebuild_from: Tuple[str, ...],
    force_pull: bool,
    log_build_context_content: bool,
    output_directory: Optional[str],
    temporary_base_directory: Optional[str],
    cache_directory: Optional[str],
    build_name: Optional[str],
):
    luigi.configuration.get_config().set(
        "build_config", "force_rebuild", str(force_rebuild)
    )
    luigi.configuration.get_config().set(
        "build_config", "force_rebuild_from", json.dumps(force_rebuild_from)
    )
    luigi.configuration.get_config().set("build_config", "force_pull", str(force_pull))
    set_output_directory(output_directory)
    if temporary_base_directory is not None:
        luigi.configuration.get_config().set(
            "build_config", "temporary_base_directory", temporary_base_directory
        )
    if cache_directory is not None:
        luigi.configuration.get_config().set(
            "build_config", "cache_directory", cache_directory
        )
    if build_name is not None:
        luigi.configuration.get_config().set("build_config", "build_name", build_name)
    luigi.configuration.get_config().set(
        "build_config", "log_build_context_content", str(log_build_context_content)
    )
