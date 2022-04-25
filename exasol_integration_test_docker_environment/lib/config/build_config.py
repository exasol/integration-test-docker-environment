import luigi

DEFAULT_OUTPUT_DIRECTORY = ".build_output"

class build_config(luigi.Config):
    force_pull = luigi.BoolParameter(False)
    force_load = luigi.BoolParameter(False)
    force_rebuild = luigi.BoolParameter(False)
    force_rebuild_from = luigi.ListParameter([])
    log_build_context_content = luigi.BoolParameter(False)
    # keep_build_context = luigi.BoolParameter(False)
    temporary_base_directory = luigi.OptionalParameter(None)
    output_directory = luigi.Parameter(DEFAULT_OUTPUT_DIRECTORY)
    cache_directory = luigi.OptionalParameter("")
    build_name = luigi.OptionalParameter("")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def configuration_finished(cls):
        cls._ready = True

    @classmethod
    def is_configured(cls):
        if hasattr(cls, "_ready"):
            return cls._ready
        return False

    def validate_new_parameters(self, new_output_directory):
        if self.__class__.is_configured():
            # If build config is set multiple times, we must ensure the output_directory does not change
            # The logging always will print to logfile in the first configured output directory (restriction by Luigi).
            if new_output_directory is None:
                new_output_directory = DEFAULT_OUTPUT_DIRECTORY
            if new_output_directory != self.output_directory:
                raise ValueError("Output directory has been changed, "
                                 "but it's not allowed to change between invocations of calls.")

