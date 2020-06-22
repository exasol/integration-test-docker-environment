# admin credentials
root 
Start123

# Umgebung anlgegen:

1. netwerk anlegen
Das ist eine Besonderheit für Docker for MacOS hilft aber für alles andere auch.
```shell
docker network create my_gitlab_env
```

2. start Gitlab Server
(sollte das angelegte Netzwerk nutzen)
```shell
docker run --detach  \
     --hostname gitlab  \
     --publish 443:443 \
     --publish 80:80 \
     --publish 22:22   \
     --name gitlab   \
     --restart always   \
     --volume $GITLAB_HOME/gitlab/config:/etc/gitlab   \
     --volume $GITLAB_HOME/gitlab/logs:/var/log/gitlab   \
     --volume $GITLAB_HOME/gitlab/data:/var/opt/gitlab  \
     --network my_gitlab_env \
     gitlab/gitlab-ce:latest
```


3. gitlab runner

    1.  volume anlgeben um Configuration abzulegen
    ```shell
    docker volume create gitlab-runner-config
    ```

    2. runner starten
    ```shell
    docker run -d --name gitlab-runner --restart always \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v gitlab-runner-config:/etc/gitlab-runner \
            --network my_gitlab_env \
            gitlab/gitlab-runner:latest
    ```


    3. einen Runner erzeugen / registrieren
    ```shell
    docker run --rm -t -i  --network my_gitlab_env -v gitlab-runner-config:/etc/gitlab-runner gitlab/gitlab-runner register
    ...
    Please enter the gitlab-ci coordinator URL (e.g. https://gitlab.com/):
    **http://gitlab**
    Please enter the gitlab-ci token for this runner:
    **-cxvXsWVmCj7UHFzsGh4**
    Please enter the gitlab-ci description for this runner:
    [4d9c097dab37]: 
    Please enter the gitlab-ci tags for this runner (comma separated):

    Registering runner... succeeded                     runner=-cxvXsWV
    Please enter the executor: custom, docker, parallels, virtualbox, docker-ssh+machine, kubernetes, docker-ssh, shell, ssh, docker+machine:
    **docker**
    Please enter the default Docker image (e.g. ruby:2.6):
    e**xatk/script-languages:test_environment_docker_runner**
    Runner registered successfully. Feel free to start it, but if it's running already the config should be automatically reloaded! 
    ```


    4. DIE Konfig muss noch angepasst werden, damit der Executor im gleichen Netzt ist, wie der runner 
    ```shell
    docker exec -it gitlab-runner bin/bash
    nano /etc/gitlab-runner/config.toml

    volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]
    network_mode = "my_gitlab_env"
    ```


    5. restart ist zu empfehlen
    ```shell
    docker restart gitlab-runner
    ```



# Variables:

```shell
export ENVIRONMENT_NAME=test
export ENVIRONMENT_TYPE=EnvironmentType.docker_db
export ENVIRONMENT_DATABASE_HOST=172.29.0.2
export ENVIRONMENT_DATABASE_DB_PORT=8888
export ENVIRONMENT_DATABASE_BUCKETFS_PORT=6583
export ENVIRONMENT_DATABASE_CONTAINER_NAME=db_container_test
export ENVIRONMENT_DATABASE_CONTAINER_NETWORK_ALIASES="exasol_test_database db_container_test"
export ENVIRONMENT_DATABASE_CONTAINER_IP_ADDRESS=172.29.0.2
export ENVIRONMENT_DATABASE_CONTAINER_DEFAULT_BRIDGE_IP_ADDRESS=172.17.0.3
export ENVIRONMENT_TEST_CONTAINER_NAME=test_container_test
export ENVIRONMENT_TEST_CONTAINER_NETWORK_ALIASES="test_container test_container_test"
export ENVIRONMENT_TEST_CONTAINER_IP_ADDRESS=172.29.0.3
```