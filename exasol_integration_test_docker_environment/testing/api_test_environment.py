import inspect
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any

from exasol_integration_test_docker_environment.cli.options.test_environment_options import LATEST_DB_VERSION
from exasol_integration_test_docker_environment.lib.api import spawn_test_environment
from exasol_integration_test_docker_environment.testing.exaslct_docker_test_environment import \
    ExaslctDockerTestEnvironment
from exasol_integration_test_docker_environment.testing.utils import find_free_ports, check_db_version_from_env


class ApiTestEnvironment:

    def __init__(self, test_object):
        self.test_object = test_object
        if not inspect.isclass(self.test_object):
            self.test_class = self.test_object.__class__
        else:
            self.test_class = self.test_object
        self.flavor_path = self.get_test_flavor()
        self.name = self.test_class.__name__
        self._repository_prefix = "exaslct_test"
        self.temp_dir = tempfile.mkdtemp()

    def get_test_flavor(self):
        source_file_of_test_object = inspect.getsourcefile(self.test_class)
        flavor_path = Path(os.path.realpath(source_file_of_test_object)).parent.joinpath(
            "resources/test-flavor")
        return flavor_path

    @property
    def docker_repository_name(self):
        return f"{self._repository_prefix.lower()}/{self.name.lower()}"  # docker repository names must be lowercase

    @property
    def repository_prefix(self):
        return self._repository_prefix

    @repository_prefix.setter
    def repository_prefix(self, value):
        self._repository_prefix = value

    @property
    def output_dir(self):
        return self.temp_dir

    @property
    def task_dependency_dot_file(self):
        return f"{self.name}.dot"

    def close(self):
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(e)

    def spawn_docker_test_environment(self, name: str, additional_parameter: Dict[str, Any] = None) \
            -> ExaslctDockerTestEnvironment:
        database_port, bucketfs_port = find_free_ports(2)
        on_host_parameter = ExaslctDockerTestEnvironment(
            name=self.name + "_" + name,
            database_host="localhost",
            db_username="sys",
            db_password="exasol",
            bucketfs_username="w",
            bucketfs_password="write",
            database_port=database_port,
            bucketfs_port=bucketfs_port)
        db_version_from_env = check_db_version_from_env()
        if additional_parameter is None:
            on_host_parameter.environment_info = \
                spawn_test_environment(environment_name=on_host_parameter.name,
                                       database_port_forward=on_host_parameter.database_port,
                                       bucketfs_port_forward=on_host_parameter.bucketfs_port,
                                       docker_db_image_version=db_version_from_env or LATEST_DB_VERSION,
                                       output_directory=self.temp_dir)
        else:
            on_host_parameter.environment_info = \
                spawn_test_environment(environment_name=on_host_parameter.name,
                                       database_port_forward=on_host_parameter.database_port,
                                       bucketfs_port_forward=on_host_parameter.bucketfs_port,
                                       docker_db_image_version=db_version_from_env or LATEST_DB_VERSION,
                                       output_directory=self.temp_dir,
                                       **additional_parameter)
        return on_host_parameter