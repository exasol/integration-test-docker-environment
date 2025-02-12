from pathlib import Path
from typing import (
    List,
    Optional,
)

from exasol_integration_test_docker_environment.lib.base.info import Info


class TestContainerBuildMapping(Info):
    """
    Represents a mapping of a build artifact for the test-container.
    The artifact will be copied to location "target", parallel to the Dockerfile and is hence accessible
    from within the Dockerfile during the build time of the test-container.
    """

    def __init__(self, source: Path, target: str):
        self.source = source
        self.target = target


class TestContainerRuntimeMapping(Info):
    """
    Represents a mapping of a runtime artifact for the test-container.
    This artifact will be bind-mounted to the test-container during startup.
    Optionally, the content will be copied within the test-container to the location indicated by parameter
    "deployement_target": This is useful if the source path must not be polluted with runtime artifacts (logs, etc.).
    """

    def __init__(
        self, source: Path, target: str, deployment_target: Optional[str] = None
    ):
        self.source = source
        self.target = target
        self.deployment_target = deployment_target


class TestContainerContentDescription(Info):
    """
    This class contains all information necessary to build, start and set up the test-container.
    Its purpose is to give the client control about the build- and runtime-artifacts.
    """

    def __init__(
        self,
        docker_file: Optional[str],
        build_files_and_directories: List[TestContainerBuildMapping],
        runtime_mappings: List[TestContainerRuntimeMapping],
    ):
        self.docker_file = docker_file
        self.build_files_and_directories = build_files_and_directories
        self.runtime_mappings = runtime_mappings
