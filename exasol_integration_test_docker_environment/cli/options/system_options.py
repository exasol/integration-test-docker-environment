import click

DEFAULT_OUTPUT_DIRECTORY = ".build_output"

output_directory_option = click.option(
    "--output-directory",
    type=click.Path(file_okay=False, dir_okay=True),
    default=DEFAULT_OUTPUT_DIRECTORY,
    show_default=True,
    help="Output directory where the system stores all output and log files.",
)

tempory_base_directory_option = click.option(
    "--temporary-base-directory",
    type=click.Path(file_okay=False, dir_okay=True),
    default="/tmp",
    show_default=True,
    help="Directory where the system creates temporary directories.",
)

system_options = [
    click.option(
        "--workers",
        type=int,
        default=5,
        show_default=True,
        help="Number of parallel workers",
    ),
    click.option(
        "--task-dependencies-dot-file",
        type=click.Path(file_okay=True),
        default=None,
        help="Path where to store the Task Dependency Graph as dot file",
    ),
]

luigi_logging_options = [
    click.option(
        "--log-level",
        type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "FATAL"]),
        default=None,
        help="Log level used for console logging",
    ),
    click.option(
        "--use-job-specific-log-file",
        type=bool,
        default=True,
        help="Use a job specific log file which write the debug log "
        "to the job directory in the build directory",
    ),
]
