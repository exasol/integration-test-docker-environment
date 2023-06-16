import pyexasol


def test_udf_execution(api_database):
    with api_database() as db:
        dbinfo = db.environment_info.database_info
        dsn = f"{dbinfo.host}:{dbinfo.db_port}"
        connection = pyexasol.connect(dsn=dsn, user="sys", password="exasol")
        result = connection.execute("select 1 from dual")
        result = next(result)[0]
        assert result == 1
