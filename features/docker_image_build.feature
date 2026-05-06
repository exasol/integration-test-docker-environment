Feature: Docker Image Build (DockerBuildBase / DockerCreateImageTask)

  Background:
    Given a DockerBuildBase subclass that defines a set of build goals

  Scenario: Requesting an unknown goal raises an error during task initialization
    Given a DockerBuildBase task configured with goal "nonexistent_stage"
    When the task object is constructed (register_required is called)
    Then an exception is raised containing "Unknown goal(s)"
    And no Docker commands are issued

  Scenario: A goal with state NEEDS_TO_BE_BUILD triggers a DockerBuildImageTask
    Given an analyze task that returns ImageInfo with state NEEDS_TO_BE_BUILD
    When create_build_tasks is called
    Then a DockerBuildImageTask is created for that image
    And the image is built via the Docker API

  Scenario: A goal with state TARGET_LOCALLY_AVAILABLE skips the build
    Given an analyze task that returns ImageInfo with state TARGET_LOCALLY_AVAILABLE
    When create_build_tasks is called
    Then no DockerBuildImageTask is created for that image
    And the returned ImageInfo.image_state is USED_LOCAL

  Scenario: A goal with state SOURCE_LOCALLY_AVAILABLE triggers a tag operation
    Given an analyze task that returns ImageInfo with state SOURCE_LOCALLY_AVAILABLE
    When create_build_tasks is called
    Then a DockerTagTask is created (tagging source as target)
    And the returned ImageInfo.image_state is WAS_TAGED

  Scenario: A goal with state CAN_BE_LOADED triggers a DockerLoadImageTask
    Given an analyze task that returns ImageInfo with state CAN_BE_LOADED
    When create_build_tasks is called
    Then a DockerLoadImageTask is created to load the image from cache
    And the returned ImageInfo.image_state is WAS_LOADED

  Scenario: A goal with state REMOTE_AVAILABLE triggers a DockerPullImageTask
    Given an analyze task that returns ImageInfo with state REMOTE_AVAILABLE
    When create_build_tasks is called
    Then a DockerPullImageTask is created to pull the image from the registry
    And the returned ImageInfo.image_state is WAS_PULLED

  Scenario: force_rebuild_from causes the specified stage and all dependents to rebuild
    Given a two-stage build where stage B depends on stage A
    And build_config().force_rebuild_from is set to ["stage_a"]
    When the analyze tasks run
    Then stage A's image_state is NEEDS_TO_BE_BUILD
    And stage B's image_state is NEEDS_TO_BE_BUILD

  Scenario: Specifying an invalid stage in force_rebuild_from raises an error
    Given build_config().force_rebuild_from contains a stage name not in get_goals()
    When the DockerBuildBase task is constructed
    Then an exception is raised listing the invalid stage name

  Scenario: Image tag encodes the build context hash
    Given a DockerAnalyzeImageTask whose context hash is computed
    When the target image tag is generated
    Then the tag string includes the first 8 characters of the SHA-256 hash of the build context
