from click._unicodefun import click

output_directory = click.option('--output-directory', type=click.Path(file_okay=False, dir_okay=True),
                                default=".build_output",
                                show_default=True,
                                help="Output directory where the system stores all output and log files.")

tempory_base_directory = click.option('--temporary-base-directory',
                                      type=click.Path(file_okay=False,
                                                      dir_okay=True),
                                      default="/tmp",
                                      show_default=True,
                                      help="Directory where the system creates temporary directories.")

system_options = [
    click.option('--workers', type=int,
                 default=5, show_default=True,
                 help="Number of parallel workers"),
]