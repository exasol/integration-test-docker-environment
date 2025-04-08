from typing import Optional

import luigi
from luigi import Config
from luigi.parameter import ParameterVisibility


class ExternalDatabaseXMLRPCParameter(Config):
    external_exasol_xmlrpc_host: Optional[str] = luigi.OptionalParameter()
    external_exasol_xmlrpc_port: int = luigi.IntParameter(default=443)
    external_exasol_xmlrpc_user: Optional[str] = luigi.OptionalParameter()
    external_exasol_xmlrpc_cluster_name: Optional[str] = luigi.OptionalParameter()
    external_exasol_xmlrpc_password: Optional[str] = luigi.OptionalParameter(
        significant=False,
        visibility=ParameterVisibility.HIDDEN,
    )


# See ticket https://github.com/exasol/integration-test-docker-environment/issues/341
class ExternalDatabaseHostParameter(Config):
    external_exasol_db_host: Optional[str] = luigi.OptionalParameter()
    external_exasol_db_port: int = luigi.IntParameter()
    external_exasol_bucketfs_port: int = luigi.IntParameter()
    external_exasol_ssh_port: int = luigi.IntParameter()


class ExternalDatabaseCredentialsParameter(
    ExternalDatabaseHostParameter,
    ExternalDatabaseXMLRPCParameter,
):
    external_exasol_db_user: Optional[str] = luigi.OptionalParameter()
    external_exasol_db_password: Optional[str] = luigi.OptionalParameter(
        significant=False,
        visibility=ParameterVisibility.HIDDEN,
    )
    external_exasol_bucketfs_write_password: Optional[str] = luigi.OptionalParameter(
        significant=False,
        visibility=ParameterVisibility.HIDDEN,
    )
