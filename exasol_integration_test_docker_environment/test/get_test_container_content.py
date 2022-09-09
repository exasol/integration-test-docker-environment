from pathlib import Path
from typing import Tuple

from exasol_integration_test_docker_environment.lib.data.test_container_content_description import \
    TestContainerContentDescription, TestContainerBuildMapping, TestContainerRuntimeMapping

TEST_CONTAINER_PATH = Path(__file__).parent / "resources" / "test_container"


def get_test_container_content(runtime_mapping: Tuple[TestContainerRuntimeMapping] = tuple()) \
        -> TestContainerContentDescription:
    return TestContainerContentDescription(
        docker_file=f"{TEST_CONTAINER_PATH}/Dockerfile",
        build_files_and_directories=[TestContainerBuildMapping(source=TEST_CONTAINER_PATH / "test.txt",
                                                               target="test.text")],
        runtime_mappings=list(runtime_mapping)
    )
