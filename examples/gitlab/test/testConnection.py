import pyexasol
import os

 

host_ip=os.environ["ENVIRONMENT_DATABASE_HOST"]
print("host ip:",host_ip)
port=os.environ["ENVIRONMENT_DATABASE_DB_PORT"]
print("port:",port)

 

C = pyexasol.connect(dsn=f'{host_ip}:{port}', user='sys', password='exasol', compression=True)

 

df = C.export_to_pandas("SELECT * FROM EXA_ALL_USERS")
print(df.head())