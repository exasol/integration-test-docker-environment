Feature: Spawn Test Environment — Happy Path

  Background:
    Given the Docker daemon is available and the platform is supported
    And no containers named with the given environment name already exist

  Scenario: Spawn a default test environment via the API
    Given an environment name "test-env-1"
    When `api.spawn_test_environment(environment_name="test-env-1")` is called
    Then the call returns a tuple of (EnvironmentInfo, cleanup_function)
    And exactly two Docker containers are running:
      | container role | name pattern                  |
      | database       | db_container_test-env-1       |
      | test container | test_container_test-env-1     |
    And the EnvironmentInfo contains the database host, internal ports, and network name
    And the database accepts SQL connections on the reported host and port

  Scenario: Spawn environment with explicit database port forward
    Given an environment name "test-env-2"
    And a free host port 54321 is available
    When `api.spawn_test_environment(environment_name="test-env-2", database_port_forward=54321)` is called
    Then the EnvironmentInfo.database_info.forwarded_ports.database equals 54321
    And the Exasol database is reachable from the host on port 54321

  Scenario: Spawn environment with BucketFS HTTP and HTTPS port forwards
    Given an environment name "test-env-3"
    And two free host ports are selected
    When `api.spawn_test_environment` is called with `bucketfs_http_port_forward` and `bucketfs_https_port_forward`
    Then BucketFS is accessible via HTTP on the forwarded HTTP port from the host
    And BucketFS is accessible via HTTPS on the forwarded HTTPS port from the host
    And both forwarded port numbers are greater than 0
    And the two forwarded port numbers are distinct

  Scenario: Spawn environment with custom nameservers
    Given an environment name "test-env-ns"
    When `api.spawn_test_environment` is called with `nameserver=("8.8.8.8", "8.8.8.9")`
    Then the EXAConf inside the database container contains "NameServers = 8.8.8.8,8.8.8.9"

  Scenario: Spawn environment with docker environment variables
    Given an environment name "test-env-envvar"
    When `api.spawn_test_environment` is called with `docker_environment_variable=("ABC=123", "DEF=456")`
    Then running `env` inside the database container shows both ABC=123 and DEF=456

  Scenario: Spawn environment with additional database parameters
    Given an environment name "test-env-params"
    When `api.spawn_test_environment` is called with `additional_db_parameter=("-disableIndexIteratorScan=1",)`
    Then `dwad_client print-params DB1` inside the database container reports that parameter in the Parameters line

  Scenario: Docker is available in the test container
    Given an environment spawned with a test container
    When `docker ps` is executed inside the test container
    Then the exit code is 0

  Scenario: Default memory and disk size are applied
    Given an environment spawned without explicit mem/disk sizes
    Then EXAConf inside the database container shows "MemSize = 2 GiB"
    And EXAConf shows " Size = 2 GiB"


Feature: Spawn Test Environment — Parameter Validation

  Scenario: Reject disk size below the minimum of 100 MiB
    Given an environment name "test-invalid-disk"
    When `api.spawn_test_environment` is called with `db_disk_size="90 MiB"`
    Then an ArgumentConstraintError is raised immediately before any Docker interaction
    And the error message references the parameter "db_disk_size"
    And the error message states the minimum is 100 MiB

  Scenario: Accept the minimum valid disk size of 100 MiB
    Given an environment name "test-min-disk"
    When `api.spawn_test_environment` is called with `db_disk_size="100 MiB"`
    Then the environment starts successfully
    And EXAConf inside the database container shows " Size = 100 MiB"

  Scenario: Reject memory size below the minimum of 1 GiB
    Given an environment name "test-invalid-mem"
    When `api.spawn_test_environment` is called with `db_mem_size="999 MiB"`
    Then an ArgumentConstraintError is raised immediately before any Docker interaction
    And the error message references the parameter "db_mem_size"

  Scenario: Reject an unsupported accelerator value
    Given an environment name "test-bad-accel"
    When `api.spawn_test_environment` is called with `accelerator=("unsupported_value",)`
    Then an ArgumentConstraintError is raised
    And the error message states that only "nvidia=all" is supported

  Scenario: Reject an invalid Docker runtime
    Given an environment name "test-bad-runtime"
    When `api.spawn_test_environment` is called with `docker_runtime="AAAABBBBCCCC_INVALID_RUNTIME"`
    Then a TaskRuntimeError is raised during environment setup
    And no database container is left running with that environment name

  Scenario: CLI rejects spawn without environment name
    When the user runs `itde spawn-test-environment` with no arguments
    Then the CLI exits with a non-zero exit code
    And the output contains "Missing option '--environment-name'"

  Scenario: CLI displays error on invalid disk size argument
    When the user runs `itde spawn-test-environment` with an invalid `--db-disk-size` value
    Then the CLI exits with exit code 1
    And the output contains the `--db-disk-size` argument name and the constraint message
