#!/bin/bash

ansible-playbook -i ../../inventory $@ test_include_role.yml
ansible-playbook -i ../../inventory $@ test_include_role_bogus_option.yml && :
WRONG_RC=$?
echo "rc was $WRONG_RC (4 is expected)"
[ $WRONG_RC -eq 4 ]
