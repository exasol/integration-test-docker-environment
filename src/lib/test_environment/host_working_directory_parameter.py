import luigi
from luigi import Config


class HostWorkingDirectoryParameter():

    host_working_directory = luigi.OptionalParameter(None, significant=False)
