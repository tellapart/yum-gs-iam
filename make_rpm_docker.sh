#!/usr/bin/env bash
source VERSION

docker build -t yum-gs-build .
docker run -t yum-gs-build /bin/bash -c '/make_rpm.sh'
container=$(docker ps -l -q)
docker cp "$container:/$NAME-$VERSION.rpm" .
docker stop "$container"
docker rm "$container"
