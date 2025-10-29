from collections.abc import Iterator
from pathlib import PurePath

import luigi
import pytest

from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)
from exasol_integration_test_docker_environment.lib.models.data.test_container_content_description import (
    TestContainerRuntimeMapping,
)
from exasol_integration_test_docker_environment.lib.test_environment.database_setup.populate_data import (
    PopulateTestDataToDatabase,
)
from exasol_integration_test_docker_environment.lib.test_environment.db_version import (
    DbVersion,
)
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    FULL_TEST_CONTAINER_PATH,
    TEST_DATA_ROOT_PATH,
    get_test_container_content,
)
from exasol_integration_test_docker_environment.testing.api_test_environment import (
    ApiTestEnvironment,
)
from exasol_integration_test_docker_environment.testing.api_test_environment_context_provider import (
    build_api_context_provider_with_test_container,
)
from exasol_integration_test_docker_environment.testing.exaslct_docker_test_environment import (
    ExaslctDockerTestEnvironment,
)


class TestDataPopulateData(PopulateTestDataToDatabase):

    db_version: str = luigi.Parameter()

    def get_data_path_within_test_container(self) -> PurePath:
        return PurePath("/test_data")

    def get_data_file_within_data_path(self) -> PurePath:
        if DbVersion.from_db_version_str(self.db_version) >= DbVersion(2025, 1, 0):
            return PurePath("import_ignore_cert.sql")
        else:
            return PurePath("import.sql")


def _populate_data(environment: ExaslctDockerTestEnvironment):
    task = generate_root_task(
        task_class=TestDataPopulateData,
        environment_name=environment.name,
        db_user=environment.db_username,
        db_password=environment.db_password,
        bucketfs_write_password=environment.bucketfs_password,
        test_environment_info=environment.environment_info,
        db_version=environment.docker_db_image_version,
    )
    try:
        success = luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        if not success:
            raise Exception("Task failed")
    except Exception as e:
        task.cleanup(False)
        raise RuntimeError("Error uploading test file.") from e


def _get_test_container_runtime_mapping():
    test_data_folder = TEST_DATA_ROOT_PATH
    test_container_runtime_mapping = TestContainerRuntimeMapping(
        source=test_data_folder, target="/test_data"
    )
    return test_container_runtime_mapping


@pytest.fixture(scope="module")
def api_env_with_test_container_with_test_data(
    api_isolation_module: ApiTestEnvironment,
) -> Iterator[ExaslctDockerTestEnvironment]:
    env_context = build_api_context_provider_with_test_container(
        test_environment=api_isolation_module,
        default_test_container_content=get_test_container_content(
            FULL_TEST_CONTAINER_PATH, (_get_test_container_runtime_mapping(),)
        ),
    )
    with env_context(name=None, additional_parameters=None) as env:
        yield env


@pytest.fixture()
def clean_test_data(
    api_env_with_test_container_with_test_data: ExaslctDockerTestEnvironment,
):
    yield
    with api_env_with_test_container_with_test_data.create_connection() as connection:
        connection.execute("DROP SCHEMA IF EXISTS TEST CASCADE;")


def test_populate_data(
    api_env_with_test_container_with_test_data: ExaslctDockerTestEnvironment,
    clean_test_data,
):
    _populate_data(api_env_with_test_container_with_test_data)
    with api_env_with_test_container_with_test_data.create_connection() as connection:
        result = connection.execute("SELECT count(*) FROM TEST.ENGINETABLE;").fetchall()
        expected_result = [(100,)]
        assert result == expected_result


def test_populate_twice_throws_exception(
    api_env_with_test_container_with_test_data, clean_test_data
):
    _populate_data(api_env_with_test_container_with_test_data)
    with pytest.raises(RuntimeError):
        _populate_data(api_env_with_test_container_with_test_data)
