Feature: CLI and API Consistency

  Scenario: Every CLI command has a matching API function with identical parameter names
    Given the `itde` CLI commands and the Python API functions
    When their argument lists are compared
    Then the parameter names, order, and type annotations match exactly for each paired command/function

  Scenario: Default values are identical between CLI and API
    Given the `itde` CLI commands and the Python API functions
    When the default values of all optional parameters are compared
    Then the defaults match for every parameter in every command/function pair
    And the known exception is `use_job_specific_log_file` which has a documented divergence

  Scenario: The `environment` command reports correct defaults
    When the user runs `itde environment --show-default-db-version`
    Then the output contains the current latest DB version string "2025.1.8"
    When the user runs `itde environment --show-default-mem-size`
    Then the output contains "2 GiB"
    When the user runs `itde environment --show-default-disk-size`
    Then the output contains "2 GiB"

  Scenario: Deprecated `bucketfs_port_forward` parameter triggers a warning
    When `api.spawn_test_environment` is called with the deprecated `bucketfs_port_forward` parameter
    Then a DeprecationWarning is emitted recommending `bucketfs_http_port_forward` instead
    And the parameter value is internally forwarded to both the HTTP and legacy BucketFS port fields
