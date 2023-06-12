import luigi
from luigi import Config

from luigi.parameter import ParameterVisibility


class ExternalDatabaseXMLRPCParameter(Config):
    external_exasol_xmlrpc_host = luigi.OptionalParameter()
    external_exasol_xmlrpc_port = luigi.IntParameter(443)
    external_exasol_xmlrpc_user = luigi.OptionalParameter()
    external_exasol_xmlrpc_cluster_name = luigi.OptionalParameter()
    external_exasol_xmlrpc_password = luigi.OptionalParameter(
        significant=False,
        visibility=ParameterVisibility.HIDDEN,
    )


# See ticket https://github.com/exasol/integration-test-docker-environment/issues/341
class ExternalDatabaseHostParameter(Config):
    external_exasol_db_host = luigi.OptionalParameter()
    external_exasol_db_port = luigi.IntParameter()
    external_exasol_bucketfs_port = luigi.IntParameter()
    external_exasol_ssh_port = luigi.IntParameter()


class ExternalDatabaseCredentialsParameter(
        ExternalDatabaseHostParameter,
        ExternalDatabaseXMLRPCParameter,
):
    external_exasol_db_user = luigi.OptionalParameter()
    external_exasol_db_password = luigi.OptionalParameter(
        significant=False,
        visibility=ParameterVisibility.HIDDEN,
    )
    external_exasol_bucketfs_write_password = luigi.OptionalParameter(
        significant=False,
        visibility=ParameterVisibility.HIDDEN,
    )
