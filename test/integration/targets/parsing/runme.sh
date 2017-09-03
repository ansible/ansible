#!/usr/bin/env bash

set -eux

ansible-playbook bad_parsing.yml  -i ../../inventory -vvv "$@" --tags prepare,common,scenario5,scenario6 --extra-vars='str2bool_test=False str2int_test=3 str2float_test=3.14'
ansible-playbook good_parsing.yml -i ../../inventory -v "$@" --extra-vars='str2bool_test=False str2int_test=3 str2float_test=3.14' --convert-type
