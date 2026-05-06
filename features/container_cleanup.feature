Feature: Container Cleanup

  Scenario: Explicit cleanup removes all environment resources
    Given a test environment named "cleanup-env" was spawned and returned a cleanup function
    When the returned cleanup function is invoked
    Then the database container "db_container_cleanup-env" is stopped and removed
    And the test container "test_container_cleanup-env" is stopped and removed
    And the Docker network for "cleanup-env" is removed
    And any Docker volume associated with the database container is removed

  Scenario: Spawned environment containers persist until cleanup is called
    Given a test environment named "persist-env" was spawned
    When the cleanup function has not been called
    Then both containers and the network remain visible in the Docker daemon
