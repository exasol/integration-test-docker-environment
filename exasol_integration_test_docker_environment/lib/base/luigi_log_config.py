import contextlib
import tempfile
from pathlib import Path

import pkg_resources
from jinja2 import Template

from exasol_integration_test_docker_environment.lib import PACKAGE_NAME
from exasol_integration_test_docker_environment.lib.base.dynamic_symlink import DynamicSymlink


@contextlib.contextmanager
def get_luigi_log_config(log_file: Path, log_file_target: Path) -> Path:
    template_str = pkg_resources.resource_string(PACKAGE_NAME, f"templates/luigi_log.conf")  # type: bytes
    template = Template(template_str.decode("utf-8"))
    rendered_template = template.render(log_file_target=str(log_file))
    print(f"Luigi Config:{rendered_template}")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_luigi_conf_path = Path(temp_dir) / "luigi_log.conf"
        with open(temp_luigi_conf_path, "w") as f:
            f.write(rendered_template)
        yield temp_luigi_conf_path


# class LuigiLogConfig(object):
#
#     def __init__(self, dynamic_symlink: DynamicSymlink, log_file_target: Path):
#         self.dynamic_symlink = dynamic_symlink
#         self.log_file_target = log_file_target
#
#     def __enter__(self):
#         print("LuigiLogConfig - enter")
#         self.log_sym_link = self.dynamic_symlink.point_to(self.log_file_target)
#         self.log_sym_link.__enter__()
#         template_str = pkg_resources.resource_string(PACKAGE_NAME, f"templates/luigi_log.conf")  # type: bytes
#         template = Template(template_str.decode("utf-8"))
#         rendered_template = template.render(log_file_target=str(self.log_sym_link.symlink_path))
#         self.temp_dir = tempfile.TemporaryDirectory()
#         self.luigi_conf_path = Path(self.temp_dir.name) / "luigi_log.conf"
#         with open(self.luigi_conf_path, "w") as f:
#             f.write(rendered_template)
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         print("LuigiLogConfig - exit")
#         self.temp_dir.cleanup()
#         self.log_sym_link.__exit__(exc_type, exc_val, exc_tb)
