from typing import (
    List,
    Optional,
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
