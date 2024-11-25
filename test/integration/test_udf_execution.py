from inspect import cleandoc
from time import sleep

import pyexasol

from exasol_integration_test_docker_environment.lib.test_environment.db_version import (
    DbVersion,
)


def test_udf_execution(api_database):
    def wait_until_container_is_unpacked():
        sleep(5 * 60)

    def udf_sql(schema: str) -> str:
        return cleandoc(
            f"""
            --/
            CREATE OR REPLACE PYTHON3 SCALAR SCRIPT
              {schema}.python3_test_udf(count INT)
              EMITS (outp INT) AS
            import os

            def run(ctx):
                for i in range(ctx.count):
                    ctx.emit(i)
            /
            """
        )

    with api_database() as db:
        dbinfo = db.environment_info.database_info
        dsn = f"{dbinfo.host}:{dbinfo.ports.database}"
        connection = pyexasol.connect(dsn=dsn, user="sys", password="exasol")
        if DbVersion.from_db_version_str(db.docker_db_image_version).major == 7:
            wait_until_container_is_unpacked()
        connection.execute("CREATE SCHEMA IF NOT EXISTS S")
        connection.execute(udf_sql(schema="S"))
        result = connection.execute("SELECT S.python3_test_udf(10)").fetchall()
        assert result == [(i,) for i in range(10)]
