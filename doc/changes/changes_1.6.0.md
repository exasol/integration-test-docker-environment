# Integration-Test-Docker-Environment 1.6.0, released 2023-05-12

## Summary

This release fixes several bugs regarding logging, reusing of an environment and rebuilding the test container.

### Supported Exasol Versions

* **7.0**: up to 7.0.20, **except 7.0.5**
* **7.1**: up to 7.1.17

If you need further versions, please open an issue.

## Internal

* #297: Update release_config.yml
* #311: Add vagrant setup

## Changes

* #294: Fixed that the client logging config gets overwritten
* #295: Fixed that the test_container_content parameter pollutes the logs
* #300: Fixed BucketFS uploads during reusing of an environment
* #241: Renamed test environment variable GOOGLE_CLOUD_BUILD to RUN_SLC_TESTS_WITHIN_CONTAINER
* #310: Fixed that using run_task with log_level duplicates log entries
* #291: Fixed that test container gets rebuild when force_rebuild is true
* #316: Removed setup.py and updated poetry (1.4.0) in actions
