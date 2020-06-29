export $GITLAB_HOME=$PWD/gitlab_home
mkdir -p $GITLAB_HOME/gitlab
docker run --detach  \
     --hostname gitlab  \
     --publish 4443:443 \
     --publish 8080:80 \
     --publish 2222:22   \
     --name gitlab \
     --restart always \
     --volume $GITLAB_HOME/gitlab/config:/etc/gitlab   \
     --volume $GITLAB_HOME/gitlab/logs:/var/log/gitlab   \
     --volume $GITLAB_HOME/gitlab/data:/var/opt/gitlab  \
     --network my_gitlab_env \
     gitlab/gitlab-ce:latest

export PERSONAL_ACCESS_TOKEN=token-string-here123
gitlab-rails runner "token = User.find_by_username('root').personal_access_tokens.create(scopes: [:read_user, :read_repository], name: 'Automation token'); token.set_token('$PERSONAL_ACCESS_TOKEN'); token.save!"

export RUNNER_TOKEN=$(gitlab-rails runner "puts Gitlab::CurrentSettings.current_application_settings.runners_registration_token")

docker run \
  --rm \
  -v "$GITLAB_HOME/gitlab-runner-config:/etc/gitlab-runner" \
  --network my_gitlab_env \
  gitlab/gitlab-runner \
  register \
  --non-interactive \
  --executor "docker" \
  --docker-image exatk/script-languages:test_environment_docker_runner \
  --url "http://gitlab" \
  --registration-token "$RUNNER_TOKEN" \
  --description "docker-runner" \
  --run-untagged="true" \
  --locked="false" \
  --access-level="not_protected"

docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$GITLAB_HOME/gitlab-runner-config:/etc/gitlab-runner" \
  --network my_gitlab_env \
  gitlab/gitlab-runner
