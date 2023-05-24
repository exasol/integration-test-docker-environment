import math
from typing import Tuple

import docker
import humanfriendly
import luigi
import netaddr
import pkg_resources
from docker.models.containers import Container
from docker.models.volumes import Volume
from jinja2 import Template

from exasol_integration_test_docker_environment.lib import PACKAGE_NAME
from exasol_integration_test_docker_environment.lib.base.docker_base_task import DockerBaseTask
from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import JsonPickleParameter
from exasol_integration_test_docker_environment.lib.base.still_running_logger import StillRunningLogger
from exasol_integration_test_docker_environment.lib.data.container_info import ContainerInfo
from exasol_integration_test_docker_environment.lib.data.database_info import DatabaseInfo
from exasol_integration_test_docker_environment.lib.data.docker_network_info import DockerNetworkInfo
from exasol_integration_test_docker_environment.lib.docker.images.create.utils.pull_log_handler import PullLogHandler
from exasol_integration_test_docker_environment.lib.docker.images.image_info import ImageInfo
from exasol_integration_test_docker_environment.lib.test_environment.db_version import DbVersion
from exasol_integration_test_docker_environment.lib.test_environment.docker_container_copy import DockerContainerCopy
from exasol_integration_test_docker_environment.lib \
    .test_environment.parameter \
    .docker_db_test_environment_parameter import (
        DbOsAccess,
        DockerDBTestEnvironmentParameter,
)
from exasol_integration_test_docker_environment.lib.base.ssh_access import (
    SshFiles,
    SshKey,
)


BUCKETFS_PORT = "6583"
DB_PORT = "8888"
CERTIFICATES_MOUNT_DIR = "/certificates"
CERTIFICATES_DEFAULT_DIR = "/exa/etc/ssl/"


class SpawnTestDockerDatabase(DockerBaseTask, DockerDBTestEnvironmentParameter):
    environment_name = luigi.Parameter()  # type: str
    db_container_name = luigi.Parameter()  # type: str
    attempt = luigi.IntParameter(1)  # type: int
    network_info = JsonPickleParameter(DockerNetworkInfo, significant=False)  # type: DockerNetworkInfo
    ip_address_index_in_subnet = luigi.IntParameter(significant=False)  # type: int
    docker_runtime = luigi.OptionalParameter(None, significant=False)  # type: str
    certificate_volume_name = luigi.OptionalParameter(None, significant=False)
    additional_db_parameter = luigi.ListParameter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.ip_address_index_in_subnet < 0:
            raise Exception(
                "ip_address_index_in_subnet needs to be greater than 0 got %s"
                % self.ip_address_index_in_subnet)

        self.db_version = DbVersion.from_db_version_str(self.docker_db_image_version)
        self.docker_db_config_resource_name = f"docker_db_config/{self.db_version}"

    def run_task(self):
        subnet = netaddr.IPNetwork(self.network_info.subnet)
        db_ip_address = str(subnet[2 + self.ip_address_index_in_subnet])
        db_private_network = "{ip}/{prefix}".format(ip=db_ip_address, prefix=subnet.prefixlen)
        database_info = None
        if self.network_info.reused:
            database_info = self._try_to_reuse_database(db_ip_address)
        if database_info is None:
            database_info = self._create_database_container(db_ip_address, db_private_network)
        self.return_object(database_info)

    def _try_to_reuse_database(self, db_ip_address: str) -> DatabaseInfo:
        self.logger.info("Try to reuse database container %s",
                         self.db_container_name)
        database_info = None
        try:
            database_info = self._create_database_info(db_ip_address=db_ip_address, reused=True)
        except Exception as e:
            self.logger.warning("Tried to reuse database container %s, but got Exeception %s. "
                                "Fallback to create new database.", self.db_container_name, e)
        return database_info

    def _handle_output(self, output_generator, image_info: ImageInfo):
        log_file_path = self.get_log_path().joinpath("pull_docker_db_image.log")
        with PullLogHandler(log_file_path, self.logger, image_info) as log_handler:
            still_running_logger = StillRunningLogger(
                self.logger, "pull image %s" % image_info.get_source_complete_name())
            for log_line in output_generator:
                still_running_logger.log()
                log_handler.handle_log_lines(log_line)

    def _create_database_container(self, db_ip_address: str, db_private_network: str):
        self.logger.info("Starting database container %s", self.db_container_name)
        with self._get_docker_client() as docker_client:
            try:
                docker_client.containers.get(self.db_container_name).remove(force=True, v=True)
            except:
                pass
            docker_db_image_info = self._pull_docker_db_images_if_necessary()
            db_volume = self._prepare_db_volume(docker_client, db_private_network, docker_db_image_info)
            ports = {}
            if self.database_port_forward is not None:
                ports[f"{DB_PORT}/tcp"] = ('0.0.0.0', int(self.database_port_forward))
            if self.bucketfs_port_forward is not None:
                ports[f"{BUCKETFS_PORT}/tcp"] = ('0.0.0.0', int(self.bucketfs_port_forward))
            volumes = {db_volume.name: {"bind": "/exa", "mode": "rw"}}
            if self.certificate_volume_name is not None:
                volumes[self.certificate_volume_name] = {"bind": CERTIFICATES_MOUNT_DIR, "mode": "ro"}

            db_container = \
                docker_client.containers.create(
                    image="%s" % (docker_db_image_info.get_source_complete_name()),
                    name=self.db_container_name,
                    detach=True,
                    privileged=True,
                    volumes=volumes,
                    network_mode=None,
                    ports=ports,
                    runtime=self.docker_runtime
                )

            if self.db_os_access == DbOsAccess.SSH:
                files = SshFiles()
                sshkey = SshKey.from_folder(files.folder)
                copy = DockerContainerCopy(db_container)
                content = sshkey.public_key_as_string("itde-ssh-access")
                copy.add_string_to_file(".ssh/authorized_keys", content)
                copy.copy("/root/")

            docker_network = docker_client.networks.get(self.network_info.network_name)
            network_aliases = self._get_network_aliases()
            docker_network.connect(db_container, ipv4_address=db_ip_address, aliases=network_aliases)
            db_container.start()
            database_info = self._create_database_info(db_ip_address=db_ip_address, reused=False)
            return database_info

    def _get_network_aliases(self):
        network_aliases = ["exasol_test_database", "exasol-test-database", self.db_container_name]
        return network_aliases

    def _create_database_info(self, db_ip_address: str, reused: bool) -> DatabaseInfo:
        with self._get_docker_client() as docker_client:
            db_container = docker_client.containers.get(self.db_container_name)
            if db_container.status != "running":
                raise Exception(f"Container {self.db_container_name} not running")
            network_aliases = self._get_network_aliases()
            container_info = \
                ContainerInfo(container_name=self.db_container_name,
                              ip_address=db_ip_address,
                              network_aliases=network_aliases,
                              network_info=self.network_info,
                              volume_name=self._get_db_volume_name())
            database_info = \
                DatabaseInfo(host=db_ip_address, db_port=DB_PORT, bucketfs_port=BUCKETFS_PORT,
                             reused=reused, container_info=container_info)
            return database_info

    def _pull_docker_db_images_if_necessary(self):
        image_name = "exasol/docker-db"
        docker_db_image_info = ImageInfo(
            target_repository_name=image_name,
            source_repository_name=image_name,
            source_tag=self.docker_db_image_version,
            target_tag=self.docker_db_image_version,
            hash_value="", commit="",
            image_description=None)
        with self._get_docker_client() as docker_client:
            try:
                docker_client.images.get(docker_db_image_info.get_source_complete_name())
            except docker.errors.ImageNotFound as e:
                self.logger.info("Pulling docker-db image %s",
                                 docker_db_image_info.get_source_complete_name())
                output_generator = docker_client.api.pull(
                    docker_db_image_info.source_repository_name,
                    tag=docker_db_image_info.source_tag,
                    stream=True)
                self._handle_output(output_generator, docker_db_image_info)
        return docker_db_image_info

    def _prepare_db_volume(self, docker_client, db_private_network: str,
                           docker_db_image_info: ImageInfo) -> Volume:
        volume, container = self._prepare_volume(
            docker_client,
            self._get_db_volume_name(),
            self._get_db_volume_preparation_container_name(),
            remove_old_instances=True,
        )
        try:
            self._upload_init_db_files(container, db_private_network)
            self._execute_init_db(volume, container)
            return volume
        finally:
            container.remove(force=True)

    def _get_db_volume_preparation_container_name(self):
        return f"""{self.db_container_name}_preparation"""

    def _get_db_volume_name(self):
        return f"""{self.db_container_name}_volume"""

    def _remove_container(self, db_volume_preparation_container_name):
        try:
            with self._get_docker_client() as docker_client:
                docker_client.containers.get(db_volume_preparation_container_name).remove(force=True)
                self.logger.info("Removed container %s", db_volume_preparation_container_name)
        except docker.errors.NotFound:
            pass

    def _remove_volume(self, db_volume_name):
        try:
            with self._get_docker_client() as docker_client:
                docker_client.volumes.get(db_volume_name).remove(force=True)
                self.logger.info("Removed volume %s", db_volume_name)
        except docker.errors.NotFound:
            pass

    def _prepare_volume(
            self,
            docker_client,
            volume_name,
            container_name,
            remove_old_instances: bool = False,
    ) -> Tuple[Volume, Container]:
        """
        Create an intermediate Docker Container containing a volume that
        can be mounted into another Docker Container.
        """
        if remove_old_instances:
            self._remove_container(container_name)
            self._remove_volume(volume_name)
        volume = docker_client.volumes.create(volume_name)
        container = docker_client.containers.run(
                image="ubuntu:18.04",
                name=container_name,
                auto_remove=True,
                command="sleep infinity",
                detach=True,
                volumes={volume.name: {"bind": "/exa", "mode": "rw"}},
                labels={
                    "test_environment_name": self.environment_name,
                    "container_type": "db_container",
                }
        )
        return volume, container

    def _upload_init_db_files(self,
                              volume_preparation_container: Container,
                              db_private_network: str):
        copy = DockerContainerCopy(volume_preparation_container)
        init_db_script_str = pkg_resources.resource_string(
            PACKAGE_NAME,
            f"{self.docker_db_config_resource_name}/init_db.sh") # type: bytes

        copy.add_string_to_file("init_db.sh", init_db_script_str.decode("utf-8"))
        self._add_exa_conf(copy, db_private_network)
        copy.copy("/")

    def _add_exa_conf(self, copy: DockerContainerCopy,
                      db_private_network: str):
        certificate_dir = CERTIFICATES_MOUNT_DIR if self.certificate_volume_name is not None \
                            else CERTIFICATES_DEFAULT_DIR
        template_str = pkg_resources.resource_string(
            PACKAGE_NAME,
            f"{self.docker_db_config_resource_name}/EXAConf") # type: bytes
        template = Template(template_str.decode("utf-8"))
        additional_db_parameter_str = " ".join(self.additional_db_parameter)
        rendered_template = template.render(private_network=db_private_network,
                                            db_version=str(self.db_version),
                                            image_version=self.docker_db_image_version,
                                            mem_size=self.mem_size,
                                            disk_size=self.disk_size,
                                            name_servers=",".join(self.nameservers),
                                            certificate_dir=certificate_dir,
                                            additional_db_parameters=additional_db_parameter_str)
        copy.add_string_to_file("EXAConf", rendered_template)

    def _execute_init_db(self, db_volume: Volume, preparation_container: Container):
        disk_size_in_bytes = humanfriendly.parse_size(self.disk_size)
        min_overhead_in_gigabyte = 2  # Exasol needs at least a 2 GB larger device than the configured disk size
        overhead_factor = max(0.01, (
                min_overhead_in_gigabyte * 1024 * 1024 * 1024) / disk_size_in_bytes)  # and in general 1% larger
        device_size_in_bytes = disk_size_in_bytes * (1 + overhead_factor)
        device_size_in_megabytes = math.ceil(
            device_size_in_bytes / (1024 * 1024))  # The init_db.sh script works with MB, because its faster
        self.logger.info(
            f"Creating database volume of size {device_size_in_megabytes / 1024} GB using and overhead factor of {overhead_factor}")
        (exit_code, output) = preparation_container.exec_run(cmd=f"bash /init_db.sh {device_size_in_megabytes}")
        if exit_code != 0:
            raise Exception(
                "Error during preparation of docker-db volume %s got following output %s" % (db_volume.name, output))

    def cleanup_task(self, success):
        if (success and not self.no_database_cleanup_after_success) or \
                (not success and not self.no_database_cleanup_after_failure):
            volume_container = self._get_db_volume_preparation_container_name()
            try:
                self.logger.info(f"Cleaning up container %s", volume_container)
                self._remove_container(volume_container)
            except Exception as e:
                self.logger.error(f"Error during removing container %s: %s", volume_container, e)

            try:
                self.logger.info(f"Cleaning up container %s", self.db_container_name)
                self._remove_container(self.db_container_name)
            except Exception as e:
                self.logger.error(f"Error during removing container %s: %s", self.db_container_name, e)

            db_volume_name = self._get_db_volume_name()
            try:
                self.logger.info(f"Cleaning up docker volume %s", db_volume_name)
                self._remove_volume(db_volume_name)
            except Exception as e:
                self.logger.error(f"Error during removing docker volume %s: %s", db_volume_name, e)
