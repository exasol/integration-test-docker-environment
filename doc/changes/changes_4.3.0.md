# 4.3.0 - 2025-08-27

Support for Exasol docker db 2025.1.0 and internal improvements.

## Features

 - #497: Added Docker-DB 2025.1.0
 - #449: Added nox taks to build standalone executable

## Refactorings

 - Updated `exasol-toolbox` to 1.6.0 and fixed broken links
 - #501: Converted integration API test to pytest - part III
   - test_cli_test_environment_additional_params
   - test_cli_test_environment_db_disk_size
   - test_cli_test_environment_nameservers
   - test_cli_test_environment_db_mem_size
   - test_common_run_task
   - test_db_version_supports_custom_certificates
   - test_click_api_consistency
 - #506: Updated formatting
 - #515: Update GPU Test Query

 ## Security

 - Updated lock file

## Internal

 - Updated GH workflows from tbx 1.6.0 to 1.7.1

## Dependency Updates

### `main`
* Updated dependency `gitpython:3.1.44` to `3.1.45`

### `dev`
* Updated dependency `exasol-toolbox:1.5.0` to `1.7.1`
* Updated dependency `mypy:1.16.1` to `1.17.0`
* Added dependency `pytest-check:2.5.3`
