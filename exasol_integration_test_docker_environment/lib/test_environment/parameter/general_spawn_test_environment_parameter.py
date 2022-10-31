import luigi
from luigi import Config

from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import JsonPickleParameter
from exasol_integration_test_docker_environment.lib.data.test_container_content_description import \
    TestContainerContentDescription


class GeneralSpawnTestEnvironmentParameter(Config):

    reuse_database_setup = luigi.BoolParameter(False, significant=False)
    reuse_test_container = luigi.BoolParameter(False, significant=False)
    no_test_container_cleanup_after_success = luigi.BoolParameter(False, significant=False)
    no_test_container_cleanup_after_failure = luigi.BoolParameter(False, significant=False)
    max_start_attempts = luigi.IntParameter(2, significant=False)
    docker_runtime = luigi.OptionalParameter(None, significant=False)
    create_certificates = luigi.BoolParameter()
    test_container_content = JsonPickleParameter(TestContainerContentDescription, is_optional=True)
    additional_db_parameter = luigi.ListParameter()
