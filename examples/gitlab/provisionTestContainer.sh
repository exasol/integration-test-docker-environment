 #!/bin/bash
 
    source integration-test-docker-environment/.build_output/cache/environments/$CI_JOB_ID/environment_info.sh
    cd $CI_PROJECT_DIR
    docker cp test $ENVIRONMENT_TEST_CONTAINER_NAME:test
    docker cp runQueries.sh $ENVIRONMENT_TEST_CONTAINER_NAME:runQueries.sh
    docker cp build $ENVIRONMENT_TEST_CONTAINER_NAME:build
    mkdir $CI_PROJECT_DIR/tmp
    chmod 666 $CI_PROJECT_DIR/tmp
    #prepare Docker-DB
    docker cp dwh-trunk $ENVIRONMENT_TEST_CONTAINER_NAME:dwh-trunk
    docker exec $ENVIRONMENT_TEST_CONTAINER_NAME bash -c "./runQueries.sh $ENVIRONMENT_DATABASE_HOST $ENVIRONMENT_DATABASE_DB_PORT dwh-trunk" &>> $CI_PROJECT_DIR/tmp/out_$CI_JOB_ID.err