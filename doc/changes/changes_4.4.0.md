# 4.4.0 - 2025-11-11

This release adds support for docker-db version 2025.1.3, 2025.1.1 and 8.29.6. Also, it enables configuration for HTTPS on BucketFS and adds a new option for accelerator configuration.
Besides, it includes several internal improvements.


## Refactorings
 - #522: Converted integration API test to pytest - test_docker_registry_image_checker.py
 - #522: Converted integration API test to pytest - test_docker_build_base.py
 - #522: Converted integration API test to pytest - test_docker_access_method.py
 - #522: Converted integration API test to pytest - test_doctor.py
 - #522: Converted integration API test to pytest - test_environment_variable.py
 - #522: Converted integration API test to pytest - test_find_free_port.py
 - #522: Converted integration API test to pytest - test_generate_graph_plot.py
 - #534: Converted integration API test to pytest - test_hash_temp_dir.py
 - #534: Converted integration API test to pytest - test_hash_temp_dir_with_files.py
 - #534: Converted integration API test to pytest - test_test_env_reuse.py
 - #534: Converted integration API test to pytest - test_populate_data.py
 - #534: Converted integration API test to pytest - test_hash_symlink_loops.py
 - #534: Converted integration API test to pytest - test_termination_handler.py
 - #534: Converted integration API test to pytest - test_test_container_reuse.py

## features
 - #531: Added docker-db 2025-1-3
 - #531: Added docker-db 2025-1-1
 - #531: Added docker-db 8-29-12
 - #545: Added GPU Option
 - #550: Added support for bucket fs https port

## Dependencies
 - #532: Updated pyexasol and update lock file

## Dependency Updates

### `main`
* Updated dependency `click:8.2.1` to `8.3.0`
* Updated dependency `requests:2.32.4` to `2.32.5`
* Updated dependency `simplejson:3.20.1` to `3.20.2`

### `dev`
* Added dependency `dill:0.4.0`
* Added dependency `exasol-bucketfs:2.1.0`
* Updated dependency `exasol-toolbox:1.7.1` to `1.10.0`
* Updated dependency `joblib:1.5.1` to `1.5.2`
* Updated dependency `mypy:1.17.0` to `1.18.2`
* Updated dependency `pyexasol:0.25.2` to `1.2.0`
* Added dependency `pyinstaller:6.16.0`
* Added dependency `types-pyinstaller:6.16.0.20250918`
