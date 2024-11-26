import json
import multiprocessing as mp

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.logging.abstract_log_handler import (
    AbstractLogHandler,
)


class DockerRegistryImageCheckerPullLogHandler(AbstractLogHandler):

    def __init__(self):
        super().__init__(None, None)
        self.result = False

    def handle_log_line(self, log_line, error: bool = False):
        json_output = json.loads(log_line)
        # TODO logging
        if "status" in json_output and json_output["status"].startswith("Pulling"):
            return True
        elif "errorDetail" in json_output:
            return False


class DockerRegistryImageChecker:
    def map(self, image: str, queue: mp.Queue):

        with ContextDockerClient() as docker_client:
            try:
                generator = docker_client.api.pull(repository=image, stream=True)
                for log_line in generator:
                    queue.put(log_line)
                queue.put(None)
            except Exception as e:
                queue.put(e)

    def check(self, image: str):
        log_handler = DockerRegistryImageCheckerPullLogHandler()
        queue: mp.Queue = mp.Queue()
        process = mp.Process(target=self.map, args=(image, queue))
        process.start()
        try:
            while True:
                value = queue.get()
                if isinstance(value, Exception):
                    raise value
                elif isinstance(value, bytes):
                    return any(log_handler.handle_log_lines(value))
                elif value is None:
                    return False
                else:
                    raise RuntimeError(
                        f"Should not happen. Programming Error. Unknown value {value}"
                    )
        finally:
            process.terminate()
