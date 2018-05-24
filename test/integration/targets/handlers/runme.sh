#!/usr/bin/env bash

set -eux

ansible-playbook test_handlers.yml -i inventory.handlers -v "$@" --tags scenario1
ansible-playbook test_listening_handlers.yml -i inventory.handlers -v "$@"

[ "$(ansible-playbook test_handlers.yml -i inventory.handlers -v "$@" --tags scenario2 -l A \
| egrep -o 'RUNNING HANDLER \[test_handlers : .*?]')" = "RUNNING HANDLER [test_handlers : test handler]" ]

# Not forcing, should only run on successful host
[ "$(ansible-playbook test_force_handlers.yml -i inventory.handlers -v "$@" --tags normal \
| egrep -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_B" ]

# Forcing from command line
[ "$(ansible-playbook test_force_handlers.yml -i inventory.handlers -v "$@" --tags normal --force-handlers \
| egrep -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_A CALLED_HANDLER_B" ]

# Forcing from command line, should only run later tasks on unfailed hosts
[ "$(ansible-playbook test_force_handlers.yml -i inventory.handlers -v "$@" --tags normal --force-handlers \
| egrep -o CALLED_TASK_. | sort | uniq | xargs)" = "CALLED_TASK_B CALLED_TASK_D CALLED_TASK_E" ]

# Forcing from command line, should call handlers even if all hosts fail
[ "$(ansible-playbook test_force_handlers.yml -i inventory.handlers -v "$@" --tags normal --force-handlers -e fail_all=yes \
| egrep -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_A CALLED_HANDLER_B" ]

# Forcing from ansible.cfg
[ "$(ANSIBLE_FORCE_HANDLERS=true ansible-playbook test_force_handlers.yml -i inventory.handlers -v "$@" --tags normal \
| egrep -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_A CALLED_HANDLER_B" ]

# Forcing true in play
[ "$(ansible-playbook test_force_handlers.yml -i inventory.handlers -v "$@" --tags force_true_in_play \
| egrep -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_A CALLED_HANDLER_B" ]

# Forcing false in play, which overrides command line
[ "$(ansible-playbook test_force_handlers.yml -i inventory.handlers -v "$@" --tags force_false_in_play --force-handlers \
| egrep -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_B" ]

[ "$(ansible-playbook test_handlers_include.yml -i ../../inventory -v "$@" --tags playbook_include_handlers \
| egrep -o 'RUNNING HANDLER \[.*?]')" = "RUNNING HANDLER [test handler]" ]

[ "$(ansible-playbook test_handlers_include.yml -i ../../inventory -v "$@" --tags role_include_handlers \
| egrep -o 'RUNNING HANDLER \[test_handlers_include : .*?]')" = "RUNNING HANDLER [test_handlers_include : test handler]" ]

[ "$(ansible-playbook test_handlers_include_role.yml -i ../../inventory -v "$@" \
| egrep -o 'RUNNING HANDLER \[test_handlers_include_role : .*?]')" = "RUNNING HANDLER [test_handlers_include_role : test handler]" ]

# Notify handler listen
ansible-playbook test_handlers_listen.yml -i inventory.handlers -v "$@"

# Notify inexistent handlers results in error
set +e
result="$(ansible-playbook test_handlers_inexistent_notify.yml -i inventory.handlers "$@" 2>&1)"
set -e
grep -q "ERROR! The requested handler 'notify_inexistent_handler' was not found in either the main handlers list nor in the listening handlers list" <<< "$result"

# Notify inexistent handlers without errors when ANSIBLE_ERROR_ON_MISSING_HANDLER=false
ANSIBLE_ERROR_ON_MISSING_HANDLER=false ansible-playbook test_handlers_inexistent_notify.yml -i inventory.handlers -v "$@"

# https://github.com/ansible/ansible/issues/36649
output_dir=/tmp
set +e
result="$(ansible-playbook test_handlers_any_errors_fatal.yml -e output_dir=$output_dir -i inventory.handlers -v "$@" 2>&1)"
set -e
[ ! -f $output_dir/should_not_exist_B ] || (rm -f $output_dir/should_not_exist_B && exit 1)
