import contextlib
import os
import tempfile
from pathlib import Path
from typing import Optional

import jinja2
import logging
from exasol_integration_test_docker_environment.lib import PACKAGE_NAME
from exasol_integration_test_docker_environment.lib.config.build_config import build_config

LOG_ENV_VARIABLE_NAME = "EXA_BUILD_LOG"

PROPAGATE = "PROPAGATE"

FILTERS = "FILTERS"

HANDLERS = "HANDLERS"

LOG_LEVEL = "LOG_LEVEL"


def get_log_path(job_id: str) -> Path:
    """
    Retrieve the log-file path. Default path is $output_path/jobs/logs/main.log, but can be overwritten by
    the environment variable LOG_ENV_VARIABLE_NAME.
    """
    main_log_path = Path(build_config().output_directory) / "jobs" / job_id / "logs"
    main_log_path.mkdir(parents=True, exist_ok=True)
    def_log_path = main_log_path / "main.log"
    env_log_path = os.getenv(LOG_ENV_VARIABLE_NAME)
    if env_log_path is not None:
        log_path = Path(env_log_path)
    else:
        log_path = def_log_path
    return log_path


@contextlib.contextmanager
def restore_root_logger(use_job_specific_log_file: bool):
    root_logger_info = None
    if use_job_specific_log_file:
        root_logger_info = {
            LOG_LEVEL: logging.root.level,
            HANDLERS: list(logging.root.handlers),
            FILTERS: list(logging.root.filters),
            PROPAGATE: logging.root.propagate
        }
    yield
    if use_job_specific_log_file and root_logger_info is not None:
        logging.root.level = root_logger_info[LOG_LEVEL]
        logging.root.handlers = root_logger_info[HANDLERS]
        logging.root.filters = root_logger_info[FILTERS]
        logging.root.propagate = root_logger_info[PROPAGATE]


@contextlib.contextmanager
def get_luigi_log_config(log_file_target: Path,
                         use_job_specific_log_file: bool,
                         console_log_level: Optional[str] = None) -> Path:
    """
    Yields a context manager containing the path of the log-config file.
    log_file_target contains the location of the log-file.
    console_log_level indicates the log_level (@see https://docs.python.org/3/library/logging.html#logging-levels)
    The log-level for the log-file is always logging.DEBUG!
    """
    if console_log_level is None:
        console_log_level = logging.getLevelName(logging.WARNING)
    env = jinja2.Environment(loader=jinja2.PackageLoader(PACKAGE_NAME),
                             autoescape=jinja2.select_autoescape())
    template = env.get_template("luigi_log.conf")
    rendered_template = template.render(console_log_level=console_log_level,
                                        log_file_target=str(log_file_target))
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_luigi_conf_path = Path(temp_dir) / "luigi_log.conf"
        with open(temp_luigi_conf_path, "w") as f:
            f.write(rendered_template)
        with restore_root_logger(use_job_specific_log_file=use_job_specific_log_file):
            yield temp_luigi_conf_path
