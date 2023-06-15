import contextlib

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


def exact_matcher(names):
    return lambda value: all(x == value for x in names)


def superset_matcher(names):
    return lambda value: all(x in value for x in names)


@contextlib.contextmanager
def container_named(*names, matcher=None):
    matcher = matcher if matcher else exact_matcher(names)
    with ContextDockerClient() as client:
        matches = [c for c in client.containers.list() if matcher(c.name)]
        yield matches[0] if matches else None
