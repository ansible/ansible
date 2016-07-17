#!/bin/bash -eux

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '../../..')))")
image=${IMAGE}
keep_containers=""

function show_environment
{
    docker ps
}

function cleanup
{
    if [ "${controller_shared_dir}" ]; then
        rm -rf "${controller_shared_dir}"
    fi

    if [ "${keep_containers}" == "" ]; then
        if [ "${container_id}" ]; then
            docker rm -f "${container_id}"
        fi
    fi
    show_environment
}

if [ "${SHIPPABLE_BUILD_DIR:-}" ]; then
    host_shared_dir="/home/shippable/cache/build-${BUILD_NUMBER}"
    controller_shared_dir="/home/shippable/cache/build-${BUILD_NUMBER}"
else
    host_shared_dir="${source_root}"
    controller_shared_dir=""
fi

if [ "${controller_shared_dir}" ]; then
    cp -a "${SHIPPABLE_BUILD_DIR}" "${controller_shared_dir}"
fi

mkdir -p ${host_shared_dir}/test_data/auth
mkdir -p ${host_shared_dir}/test_data/certs

show_environment 

docker_api_version=`docker version --format "{{ .Server.APIVersion }}"`
echo "Setting DOCKER_API_VERSION = ${docker_api_version}"
echo "Shippable host IP = ${SHIPPABLE_HOST_IP}"

container_id=$(docker run \
               -v /var/run/docker.sock:/var/run/docker.sock \
               -v ${host_shared_dir}:/ansible \
               -v ${host_shared_dir}/test_data:/data \
               -e DOCKER_DATA_PATH=${host_shared_dir}/test_data \
               -e DOCKER_API_VERSION=${docker_api_version} \
               --add-host=ansibleregistry.com:${SHIPPABLE_HOST_IP} \
               "${image}" /run.sh)

docker inspect registry
docker exec registry ls -l /auth
docker exec registry ls -l /certs
docker exec registry cat /auth/htpasswd
docker login -u testuser -p testpassword https://ansibleregistry.com:5000

# show_environment
# cleanup
