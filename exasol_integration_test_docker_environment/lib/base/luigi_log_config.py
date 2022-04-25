import contextlib
import tempfile
from pathlib import Path

import pkg_resources
from jinja2 import Template

from exasol_integration_test_docker_environment.lib import PACKAGE_NAME


@contextlib.contextmanager
def get_luigi_log_config(log_file_target: Path) -> Path:
    template_str = pkg_resources.resource_string(PACKAGE_NAME, f"templates/luigi_log.conf")  # type: bytes
    template = Template(template_str.decode("utf-8"))
    rendered_template = template.render(log_file_target=str(log_file_target))
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_luigi_conf_path = Path(temp_dir) / "luigi_log.conf"
        with open(temp_luigi_conf_path, "w") as f:
            f.write(rendered_template)
        yield temp_luigi_conf_path
