#!/usr/bin/env bash

set -eu
set -o pipefail

docker exec "$1" tar cz -C /root/ansible/test results | tar oxz -C test
