from typing import (
    Dict,
    Generator,
    Optional,
    Set,
)

import docker
import luigi

import exasol_integration_test_docker_environment.certificate_resources.container
from exasol_integration_test_docker_environment.lib.base.base_task import BaseTask
from exasol_integration_test_docker_environment.lib.base.docker_base_task import (
    DockerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.pickle_target import (
    PickleTarget,
)
from exasol_integration_test_docker_environment.lib.data.docker_volume_info import (
    DockerVolumeInfo,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageInfo,
)
from exasol_integration_test_docker_environment.lib.test_environment.create_certificates.analyze_certificate_container import (
    DockerCertificateBuildBase,
    DockerCertificateContainerBuild,
)
from exasol_integration_test_docker_environment.lib.utils.resource_directory import (
    ResourceDirectory,
)

CERTIFICATES_MOUNT_PATH = "/certificates"


class CreateSSLCertificatesTask(DockerBaseTask):
    environment_name: str = luigi.Parameter()  # type: ignore
    docker_runtime: Optional[str] = luigi.OptionalParameter(None, significant=False)  # type: ignore
    db_container_name: str = luigi.Parameter(significant=False)  # type: ignore
    network_name: str = luigi.Parameter()  # type: ignore
    reuse: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    no_cleanup_after_success: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    no_cleanup_after_failure: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    volume_name: str = luigi.Parameter()  # type: ignore

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._temp_resource_directory = ResourceDirectory(
            exasol_integration_test_docker_environment.certificate_resources.container
        )
        self._temp_resource_directory.create()

    def on_failure(self, exception):
        super().on_failure(exception)
        self._temp_resource_directory.cleanup()

    def on_success(self):
        super().on_success()
        self._temp_resource_directory.cleanup()

    def run_task(self):
        self.volume_info = None
        image_infos = yield from self.build_image()
        if self.reuse:
            self.logger.info("Try to reuse volume %s", self.volume_name)
            try:
                self.volume_info = self.get_volume_info(reused=True)
            except Exception as e:
                self.logger.warning(
                    f"Tried to reuse volume {self.volume_name}, but got Exeception {e}. "
                    "Fallback to create new volume."
                )
        if self.volume_info is None:
            self.volume_info = self.create_docker_volume()
            self.create_certificate(image_infos)

        self.return_object(self.volume_info)

    def build_image(self) -> Generator[BaseTask, None, Set[ImageInfo]]:
        task = self.create_child_task(
            task_class=DockerCertificateContainerBuild,
            certificate_container_root_directory=self._temp_resource_directory.tmp_directory,
        )
        image_infos_future = yield from self.run_dependencies(task)
        image_infos: Set[ImageInfo] = self.get_values_from_future(image_infos_future)  # type: ignore
        return image_infos

    def get_volume_info(self, reused: bool) -> DockerVolumeInfo:
        with self._get_docker_client() as docker_client:
            volume_properties = docker_client.api.inspect_volume(self.volume_name)
            if volume_properties["Name"] == self.volume_name:
                return DockerVolumeInfo(
                    volume_name=str(self.volume_name),
                    mount_point=volume_properties["Mountpoint"],
                    reused=reused,
                )
        raise RuntimeError(
            f"Volume Info not found for created volume {self.volume_name}"
        )

    def create_docker_volume(self) -> DockerVolumeInfo:
        self.remove_volume(self.volume_name)
        with self._get_docker_client() as docker_client:
            volume = docker_client.volumes.create(
                name=self.volume_name,
            )
            volume_info = self.get_volume_info(reused=False)
        return volume_info

    def remove_volume(self, volume_name):
        try:
            with self._get_docker_client() as docker_client:
                docker_client.volumes.get(volume_name).remove()
                self.logger.info("Removed volume %s", volume_name)
        except docker.errors.NotFound:
            pass

    def cleanup_task(self, success):
        if (success and not self.no_cleanup_after_success) or (
            not success and not self.no_cleanup_after_failure
        ):
            try:
                self.logger.info(f"Cleaning up volume %s:", self.volume_name)
                self.remove_volume(self.volume_name)
            except Exception as e:
                self.logger.error(
                    f"Error during removing volume %s: %s:", self.volume_name, e
                )

    @property
    def _construct_complete_host_name(self):
        """
        Example: 'db_container_exasol_test.db_network_exasol_test'
        """
        return f"{self.db_container_name}.{self.network_name}"

    def create_certificate(self, image_infos: Dict[str, ImageInfo]) -> None:
        certificate_container_image_info = image_infos[DockerCertificateBuildBase.GOAL]

        volumes = {
            self.volume_info.volume_name: {
                "bind": CERTIFICATES_MOUNT_PATH,
                "mode": "rw",
            }
        }

        with self._get_docker_client() as docker_client:
            try:
                container = docker_client.containers.create(
                    image=certificate_container_image_info.get_target_complete_name(),
                    name="certificate_resources",
                    network_mode=None,
                    command="sleep infinity",
                    detach=True,
                    volumes=volumes,
                    labels={
                        "test_environment_name": self.environment_name,
                        "container_type": "certificate_resources",
                    },
                    runtime=self.docker_runtime,
                )
                container.start()
                self.logger.info("Creating certificates...")
                cmd = (
                    f"bash /scripts/create_certificates.sh "
                    f"{self._construct_complete_host_name} {CERTIFICATES_MOUNT_PATH}"
                )
                exit_code, output = container.exec_run(cmd)
                self.logger.info(output.decode("utf-8"))
                if exit_code != 0:
                    raise RuntimeError(
                        f"Error creating certificates:'{output.decode('utf-8')}'"
                    )
            finally:
                container.stop()
                container.remove()
