from inspect import cleandoc

import pyexasol


def test_gpu(cli_database):

    query_accelerator_parameters = cleandoc(
        f"""
            SELECT PARAM_VALUE FROM EXA_METADATA 
            WHERE PARAM_NAME LIKE '%accelerator%' 
            ORDER BY PARAM_NAME;
            """
    )
    additional_param = [
        "--docker-runtime",
        "nvidia",
        "--docker-environment-variable",
        "NVIDIA_VISIBLE_DEVICES=all",
        "--additional-db-parameter",
        "-enableAcceleratorDeviceDetection=1",
    ]
    with cli_database(name="test_gpu", additional_parameters=additional_param) as db:
        host_name = db.on_host_docker_environment.database_host
        port = db.on_host_docker_environment.ports.database
        dsn = f"{host_name}:{port}"
        connection = pyexasol.connect(dsn=dsn, user="sys", password="exasol")
        result = connection.execute(query_accelerator_parameters).fetchall()
        assert result == [("0",), ("0",)]
