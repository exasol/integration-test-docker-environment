Feature: Docker Runtime Selection

  Scenario: Both containers use the Docker daemon default runtime when none is specified
    Given no `docker_runtime` parameter is passed to `spawn_test_environment`
    When the environment is spawned
    Then both the database container and the test container use the daemon's default runtime

  Scenario: Both containers use a specified Docker runtime
    Given a valid Docker runtime name is known on the host
    When `api.spawn_test_environment` is called with that runtime name as `docker_runtime`
    Then both the database container and the test container report that runtime in their HostConfig
