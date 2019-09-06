#!/usr/bin/env bash

set -eux
export VMWARE_TEST_PLATFORM=govcsim
exec bash test/utils/shippable/cloud.sh vcenter/3.7/1
