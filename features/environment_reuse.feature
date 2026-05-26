Feature: Environment Reuse

  Scenario: Reuse existing containers when name and configuration are unchanged
    Given a test environment named "reuse-env" was previously spawned with `no_cleanup=True`
    And the environment's test container, database container, and Docker network all exist with recorded IDs
    When `spawn_test_environment` is called again with the same environment name and configuration
    Then the returned EnvironmentInfo references the same container IDs as before
    And no new containers are created

  Scenario: Spawn fresh containers when the test container Dockerfile is modified
    Given a test environment named "reuse-env-changed" was previously spawned with `no_cleanup=True`
    And the Dockerfile used for the test container is modified (even by appending a comment)
    When `spawn_test_environment` is called again for "reuse-env-changed"
    Then a new container image is built
    And the new container ID and image ID differ from those of the previous run
