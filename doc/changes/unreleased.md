# Integration-Test-Docker-Environment X.Y.Z, released YYYY-MM-DD

## Summary

Added pytest plugin and fixed itde cli command

### Supported Exasol Versions

* **7.0**: up to 7.0.20, **except 7.0.5**
* **7.1**: up to 7.1.17

If you need further versions, please open an issue.

## Feature
- Added pytest plugin and fixtures

    - Show settings related to itde plugin

        ```shell
        pytest --help | grep "itde\|exasol\|bucketfs"
        ```
    - Show fixtures related to itde

        ```shell
        pytest --fixtures | grep pytest_itde -A 3
        ```
    
    - Use itde to setup a test db etc. for a test

      ```python
      # In order to use itde, just request it as fixture
      # ATTENTION: initial startup may be up to ~1-2 minutes
      # (Somtimes even longer if images must be fetched for the first time)
      def test_smoke_test_plugin(itde):
          db = itde.exasol_config,
          bucketfs = itde.bucketfs_config,
          itde_cfg = itde.itde_config,
          ctrl_connection = itde.connection,
          assert True
      ```

## Changes
- Fixed `itde` cli command and subcommands
  - Provide all available subcommands in help
  - Provide examples and basic doc string for commands
  - Fix subcommand imports
  - Example Usage:

      ```shell
        $ itde spawn-test-environment --environment-name test \\
        --database-port-forward 8888 --bucketfs-port-forward 6666 \\
        --docker-db-image-version 7.1.9 --db-mem-size 4GB
      ```

## Internal
- Updated dependencies
