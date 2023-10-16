#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

whoami
apt-get update -y
apt-get install iproute2 -y
ip addr show
