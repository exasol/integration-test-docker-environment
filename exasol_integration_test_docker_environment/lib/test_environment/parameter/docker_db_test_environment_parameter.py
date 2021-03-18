import luigi
from luigi import Config


class DockerDBTestEnvironmentParameter(Config):
    docker_db_image_name = luigi.OptionalParameter(None)
    docker_db_image_version = luigi.OptionalParameter(None)
    reuse_database = luigi.BoolParameter(False, significant=False)
    no_database_cleanup_after_success = luigi.BoolParameter(False, significant=False)
    no_database_cleanup_after_failure = luigi.BoolParameter(False, significant=False)
    database_port_forward = luigi.OptionalParameter(None, significant=False)
    bucketfs_port_forward = luigi.OptionalParameter(None, significant=False)
    mem_size = luigi.OptionalParameter("2 GiB",significant=False)
    disk_size = luigi.OptionalParameter("2 GiB",significant=False)
    nameservers = luigi.ListParameter([],significant=False)
