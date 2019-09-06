#!/usr/bin/env bash

set -eux
export VMWARE_TEST_PLATFORM=worldstream
exec bash test/utils/shippable/cloud.sh vcenter/3.7/1
