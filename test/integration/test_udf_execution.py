import pyexasol

from inspect import cleandoc
from time import sleep

def test_udf_execution(api_database):
    def wait_until_container_is_unpacked():
        sleep(5*60)

    def udf_sql(schema: str) -> str:
        return cleandoc(
            f"""
            --/
            CREATE OR REPLACE PYTHON3 SCALAR SCRIPT
              {schema}.bucketfs_ls(my_path VARCHAR(256))
              EMITS (files VARCHAR(256)) AS
            import os

            def run(ctx):
                    for line in os.listdir(ctx.my_path):
                            ctx.emit(line)
            /
            """
        )
    with api_database() as db:
        dbinfo = db.environment_info.database_info
        dsn = f"{dbinfo.host}:{dbinfo.db_port}"
        connection = pyexasol.connect(dsn=dsn, user="sys", password="exasol")
        wait_until_container_is_unpacked()
        connection.execute("CREATE SCHEMA IF NOT EXISTS S")
        connection.execute(udf_sql(schema="S"))
        result = connection.execute("SELECT S.bucketfs_ls('/buckets/bfsdefault/default')")
        result = next(result)[0]
        assert result == "EXAClusterOS"
