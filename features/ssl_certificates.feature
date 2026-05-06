Feature: SSL Certificate Generation

  Scenario: SSL certificates are created and injected when requested
    Given a database version greater than 7.0.5
    And an environment name short enough for a valid certificate CN (at most 63 characters)
    When `api.spawn_test_environment` is called with `create_certificates=True`
    Then running `openssl s_client -connect <db_container>.<network>:<db_port>` from the test container exits with code 0
    And the TLS certificate subject contains `CN = <db_container_name>`
    And the certificate is self-signed by "O = Self-signed certificate"

  Scenario: Certificate creation is skipped for unsupported database versions
    Given a database version 7.0.5 or earlier
    When `spawn_test_environment_with_docker_db` is called with `create_certificates=True`
    Then a ValueError is raised stating the minimum supported version is 7.0.6

  Scenario: Certificate support is correctly detected by version string
    When the helper `db_version_supports_custom_certificates` is called with version "7.0.5"
    Then it returns False
    When it is called with version "7.0.14"
    Then it returns True
    When it is called with version "7.1.3"
    Then it returns True
    When it is called with an unparseable version string "7abc"
    Then it raises a ValueError
