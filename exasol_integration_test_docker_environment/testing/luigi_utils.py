import shutil

from exasol_integration_test_docker_environment.lib.base import ray_runner
from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)
from exasol_integration_test_docker_environment.lib.docker.images.clean.clean_images import (
    CleanImagesStartingWith,
)


def clean(docker_repository_name):
    task = generate_root_task(
        task_class=CleanImagesStartingWith, starts_with_pattern=docker_repository_name
    )
    ray_runner.build([task], workers=1)
    if task._get_tmp_path_for_job().exists():
        shutil.rmtree(str(task._get_tmp_path_for_job()))
