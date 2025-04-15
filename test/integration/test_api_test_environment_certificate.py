import pytest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.db_version import (
    db_version_supports_custom_certificates,
)
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    get_test_container_content,
)
from exasol_integration_test_docker_environment.testing.api_test_environment import (
    ApiTestEnvironment,
)
from exasol_integration_test_docker_environment.testing.api_test_environment_context_provider import (
    build_api_context_provider_with_test_container,
)
from exasol_integration_test_docker_environment.testing.utils import (
    check_db_version_from_env,
)


@pytest.fixture(scope="module")
def environment_with_certificate(
    api_isolation_module: ApiTestEnvironment,
):
    # Abbreviate environment name to meet limitation of max. 63 characters for
    # certificate host name.
    api_isolation_module.name = "cert_test"
    additional_parameter = {"create_certificates": True}

    provider = build_api_context_provider_with_test_container(
        api_isolation_module, get_test_container_content()
    )
    with provider(
        None,
        additional_parameter,
    ) as db:
        yield db


@pytest.mark.skipif(
    not db_version_supports_custom_certificates(check_db_version_from_env()),
    reason="Database version does not support custom certificates.",
)
def test_certificate(environment_with_certificate):
    with ContextDockerClient() as docker_client:
        test_container_name = (
            environment_with_certificate.environment_info.test_container_info.container_name
        )
        test_container = docker_client.containers.get(test_container_name)
        database_container = (
            environment_with_certificate.environment_info.database_info.container_info.container_name
        )
        database_network_name = (
            environment_with_certificate.environment_info.database_info.container_info.network_info.network_name
        )
        db_port = (
            environment_with_certificate.environment_info.database_info.ports.database
        )

        openssl_check_cmd = f"openssl s_client -connect {database_container}.{database_network_name}:{db_port}"
        print(f"OpenSSL cmd:{openssl_check_cmd}")
        exit_code, output = test_container.exec_run(openssl_check_cmd)
        print(f"fOpenSSL out:{output}")
        assert exit_code == 0
        log = output.decode("utf-8")
        expected_subject = (
            f"subject=C = XX, ST = N/A, L = N/A, O = Self-signed certificate, "
            f"CN = {database_container}"
        )
        assert expected_subject in log, "Certificate check"
