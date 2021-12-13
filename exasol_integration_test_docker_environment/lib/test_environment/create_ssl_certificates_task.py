import docker
import luigi

from exasol_integration_test_docker_environment.lib.base.docker_base_task import DockerBaseTask
from exasol_integration_test_docker_environment.lib.data.docker_volume_info import DockerVolumeInfo
from exasol_integration_test_docker_environment.lib.test_environment.shell.create_certificate import create_certificate


class CreateSSLCertificatesTask(DockerBaseTask):
    db_container_name = luigi.Parameter(significant=False)
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
        self.return_object(self.volume_info)

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
            create_certificate(host_name=str(self.db_container_name), certificate_dir=volume_info.mount_point)
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

