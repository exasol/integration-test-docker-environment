Feature: Docker Image Analysis (DockerAnalyzeImageTask)

  Background:
    Given a DockerAnalyzeImageTask subclass with a valid Dockerfile and build context

  Scenario: Image state is TARGET_LOCALLY_AVAILABLE when the target image already exists locally
    Given the target image tag is present in the local Docker daemon
    And neither force_pull nor force_load is set
    And no rebuild is requested
    When the analyze task runs
    Then the returned ImageInfo.image_state is TARGET_LOCALLY_AVAILABLE

  Scenario: Image state is NEEDS_TO_BE_BUILD when the target image is absent
    Given the target image tag is not present locally or in any registry
    When the analyze task runs
    Then the returned ImageInfo.image_state is NEEDS_TO_BE_BUILD

  Scenario: Image state is NEEDS_TO_BE_BUILD when rebuild is explicitly requested
    Given the target image already exists locally
    And is_rebuild_requested returns True
    When the analyze task runs
    Then the returned ImageInfo.image_state is NEEDS_TO_BE_BUILD

  Scenario: Image state is SOURCE_LOCALLY_AVAILABLE when only the source tag is present
    Given the target image tag is absent
    And the source image tag is present in the local Docker daemon
    When the analyze task runs
    Then the returned ImageInfo.image_state is SOURCE_LOCALLY_AVAILABLE

  Scenario: Build context hash includes Dockerfile content, build files, and image-changing build arguments
    Given two analyze tasks with identical configuration except for one image-changing build argument
    When both tasks compute their image hash
    Then the hashes are different

  Scenario: Transparent build arguments do not affect the image hash
    Given two analyze tasks identical except for a transparent build argument (e.g. a mirror URL)
    When both tasks compute their image hash
    Then the hashes are equal

  Scenario: A dependency image hash change causes the dependent image to be rebuilt
    Given image B depends on image A
    And image A's Dockerfile has been modified (changing its hash)
    When the analyze task for image B runs
    Then image B's image_state is NEEDS_TO_BE_BUILD
