from docker.models.containers import Container
import io
import tarfile
import time

class DockerContainerCopy:

    def __init__(self, container:Container):
        super().__init__()
        self.open = True
        self.file_like_object = io.BytesIO()
        self.tar = tarfile.open(fileobj=self.file_like_object, mode="x")
        self.container = container

    def __del__(self):
        if self.open:
            self.tar.close()
            self.open = False
            self.tar = None
            self.file_like_object = None


    def is_open_or_raise(self):
        if not self.open:
            raise Exception("DockerContainerCopy not open")

    def add_string_to_file(self, name: str, string: str):
        self.is_open_or_raise()
        encoded = string.encode('utf-8')
        bytes_io = io.BytesIO(encoded)
        tar_info = tarfile.TarInfo(name=name)
        tar_info.mtime = time.time()
        tar_info.size = len(encoded)
        self.tar.addfile(tarinfo=tar_info, fileobj=bytes_io)

    def add_file(self, host_path:str, path_in_tar:str):
        self.is_open_or_raise()
        self.tar.add(host_path, path_in_tar)

    def copy(self, path_in_container:str):
        self.is_open_or_raise()
        self.tar.close()
        self.open = False
        self.tar = None
        self.container.put_archive(path_in_container, self.file_like_object.getbuffer().tobytes())
        self.file_like_object = None


def copy_script_to_container(script: str, script_path: str, container: Container):
    """
    Copy a script, given as string, to the container under specified location, relative to "/"
    """
    docker_container_copy = DockerContainerCopy(container)
    docker_container_copy.add_string_to_file(script_path, script)
    docker_container_copy.copy("/")
