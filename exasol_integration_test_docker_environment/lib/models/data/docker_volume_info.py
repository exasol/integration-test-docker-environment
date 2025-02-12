from exasol_integration_test_docker_environment.lib.base.info import Info


class DockerVolumeInfo(Info):

    def __str__(self):
        return (
            f"DockerVolumeInfo: \n"
            f'volume_name="{self.volume_name}"\n'
            f"reused={self.reused}\n"
            f"mount_point={self.mount_point}"
        )

    def __init__(self, volume_name: str, mount_point: str, reused: bool = False):
        self.volume_name = volume_name
        self.reused = reused
        self.mount_point = mount_point
