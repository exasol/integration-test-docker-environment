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
