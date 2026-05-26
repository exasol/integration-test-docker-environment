Feature: Health Check

  Background:
    Given the `itde` CLI or Python API is installed and available

  Scenario: Healthy environment exits successfully
    Given a Docker daemon is reachable via the configured socket
    And the current platform is Linux or macOS (Intel)
    When the user runs `itde health` or calls `api.health()`
    Then the command exits with code 0
    And no output or error message is produced

  Scenario: Docker daemon unavailable via missing Unix socket
    Given the DOCKER_HOST environment variable points to a non-existent Unix socket path
    When the user runs `itde health` or calls `api.health()`
    Then the exit code is -1 (CLI) or a HealthProblem exception is raised (API)
    And the output contains error code "E-ITDE-1"
    And the output includes a suggestion to verify the DOCKER_HOST environment variable

  Scenario: Running on an unsupported platform
    Given the host operating system is neither Linux nor macOS
    When the user runs `itde health` or calls `api.health()`
    Then the exit code is -1 (CLI) or a HealthProblem exception is raised (API)
    And the output contains error code "E-ITDE-2"
    And the output includes a list of supported platforms

  Scenario: Multiple problems are all reported
    Given the Docker socket is missing
    And the host platform is unsupported
    When the user runs `itde health`
    Then the output states "2 problem(s) have been identified"
    And both E-ITDE-1 and E-ITDE-2 appear in the output
