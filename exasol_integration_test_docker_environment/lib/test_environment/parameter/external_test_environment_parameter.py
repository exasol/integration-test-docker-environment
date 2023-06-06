import luigi
from luigi import Config

from luigi.parameter import ParameterVisibility


class ExternalDatabaseXMLRPCParameter(Config):
    external_exasol_xmlrpc_host = luigi.OptionalParameter()
    external_exasol_xmlrpc_port = luigi.IntParameter(443)
    external_exasol_xmlrpc_user = luigi.OptionalParameter()
    external_exasol_xmlrpc_cluster_name = luigi.OptionalParameter()
    external_exasol_xmlrpc_password = luigi.OptionalParameter(significant=False,
                                                              visibility=ParameterVisibility.HIDDEN)


# should or can we use lib.test_environment.ports.PortForwarding.default_ports here?
class ExternalDatabaseHostParameter(Config):
    external_exasol_db_host = luigi.OptionalParameter()
    external_exasol_db_port = luigi.IntParameter(8563)
    external_exasol_bucketfs_port = luigi.IntParameter(6583)
    external_exasol_ssh_port = luigi.IntParameter(22) # TBC: is this correct?


class ExternalDatabaseCredentialsParameter(ExternalDatabaseHostParameter,
                                           ExternalDatabaseXMLRPCParameter):
    external_exasol_db_user = luigi.OptionalParameter()
    external_exasol_db_password = luigi.OptionalParameter(significant=False,
                                                          visibility=ParameterVisibility.HIDDEN)
    external_exasol_bucketfs_write_password = luigi.OptionalParameter(significant=False,
                                                                      visibility=ParameterVisibility.HIDDEN)
