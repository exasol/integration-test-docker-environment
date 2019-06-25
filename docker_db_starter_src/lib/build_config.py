import luigi


class build_config(luigi.Config):
    temporary_base_directory = luigi.OptionalParameter(None)
    output_directory = luigi.Parameter(".build_output")
    log_build_context_content = luigi.BoolParameter(False)
