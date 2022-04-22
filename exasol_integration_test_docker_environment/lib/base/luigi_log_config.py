import contextlib
import tempfile
from pathlib import Path

import pkg_resources
from jinja2 import Template

from exasol_integration_test_docker_environment.lib import PACKAGE_NAME
from exasol_integration_test_docker_environment.lib.base.dynamic_symlink import DynamicSymlink


@contextlib.contextmanager
def get_luigi_log_config(dynamic_symlink: DynamicSymlink, log_file_target: Path) -> Path:

    with dynamic_symlink.point_to(log_file_target) as log_sym_link:
        template_str = pkg_resources.resource_string(
            PACKAGE_NAME,
            f"templates/luigi_log.conf")  # type: bytes
        template = Template(template_str.decode("utf-8"))
        rendered_template = template.render(log_file_target=str(log_sym_link.symlink_path))
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "luigi_log.conf"
            with open(temp_path, "f") as f:
                f.write(rendered_template)
            yield temp_path
