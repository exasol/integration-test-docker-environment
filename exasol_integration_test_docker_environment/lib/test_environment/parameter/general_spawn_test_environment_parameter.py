import luigi
from luigi import Config

from exasol_integration_test_docker_environment.lib.test_environment.parameter.test_container_parameter import \
    OptionalTestContainerParameter


class GeneralSpawnTestEnvironmentParameter(OptionalTestContainerParameter):
    reuse_database_setup = luigi.BoolParameter(False, significant=False)
    reuse_test_container = luigi.BoolParameter(False, significant=False)
    no_test_container_cleanup_after_success = luigi.BoolParameter(False, significant=False)
    no_test_container_cleanup_after_failure = luigi.BoolParameter(False, significant=False)
    max_start_attempts = luigi.IntParameter(2, significant=False)
    docker_runtime = luigi.OptionalParameter(None, significant=False)
    create_certificates = luigi.BoolParameter()
    additional_db_parameter = luigi.ListParameter()
