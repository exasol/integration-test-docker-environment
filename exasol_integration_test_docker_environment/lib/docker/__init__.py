import docker


class ContextDockerClient(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._client = None

    def __enter__(self):
        self._client = docker.from_env(**self.kwargs)
        return self._client

    def __exit__(self, type_, value, traceback):
        if self._client is not None:
            self._client.close()
        self._client = None
