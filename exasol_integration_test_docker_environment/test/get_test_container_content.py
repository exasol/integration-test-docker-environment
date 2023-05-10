from pathlib import Path
from typing import Tuple

from exasol_integration_test_docker_environment.lib.data.test_container_content_description import \
    TestContainerContentDescription, TestContainerBuildMapping, TestContainerRuntimeMapping

TEST_CONTAINER_ROOT_PATH = Path(__file__).parent / "resources" / "test_container"

FULL_TEST_CONTAINER_PATH = TEST_CONTAINER_ROOT_PATH / "full"
MOCK_TEST_CONTAINER_PATH = TEST_CONTAINER_ROOT_PATH / "mock"


def get_test_container_content(test_container_path: Path = FULL_TEST_CONTAINER_PATH,
                               runtime_mapping: Tuple[TestContainerRuntimeMapping] = tuple()) \
        -> TestContainerContentDescription:
    return TestContainerContentDescription(
        docker_file=str(test_container_path / "Dockerfile"),
        build_files_and_directories=[TestContainerBuildMapping(source=test_container_path / "test.txt",
                                                               target="test.text")],
        runtime_mappings=list(runtime_mapping)
    )
