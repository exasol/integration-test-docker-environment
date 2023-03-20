import click


@click.group()
def cli():
    """
    ITDE - Itegration Test Docker Environemnt

    Create and control a docker based exasol database test setup.

    Examples:

        Check the health of the execution environment:

            $ itde health

        Spwan a itde test environment:

            $ itde spawn-test-environment --environment-name test \\
            --database-port-forward 8888 --bucketfs-port-forward 6666 \\
            --docker-db-image-version 7.1.9 --db-mem-size 4GB

    """
    pass
