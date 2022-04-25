import contextlib
import os
import tempfile
from pathlib import Path
from typing import Optional

import pkg_resources
from jinja2 import Template

from exasol_integration_test_docker_environment.lib import PACKAGE_NAME

global_log_file: Optional[Path] = None

LOG_ENV_VARIABLE_NAME = "EXA_BUILD_LOG"


def get_log_path(main_log_path: Path) -> Path:
    def_log_path = main_log_path / "main.log"
    env_log_path = os.getenv(LOG_ENV_VARIABLE_NAME)
    if env_log_path is not None:
        log_path = Path(env_log_path)
    else:
        log_path = def_log_path
    return log_path


def validate_log_file(log_file: Path):
    global global_log_file
    # If build config is set multiple times, we must ensure the output_directory does not change
    # The logging always will print to logfile in the first configured output directory (restriction by Luigi).
    if global_log_file is not None and global_log_file.absolute() != log_file.absolute():
        raise ValueError("Log file location for Luigi has been changed. "
                         "This is not allowed to change between consecutive task invocations.")
    global_log_file = log_file


@contextlib.contextmanager
def get_luigi_log_config(log_file_target: Path) -> Path:
    validate_log_file(log_file_target)
    template_str = pkg_resources.resource_string(PACKAGE_NAME, f"templates/luigi_log.conf")  # type: bytes
    template = Template(template_str.decode("utf-8"))
    rendered_template = template.render(log_file_target=str(log_file_target))
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_luigi_conf_path = Path(temp_dir) / "luigi_log.conf"
        with open(temp_luigi_conf_path, "w") as f:
            f.write(rendered_template)
        yield temp_luigi_conf_path
