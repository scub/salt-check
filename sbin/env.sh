#!/bin/bash

IMAGE_NAME='wcannon/saltcheck'

if [ $(docker images | egrep -c -i $IMAGE_NAME) != 1 ]; then
  echo "Building docker image '$IMAGE_NAME' from $(grep 'FROM' $(pwd)/Dockerfile)"
  docker build -t $IMAGE_NAME .
fi

# Start our docker engine
docker run --add-host=salt:127.0.0.1 --rm -it       \
    -v $(pwd)/salt:/srv/salt/                       \
    -v $(pwd)/pillar:/srv/pillar                    \
    -v $(pwd)/minion_config/minion:/etc/salt/minion \
    -v $(pwd)/sbin/docker:/opt/sbin                 \
    $IMAGE_NAME /bin/bash
