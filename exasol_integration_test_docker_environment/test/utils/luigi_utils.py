import shutil
from datetime import datetime

import luigi

from exasol_integration_test_docker_environment.lib.docker.images.clean.clean_images import CleanImagesStartingWith


def set_job_id(task_cls):
    strftime = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    job_id = f"{strftime}_{task_cls.__name__}"
    config = luigi.configuration.get_config()
    config.set('job_config', 'job_id', job_id)
    return job_id


def clean(docker_repository_name):
    jobid = set_job_id(CleanImagesStartingWith)
    task = CleanImagesStartingWith(starts_with_pattern=docker_repository_name, jobid=jobid)
    luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
    if task._get_tmp_path_for_job().exists():
        shutil.rmtree(str(task._get_tmp_path_for_job()))
