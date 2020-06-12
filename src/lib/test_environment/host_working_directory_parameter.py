import luigi
from luigi import Config


class HostWorkingDirectoryParameter(Config):

    host_working_directory = luigi.OptionalParameter(None, significant=False)
