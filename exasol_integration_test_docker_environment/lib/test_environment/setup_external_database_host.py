import ssl
from time import sleep
from urllib.parse import quote_plus
from xmlrpc.client import ServerProxy

import luigi

from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import (
    DependencyLoggerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import (
    JsonPickleParameter,
)
from exasol_integration_test_docker_environment.lib.data.database_credentials import (
    DatabaseCredentialsParameter,
)
from exasol_integration_test_docker_environment.lib.data.database_info import (
    DatabaseInfo,
)
from exasol_integration_test_docker_environment.lib.data.docker_network_info import (
    DockerNetworkInfo,
)
from exasol_integration_test_docker_environment.lib.test_environment.parameter.external_test_environment_parameter import (
    ExternalDatabaseHostParameter,
    ExternalDatabaseXMLRPCParameter,
)
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports


class SetupExternalDatabaseHost(
    DependencyLoggerBaseTask,
    ExternalDatabaseXMLRPCParameter,
    ExternalDatabaseHostParameter,
    DatabaseCredentialsParameter,
):
    environment_name: str = luigi.Parameter()  # type: ignore
    network_info: DockerNetworkInfo = JsonPickleParameter(DockerNetworkInfo, significant=False)  # type: ignore
    attempt: int = luigi.IntParameter(1)  # type: ignore

    def run_task(self):
        database_host = self.external_exasol_db_host
        if (
            self.external_exasol_db_host == "localhost"
            or self.external_exasol_db_host == "127.0.0.1"
        ):
            database_host = self.network_info.gateway
        self.setup_database()
        ports = Ports(
            database=self.external_exasol_db_port,
            bucketfs=self.external_exasol_bucketfs_port,
            ssh=self.external_exasol_ssh_port,
        )
        database_info = DatabaseInfo(host=database_host, ports=ports, reused=False)
        self.return_object(database_info)

    def setup_database(self):
        if self.external_exasol_xmlrpc_host is not None:
            # TODO add option to use unverified ssl
            cluster = self.get_xml_rpc_object()
            self.start_database(cluster)
            cluster.bfsdefault.editBucketFS(
                {"http_port": int(self.external_exasol_bucketfs_port)}
            )
            try:
                cluster.bfsdefault.addBucket(
                    {
                        "bucket_name": "myudfs",
                        "public_bucket": True,
                        "read_password": self.bucketfs_write_password,
                        "write_password": self.bucketfs_write_password,
                    }
                )
            except Exception as e:
                self.logger.info(e)
            try:
                cluster.bfsdefault.addBucket(
                    {
                        "bucket_name": "jdbc_adapter",
                        "public_bucket": True,
                        "read_password": self.bucketfs_write_password,
                        "write_password": self.bucketfs_write_password,
                    }
                )
            except Exception as e:
                self.logger.info(e)

    def get_xml_rpc_object(self, object_name: str = ""):
        assert self.external_exasol_xmlrpc_user and self.external_exasol_xmlrpc_password
        uri = "https://{user}:{password}@{host}:{port}/{cluster_name}/{object_name}".format(
            user=quote_plus(self.external_exasol_xmlrpc_user),
            password=quote_plus(self.external_exasol_xmlrpc_password),
            host=self.external_exasol_xmlrpc_host,
            port=self.external_exasol_xmlrpc_port,
            cluster_name=self.external_exasol_xmlrpc_cluster_name,
            object_name=object_name,
        )
        server = ServerProxy(uri, context=ssl._create_unverified_context())
        return server

    def start_database(self, cluster: ServerProxy):
        storage = self.get_xml_rpc_object("storage")
        # wait until all nodes are online
        self.logger.info("Waiting until all nodes are online")
        all_nodes_online = False
        while not all_nodes_online:
            all_nodes_online = True
            for nodeName in cluster.getNodeList():  # type: ignore
                node_state = self.get_xml_rpc_object(nodeName).getNodeState()  # type: ignore
                if node_state["status"] != "Running":
                    all_nodes_online = False
                    break
            sleep(5)
        self.logger.info("All nodes are online now")

        # start EXAStorage
        if not storage.serviceIsOnline():
            if storage.startEXAStorage() != "OK":
                self.logger.info("EXAStorage has been started successfully")
            else:
                raise Exception("Not able startup EXAStorage!\n")
        elif storage.serviceIsOnline():
            self.logger.info("EXAStorage already online; continuing startup process")

        # triggering database startup
        for databaseName in cluster.getDatabaseList():  # type: ignore
            database = self.get_xml_rpc_object("/db_" + quote_plus(str(databaseName)))
            if not database.runningDatabase():
                self.logger.info("Starting database instance %s" % str(databaseName))
                database.startDatabase()
            else:
                self.logger.info(
                    "Database instance %s already running" % str(databaseName)
                )
