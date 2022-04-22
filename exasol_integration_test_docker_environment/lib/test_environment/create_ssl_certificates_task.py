import docker
import luigi
import pkg_resources
from jinja2 import Template

from exasol_integration_test_docker_environment.lib import PACKAGE_NAME
from exasol_integration_test_docker_environment.lib.base.docker_base_task import DockerBaseTask
from exasol_integration_test_docker_environment.lib.data.docker_volume_info import DockerVolumeInfo
from exasol_integration_test_docker_environment.lib.test_environment.analyze_test_container import \
    DockerTestContainerBuild
from exasol_integration_test_docker_environment.lib.test_environment.docker_container_copy import \
    copy_script_to_container

CERTIFICATES_MOUNT_PATH = "/certificates"


class CreateSSLCertificatesTask(DockerBaseTask):
    environment_name = luigi.Parameter()
    test_container_name = luigi.Parameter()
    docker_runtime = luigi.OptionalParameter(None, significant=False)
    db_container_name = luigi.Parameter(significant=False)
    network_name = luigi.Parameter()
    reuse = luigi.BoolParameter(False, significant=False)
    no_cleanup_after_success = luigi.BoolParameter(False, significant=False)
    no_cleanup_after_failure = luigi.BoolParameter(False, significant=False)
    volume_name = luigi.Parameter()

    def run_task(self):
        self.volume_info = None
        if self.reuse:
            self.logger.info("Try to reuse volume %s", self.volume_name)
            try:
                self.volume_info = self.get_volume_info(reused=True)
            except Exception as e:
                self.logger.warning(f"Tried to reuse volume {self.volume_name}, but got Exeception {e}. "
                                    "Fallback to create new volume.")
        if self.volume_info is None:
            self.volume_info = self.create_docker_volume()
            self.create_certificate()

        self.return_object(self.volume_info)

    def register_required(self):
        self.test_container_image_future = \
            self.register_dependency(self.create_child_task(task_class=DockerTestContainerBuild))


    def get_volume_info(self, reused: bool) -> DockerVolumeInfo:
        with self._get_docker_client() as docker_client:
            volume_properties = docker_client.api.inspect_volume(self.volume_name)
            if volume_properties['Name'] == self.volume_name:
                return DockerVolumeInfo(volume_name=str(self.volume_name),
                                        mount_point=volume_properties['Mountpoint'], reused=reused)

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
        if (success and not self.no_cleanup_after_success) or \
                (not success and not self.no_cleanup_after_failure):
            try:
                self.logger.info(f"Cleaning up volume %s:", self.volume_name)
                self.remove_volume(self.volume_name)
            except Exception as e:
                self.logger.error(f"Error during removing volume %s: %s:", self.volume_name, e)

    @property
    def _construct_complete_host_name(self):
        """
        Example: 'db_container_exasol_test.db_network_exasol_test'
        """
        return f"{self.db_container_name}.{self.network_name}"

    def create_certificate(self) -> None:
        script_name = "create_certificates.sh"
        template_str = pkg_resources.resource_string(
            PACKAGE_NAME,
            f"test_container_config/{script_name}")  # type: bytes
        template = Template(template_str.decode("utf-8"))
        rendered_template = template.render(HOST_NAME=self._construct_complete_host_name,
                                            cert_dir=CERTIFICATES_MOUNT_PATH)
        test_container_image_info = \
            self.get_values_from_futures(self.test_container_image_future)["test-container"]  # type:

        volumes = {
            self.volume_info.volume_name: {
                "bind": CERTIFICATES_MOUNT_PATH,
                "mode": "rw"
            }
        }

        with self._get_docker_client() as docker_client:
            try:
                test_container = \
                    docker_client.containers.create(
                        image=test_container_image_info.get_target_complete_name(),
                        name=self.test_container_name,
                        network_mode=None,
                        command="sleep infinity",
                        detach=True,
                        volumes=volumes,
                        labels={"test_environment_name": self.environment_name, "container_type": "test_container"},
                        runtime=self.docker_runtime
                    )
                test_container.start()
                script_path_in_container = f"scripts/{script_name}"
                copy_script_to_container(rendered_template, script_path_in_container, test_container)

                self.logger.info("Creating certificates...")
                exit_code, output = test_container.exec_run(f"bash {script_path_in_container}")
                self.logger.info(output.decode('utf-8'))
                if exit_code != 0:
                    raise RuntimeError(f"Error creating certificates:'{output.decode('utf-8')}'")
            finally:
                test_container.stop()
                test_container.remove()
