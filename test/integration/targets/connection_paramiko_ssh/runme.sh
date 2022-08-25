#!/usr/bin/env bash

source /etc/os-release

if [ "${ID}" == "alpine" ]; then
  echo "skipping due to issues installing paramiko"
  exit 0
fi

set -eux

source ../setup_paramiko/setup.sh

./test.sh
