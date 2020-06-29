
# Umgebung anlgegen:

1. Gitlab Server aufsetzten

    1. https://docs.gitlab.com/omnibus/docker/

    2. Für mac OS hat sich bewährt ein separates Netzwerk anzulegen
    ```shell
    docker network create my_gitlab_env
    ```

    3. Das erzeugte Netzwerk muss dann beim starten des Gitlab-Servers mit angegeben werden
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



2. gitlab runner

    1.  Volume anlgeben um Configuration abzulegen
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
    **exatk/script-languages:test_environment_docker_runner**
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