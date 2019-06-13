

set -eux

export ANSIBLE_RESERVED_VAR_NAMES='warn'

# Test for warnings
ansible -m debug -e 'lookup=function' localhost "$@" 2>&1|grep 'Found variable using reserved name: lookup'
ansible -m debug -e 'name=attribute' localhost "$@" 2>&1|grep 'Found variable using reserved name: name'
ansible -m debug -e 'loop_with=private_attribute' localhost 2>&1|grep 'Found variable using reserved name: loop_with'

# find right number of warnings
[ $(ansible-playbook defined_warnings.yml "$@" 2>&1 |grep -c 'Found variable using reserved name:') -eq 3 ]

export ANSIBLE_RESERVED_VAR_NAMES='error'
# these should fail in error
ansible -m debug -e 'lookup=thisshouldfail' localhost "$@" || true
ansible-playbook defined_warnings.yml "$@" || true

export ANSIBLE_RESERVED_VAR_NAMES='ignore'
ansible-playbook defined_warnings.yml "$@" |grep -v 'Found variable using reserved name:'
