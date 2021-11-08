import inspect
import json
import os
import shlex
import shutil
import socket
import subprocess
import tempfile
import time
from contextlib import closing
from pathlib import Path
from typing import List, Tuple

import requests

from exasol_integration_test_docker_environment.lib.data.environment_info import EnvironmentInfo
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient

INTEGRATION_TEST_DOCKER_ENVIRONMENT_DEFAULT_BIN="./start-test-env-without-poetry"


class ExaslctDockerTestEnvironment:
    def __init__(self, name: str, database_host: str,
                 db_username: str, db_password: str,
                 bucketfs_username: str, bucketfs_password: str,
                 database_port: int, bucketfs_port: int,
                 environment_info: EnvironmentInfo = None,
                 completed_process: subprocess.CompletedProcess = None):
        self.db_password = db_password
        self.db_username = db_username
        self.database_port = database_port
        self.bucketfs_port = bucketfs_port
        self.bucketfs_username = bucketfs_username
        self.bucketfs_password = bucketfs_password
        self.database_host = database_host
        self.name = name
        self.environment_info = environment_info
        self.completed_process = completed_process

    def close(self):
        remove_docker_container([f"test_container_{self.name}",
                                 f"db_container_{self.name}"])
        remove_docker_volumes([f"db_container_{self.name}_volume"])


class ExaslctTestEnvironment:

    def __init__(self, test_object, executable="./exaslct", clean_images_at_close=True):
        self.clean_images_at_close = clean_images_at_close
        self.executable = executable
        self.test_object = test_object
        if not inspect.isclass(self.test_object):
            self.test_class = self.test_object.__class__
        else:
            self.test_class = self.test_object
        self.flavor_path = self.get_test_flavor()
        self.name = self.test_class.__name__
        self._repository_prefix = "exaslct_test"
        if "GOOGLE_CLOUD_BUILD" in os.environ:
            # We need to put the output directories into the workdir, 
            # because only this is shared between the current container and
            # host. Only path within this shared directory can be mounted 
            # to docker container started by exaslct
            temp_dir_prefix_path = Path("./temp_outputs")
            temp_dir_prefix_path.mkdir(exist_ok=True)
            self.temp_dir = tempfile.mkdtemp(dir=temp_dir_prefix_path)
        else:
            self.temp_dir = tempfile.mkdtemp()
        self._update_attributes()

    def get_test_flavor(self):
        source_file_of_test_object = inspect.getsourcefile(self.test_class)
        flavor_path = Path(os.path.realpath(source_file_of_test_object)).parent.joinpath(
            "resources/test-flavor")
        return flavor_path

    @property
    def repository_prefix(self):
        return self._repository_prefix

    @repository_prefix.setter
    def repository_prefix(self, value):
        self._repository_prefix = value
        self._update_attributes()

    def _update_attributes(self):
        self.repository_name = f"{self._repository_prefix.lower()}/{self.name.lower()}"  # docker repository names must be lowercase
        self.flavor_path_argument = f"--flavor-path {self.get_test_flavor()}"
        self.docker_repository_arguments = f"--source-docker-repository-name {self.repository_name} --target-docker-repository-name {self.repository_name}"
        self.clean_docker_repository_arguments = f"--docker-repository-name {self.repository_name}"
        self.output_directory_arguments = f"--output-directory {self.temp_dir}"
        self.task_dependencies_argument = " ".join([f"--task-dependencies-dot-file {self.name}.dot", ])

    def clean_images(self):
        self.run_command(f"{self.executable} clean-flavor-images", clean=True)

    def run_command(self, command: str,
                    use_output_directory: bool = True,
                    use_flavor_path: bool = True,
                    use_docker_repository: bool = True,
                    track_task_dependencies: bool = False,
                    clean: bool = False,
                    capture_output: bool = False):
        if use_output_directory:
            command = f"{command} {self.output_directory_arguments}"
        if track_task_dependencies:
            command = f"{command} {self.task_dependencies_argument}"
        if use_flavor_path:
            command = f"{command} {self.flavor_path_argument}"
        if use_docker_repository and not clean:
            command = f"{command} {self.docker_repository_arguments}"
        if use_docker_repository and clean:
            command = f"{command} {self.clean_docker_repository_arguments}"
        print()
        print(f"command: {command}")
        if capture_output:
            completed_process = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            completed_process = subprocess.run(shlex.split(command))
        try:
            completed_process.check_returncode()
        except subprocess.CalledProcessError as e:
            print(e.stdout.decode("UTF-8"))
            raise e
        return completed_process

    def close(self):
        try:
            if self.clean_images_at_close:
                self.clean_images()
        except Exception as e:
            print(e)
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(e)

    def spawn_docker_test_environment(self, name, additional_parameter: List[str] = None) \
            -> Tuple[ExaslctDockerTestEnvironment, ExaslctDockerTestEnvironment]:
        on_host_parameter = ExaslctDockerTestEnvironment(
            name=self.name + "_" + name,
            database_host="localhost",
            db_username="sys",
            db_password="exasol",
            bucketfs_username="w",
            bucketfs_password="write",
            database_port=find_free_port(),
            bucketfs_port=find_free_port())
        docker_db_version_parameter = ""
        if "EXASOL_VERSION" in os.environ and os.environ["EXASOL_VERSION"] != "default":
            docker_db_version_parameter = f'--docker-db-image-version "{os.environ["EXASOL_VERSION"]}"'
        if additional_parameter is None:
            additional_parameter = []
        arguments = " ".join([f"--environment-name {on_host_parameter.name}",
                              f"--database-port-forward {on_host_parameter.database_port}",
                              f"--bucketfs-port-forward {on_host_parameter.bucketfs_port}",
                              docker_db_version_parameter] + additional_parameter)

        command = f"{self.executable} spawn-test-environment {arguments}"
        completed_process = self.run_command(command, use_flavor_path=False, use_docker_repository=False,
                                             capture_output=True)
        on_host_parameter.completed_process = completed_process
        environment_info_json_path = Path(self.temp_dir,
                                          f"cache/environments/{on_host_parameter.name}/environment_info.json")
        if environment_info_json_path.exists():
            with environment_info_json_path.open() as f:
                environment_info = EnvironmentInfo.from_json(f.read())
                on_host_parameter.environment_info = environment_info
        if "GOOGLE_CLOUD_BUILD" in os.environ:
            google_cloud_parameter = ExaslctDockerTestEnvironment(
                name=on_host_parameter.name,
                database_host="localhost",
                db_username=on_host_parameter.db_username,
                db_password=on_host_parameter.db_password,
                bucketfs_username=on_host_parameter.bucketfs_username,
                bucketfs_password=on_host_parameter.bucketfs_password,
                database_port=8888,
                bucketfs_port=6583,
                environment_info=on_host_parameter.completed_process,
                completed_process=on_host_parameter.completed_process
            )
            with ContextDockerClient() as docker_client:
                db_container = docker_client.containers.get(f"db_container_{google_cloud_parameter.name}")
                cloudbuild_network = docker_client.networks.get("cloudbuild")
                cloudbuild_network.connect(db_container)
                db_container.reload()
                google_cloud_parameter.database_host = \
                    db_container.attrs["NetworkSettings"]["Networks"][cloudbuild_network.name]["IPAddress"]
                return on_host_parameter, google_cloud_parameter
        else:
            return on_host_parameter, None

    def create_registry(self):
        registry_port = find_free_port()
        registry_container_name = self.name.replace("/", "_") + "_registry"
        with ContextDockerClient() as docker_client:
            print("Start pull of registry:2")
            docker_client.images.pull(repository="registry", tag="2")
            print(f"Start container of {registry_container_name}")
            try:
                docker_client.containers.get(registry_container_name).remove(force=True)
            except:
                pass
            registry_container = docker_client.containers.run(
                image="registry:2", name=registry_container_name,
                ports={5000: registry_port},
                detach=True
            )
            time.sleep(10)
            print(f"Finished start container of {registry_container_name}")
            if "GOOGLE_CLOUD_BUILD" in os.environ:
                cloudbuild_network = docker_client.networks.get("cloudbuild")
                cloudbuild_network.connect(registry_container)
                registry_container.reload()
                registry_host = registry_container.attrs["NetworkSettings"]["Networks"][cloudbuild_network.name][
                    "IPAddress"]
                # self.repository_prefix = f"{registry_host}:5000"
                self.repository_prefix = f"localhost:{registry_port}"
                return registry_container, registry_host, "5000"
            else:
                self.repository_prefix = f"localhost:{registry_port}"
                return registry_container, "localhost", registry_port


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = s.getsockname()[1]
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', port))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return port


def remove_docker_container(containers):
    with ContextDockerClient() as docker_client:
        for container in containers:
            try:
                docker_client.containers.get(container).remove(force=True)
            except Exception as e:
                print(e)

def remove_docker_volumes(volumes):
    with ContextDockerClient() as docker_client:
        for volume in volumes:
            try:
                docker_client.volumes.get(volume).remove(force=True)
            except Exception as e:
                print(e)


def request_registry_images(registry_host, registry_port, repo_name):
    url = f"http://{registry_host}:{registry_port}/v2/{repo_name}/tags/list"
    result = requests.request("GET", url)
    images = json.loads(result.content.decode("UTF-8"))
    return images


def request_registry_repositories(registry_host, registry_port):
    result = requests.request("GET", f"http://{registry_host}:{registry_port}/v2/_catalog/")
    repositories_ = json.loads(result.content.decode("UTF-8"))["repositories"]
    return repositories_
