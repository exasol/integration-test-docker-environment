Feature: Test Container Build and Push

  Scenario: Build a test container from a Dockerfile
    Given a valid TestContainerContentDescription referencing a Dockerfile
    When `api.build_test_container(test_container_content=...)` is called
    Then the Docker image is built and tagged in the local Docker daemon
    And the returned ImageInfo.image_state equals "WAS_BUILD"
    And the image tag matches ImageInfo.get_target_complete_name()

  Scenario: Second build with unchanged Dockerfile uses the local cache
    Given the test container was already built once from an unchanged Dockerfile
    When `api.build_test_container` is called again with the same content
    Then no rebuild is performed
    And the returned ImageInfo.image_state equals "USED_LOCAL"

  Scenario: Force rebuild ignores the local cache
    Given the test container was already built once
    When `api.build_test_container` is called with `force_rebuild=True`
    Then the image is rebuilt unconditionally
    And the returned ImageInfo.image_state equals "WAS_BUILD"

  Scenario: Push test container to a Docker registry
    Given a local Docker registry is running
    And the test container has been built or is buildable from the Dockerfile
    When `api.push_test_container` is called with the registry as the target repository
    Then the registry contains exactly one tag for the test container image
    And the pushed tag matches ImageInfo.get_target_complete_tag()
