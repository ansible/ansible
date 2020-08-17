#!/usr/bin/env bash
set -x
set -e
checkmodule -Mmo ansible-podman.mod ansible-podman.te
semodule_package -o ansible-podman.pp -m ansible-podman.mod

set +x
echo "Module built. Now run this as root:"
echo "semodule -i $(pwd)/ansible-podman.pp"
