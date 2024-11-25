import shutil

import luigi

from exasol_integration_test_docker_environment.lib.api.common import generate_root_task
from exasol_integration_test_docker_environment.lib.docker.images.clean.clean_images import (
    CleanImagesStartingWith,
)


def clean(docker_repository_name):
    task = generate_root_task(
        task_class=CleanImagesStartingWith, starts_with_pattern=docker_repository_name
    )
    luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
    if task._get_tmp_path_for_job().exists():
        shutil.rmtree(str(task._get_tmp_path_for_job()))
