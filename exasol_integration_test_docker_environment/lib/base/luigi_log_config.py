import contextlib
import os
import tempfile
from pathlib import Path
from typing import Optional, Callable

import jinja2
import logging
from exasol_integration_test_docker_environment.lib import PACKAGE_NAME
from exasol_integration_test_docker_environment.lib.config.build_config import build_config

LOG_ENV_VARIABLE_NAME = "EXA_BUILD_LOG"

PROPAGATE = "PROPAGATE"

FILTERS = "FILTERS"

HANDLERS = "HANDLERS"

LOG_LEVEL = "LOG_LEVEL"

LUIGI_INTERFACE_LOGGER = "luigi-interface"

LUIGI_LOGGER = "luigi"


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
def restore_logger(logger_creator: Callable[[], logging.Logger]):
    before_logger = logger_creator()
    logger_info = {
        LOG_LEVEL: before_logger.level,
        HANDLERS: list(before_logger.handlers),
        FILTERS: list(before_logger.filters),
        PROPAGATE: before_logger.propagate
    }
    yield
    after_logger = logger_creator()
    after_logger.level = logger_info[LOG_LEVEL]
    after_logger.handlers = logger_info[HANDLERS]
    after_logger.filters = logger_info[FILTERS]
    after_logger.propagate = logger_info[PROPAGATE]


@contextlib.contextmanager
def get_luigi_log_config(log_file_target: Path,
                         use_job_specific_log_file: bool,
                         log_level: Optional[str] = None) -> Path:
    """
    Yields a context manager containing the path of the log-config file.
    log_file_target contains the location of the log-file.
    console_log_level indicates the log_level (@see https://docs.python.org/3/library/logging.html#logging-levels)
    The log-level for the log-file is always logging.DEBUG!
    """
    if log_level is None and use_job_specific_log_file:
        log_level = logging.getLevelName(logging.WARNING)
    env = jinja2.Environment(loader=jinja2.PackageLoader(PACKAGE_NAME),
                             autoescape=jinja2.select_autoescape())
    template = env.get_template("luigi_log.conf")
    rendered_template = template.render(console_log_level=log_level,
                                        log_file_target=str(log_file_target))
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_luigi_conf_path = Path(temp_dir) / "luigi_log.conf"
        with open(temp_luigi_conf_path, "w") as f:
            f.write(rendered_template)
        with restore_logger(logger_creator=lambda: logging.root), \
                restore_logger(logger_creator=lambda: logging.getLogger(LUIGI_INTERFACE_LOGGER)), \
                restore_logger(logger_creator=lambda: logging.getLogger(LUIGI_LOGGER)):
            if log_level is not None and not use_job_specific_log_file:
                logging.getLogger(LUIGI_INTERFACE_LOGGER).level = logging.getLevelName(log_level)
                logging.getLogger(LUIGI_LOGGER).level = logging.getLevelName(log_level)

            yield temp_luigi_conf_path
