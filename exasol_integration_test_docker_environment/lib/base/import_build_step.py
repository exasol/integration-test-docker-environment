from pathlib import Path

from exasol_integration_test_docker_environment.lib import (
    extract_modulename_for_build_steps,
)


def import_build_steps(flavor_path: tuple[str, ...]) -> None:
    # TODO Move to script-languages-container-tools: https://github.com/exasol/script-languages-container-tool/issues/268
    # We need to load the build steps of a flavor in the commandline processor,
    # because the imported classes need to be available in all processes spawned by luigi.
    # If we  import the build steps in a Luigi Task they are only available in the worker
    # which executes this task. The build method with local scheduler of luigi uses fork
    # to create the scheduler and worker processes, such that the imported classes available
    # in the scheduler and worker processes
    import importlib.util

    for path in flavor_path:
        path_to_build_steps = Path(path).joinpath("flavor_base/build_steps.py")
        module_name_for_build_steps = extract_modulename_for_build_steps(path)
        spec = importlib.util.spec_from_file_location(
            module_name_for_build_steps, path_to_build_steps
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
