import os
import ssl
from inspect import cleandoc
from time import sleep

import pyexasol
import pytest

from exasol_integration_test_docker_environment.lib.test_environment.db_version import (
    DbVersion,
)


def test_udf_execution(api_context):
    if "EXASOL_VERSION" in os.environ and os.environ["EXASOL_VERSION"].startswith("7"):
        pytest.skip("Test is unstable with Exasol 7.x on newer Linux Kernel")

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

    with api_context() as db:
        dbinfo = db.environment_info.database_info
        dsn = f"{dbinfo.host}:{dbinfo.ports.database}"
        connection = pyexasol.connect(dsn=dsn, user="sys", password="exasol", websocket_sslopt={"cert_reqs": ssl.CERT_NONE})
        if DbVersion.from_db_version_str(db.docker_db_image_version).major == 7:
            wait_until_container_is_unpacked()
        connection.execute("CREATE SCHEMA IF NOT EXISTS S")
        connection.execute(udf_sql(schema="S"))
        result = connection.execute("SELECT S.python3_test_udf(10)").fetchall()
        assert result == [(i,) for i in range(10)]
