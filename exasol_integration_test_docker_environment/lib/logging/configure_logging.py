import contextlib
import warnings
from collections.abc import Iterator
from pathlib import Path
from typing import (
    Optional,
)

import luigi
from luigi.parameter import UnconsumedParameterWarning
from luigi.setup_logging import InterfaceLogging

from exasol_integration_test_docker_environment.lib.logging.luigi_log_config import (
    get_luigi_log_config,
)


@contextlib.contextmanager
def configure_logging(
    log_file_path: Path, log_level: Optional[str], use_job_specific_log_file: bool
) -> Iterator[dict[str, str]]:
    with get_luigi_log_config(
        log_file_target=log_file_path,
        log_level=log_level,
        use_job_specific_log_file=use_job_specific_log_file,
    ) as luigi_config:
        no_configure_logging, run_kwargs = _configure_logging_parameter(
            log_level=log_level,
            luigi_config=luigi_config,
            use_job_specific_log_file=use_job_specific_log_file,
        )
        # We need to set InterfaceLogging._configured to false,
        # because otherwise luigi doesn't accept the new config.
        InterfaceLogging._configured = False
        luigi.configuration.get_config().set(
            "core", "no_configure_logging", str(no_configure_logging)
        )
        with warnings.catch_warnings():
            # This filter is necessary, because luigi uses the config no_configure_logging,
            # but doesn't define it, which seems to be a bug in luigi
            warnings.filterwarnings(
                action="ignore",
                category=UnconsumedParameterWarning,
                message=".*no_configure_logging.*",
            )
            yield run_kwargs


def _configure_logging_parameter(
    log_level: Optional[str], luigi_config: Path, use_job_specific_log_file: bool
) -> tuple[bool, dict[str, str]]:
    if use_job_specific_log_file:
        no_configure_logging = False
        run_kwargs = {"logging_conf_file": f"{luigi_config}"}
    else:
        no_configure_logging = True
        run_kwargs = {}
    return no_configure_logging, run_kwargs
