import click


@click.group()
def cli():
    """
    ITDE - Integration Test Docker Environment

    Create and control a docker based exasol database test setup.

    Examples:

        Check the health of the execution environment:

            $ itde health

        Spawn an ITDE test environment:

            $ itde spawn-test-environment --environment-name test \\
            --database-port-forward 8563 --bucketfs-port-forward 2580 \\
            --docker-db-image-version 7.1.9 --db-mem-size 4GB
    """
    pass
