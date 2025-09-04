#!/usr/bin/env bash

set -eux

export ANSIBLE_FORCE_HANDLERS

ANSIBLE_FORCE_HANDLERS=false

# simple handler test
ansible-playbook test_handlers.yml -i inventory.handlers -v "$@" --tags scenario1

# simple from_handlers test
ansible-playbook from_handlers.yml -i inventory.handlers -v "$@" --tags scenario1

ansible-playbook test_listening_handlers.yml -i inventory.handlers -v "$@"

[ "$(ansible-playbook test_handlers.yml -i inventory.handlers -v "$@" --tags scenario2 -l A \
| grep -E -o 'RUNNING HANDLER \[test_handlers : .*]')" = "RUNNING HANDLER [test_handlers : test handler]" ]

# Test forcing handlers using the linear and free strategy
for strategy in linear free; do

  export ANSIBLE_STRATEGY=$strategy

  # Not forcing, should only run on successful host
  [ "$(ansible-playbook test_force_handlers.yml -i inventory.handlers -v "$@" --tags normal \
  | grep -E -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_B" ]

  # Forcing from command line
  [ "$(ansible-playbook test_force_handlers.yml -i inventory.handlers -v "$@" --tags normal --force-handlers \
  | grep -E -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_A CALLED_HANDLER_B" ]

  # Forcing from command line, should only run later tasks on unfailed hosts
  [ "$(ansible-playbook test_force_handlers.yml -i inventory.handlers -v "$@" --tags normal --force-handlers \
  | grep -E -o CALLED_TASK_. | sort | uniq | xargs)" = "CALLED_TASK_B CALLED_TASK_D CALLED_TASK_E" ]

  # Forcing from command line, should call handlers even if all hosts fail
  [ "$(ansible-playbook test_force_handlers.yml -i inventory.handlers -v "$@" --tags normal --force-handlers -e fail_all=yes \
  | grep -E -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_A CALLED_HANDLER_B" ]

  # Forcing from ansible.cfg
  [ "$(ANSIBLE_FORCE_HANDLERS=true ansible-playbook test_force_handlers.yml -i inventory.handlers -v "$@" --tags normal \
  | grep -E -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_A CALLED_HANDLER_B" ]

  # Forcing true in play
  [ "$(ansible-playbook test_force_handlers.yml -i inventory.handlers -v "$@" --tags force_true_in_play \
  | grep -E -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_A CALLED_HANDLER_B" ]

  # Forcing false in play, which overrides command line
  [ "$(ansible-playbook test_force_handlers.yml -i inventory.handlers -v "$@" --tags force_false_in_play --force-handlers \
  | grep -E -o CALLED_HANDLER_. | sort | uniq | xargs)" = "CALLED_HANDLER_B" ]

  # https://github.com/ansible/ansible/pull/80898
  [ "$(ansible-playbook 80880.yml -i inventory.handlers -vv "$@" 2>&1)" ]

  unset ANSIBLE_STRATEGY

done

[ "$(ansible-playbook test_handlers_include.yml -i ../../inventory -v "$@" --tags playbook_include_handlers \
| grep -E -o 'RUNNING HANDLER \[.*]')" = "RUNNING HANDLER [test handler]" ]

[ "$(ansible-playbook test_handlers_include.yml -i ../../inventory -v "$@" --tags role_include_handlers \
| grep -E -o 'RUNNING HANDLER \[test_handlers_include : .*]')" = "RUNNING HANDLER [test_handlers_include : test handler]" ]

[ "$(ansible-playbook test_handlers_include_role.yml -i ../../inventory -v "$@" \
| grep -E -o 'RUNNING HANDLER \[test_handlers_include_role : .*]')" = "RUNNING HANDLER [test_handlers_include_role : test handler]" ]

# Notify handler listen
ansible-playbook test_handlers_listen.yml -i inventory.handlers -v "$@"

# https://github.com/ansible/ansible/issues/82363
ansible-playbook test_multiple_handlers_with_recursive_notification.yml -i inventory.handlers -v "$@"

# Notify inexistent handlers results in error
set +e
result="$(ansible-playbook test_handlers_inexistent_notify.yml -i inventory.handlers "$@" 2>&1)"
set -e
grep -q "The requested handler 'notify_inexistent_handler' was not found in either the main handlers list nor in the listening handlers list" <<< "$result"

# Notify inexistent handlers without errors when ANSIBLE_ERROR_ON_MISSING_HANDLER=false
ANSIBLE_ERROR_ON_MISSING_HANDLER=false ansible-playbook test_handlers_inexistent_notify.yml -i inventory.handlers -v "$@"

ANSIBLE_ERROR_ON_MISSING_HANDLER=false ansible-playbook test_templating_in_handlers.yml -v "$@"

# https://github.com/ansible/ansible/issues/36649
output_dir=/tmp
set +e
result="$(ansible-playbook test_handlers_any_errors_fatal.yml -e output_dir=$output_dir -i inventory.handlers -v "$@" 2>&1)"
set -e
[ ! -f $output_dir/should_not_exist_B ] || (rm -f $output_dir/should_not_exist_B && exit 1)

# https://github.com/ansible/ansible/issues/47287
[ "$(ansible-playbook test_handlers_including_task.yml -i ../../inventory -v "$@" | grep -E -o 'failed=[0-9]+')" = "failed=0" ]

# https://github.com/ansible/ansible/issues/71222
ansible-playbook test_role_handlers_including_tasks.yml -i ../../inventory -v "$@"

# https://github.com/ansible/ansible/issues/27237
set +e
result="$(ansible-playbook test_handlers_template_run_once.yml -i inventory.handlers "$@" 2>&1)"
set -e
grep -q "handler A" <<< "$result"
grep -q "handler B" <<< "$result"

# Test an undefined variable in another handler name isn't a failure
ansible-playbook 58841.yml "$@" --tags lazy_evaluation 2>&1 | tee out.txt ; cat out.txt
grep out.txt -e "\[WARNING\]: Handler 'handler name with {{ test_var }}' is unusable"
[ "$(grep out.txt -ce 'handler ran')" = "1" ]
[ "$(grep out.txt -ce 'handler with var ran')" = "0" ]

# Test templating a handler name with a defined variable
ansible-playbook 58841.yml "$@" --tags evaluation_time -e test_var=myvar | tee out.txt ; cat out.txt
[ "$(grep out.txt -ce 'handler ran')" = "0" ]
[ "$(grep out.txt -ce 'handler with var ran')" = "1" ]

# Test the handler is not found when the variable is undefined
ansible-playbook 58841.yml "$@" --tags evaluation_time 2>&1 | tee out.txt ; cat out.txt
grep out.txt -e "The requested handler 'handler name with myvar' was not found"
grep out.txt -e "\[WARNING\]: Handler 'handler name with {{ test_var }}' is unusable"
[ "$(grep out.txt -ce 'handler ran')" = "0" ]
[ "$(grep out.txt -ce 'handler with var ran')" = "0" ]

# Test include_role and import_role cannot be used as handlers
ansible-playbook test_role_as_handler.yml "$@"  2>&1 | tee out.txt
grep out.txt -e "Using 'include_role' as a handler is not supported."

# Test notifying a handler from within include_tasks does not work anymore
ansible-playbook test_notify_included.yml "$@"  2>&1 | tee out.txt
[ "$(grep out.txt -ce 'I was included')" = "1" ]
grep out.txt -e "The requested handler 'handler_from_include' was not found in either the main handlers list nor in the listening handlers list"

ansible-playbook test_handlers_meta.yml -i inventory.handlers -vv "$@" | tee out.txt
[ "$(grep out.txt -ce 'RUNNING HANDLER \[noop_handler\]')" = "1" ]
[ "$(grep out.txt -ce 'META: noop')" = "1" ]

# https://github.com/ansible/ansible/issues/46447
test "$(ansible-playbook 46447.yml -i inventory.handlers "$@" 2>&1 | grep -c 'SHOULD NOT GET HERE')" = "0"

# https://github.com/ansible/ansible/issues/52561
ansible-playbook 52561.yml -i inventory.handlers "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'handler1 ran')" = "1" ]

# Test flush_handlers meta task does not imply any_errors_fatal
ansible-playbook 54991.yml -i inventory.handlers "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'handler ran')" = "5" ]

ansible-playbook order.yml -i inventory.handlers "$@" 2>&1
set +e
ansible-playbook order.yml --force-handlers -e test_force_handlers=true -i inventory.handlers "$@" 2>&1
set -e

ansible-playbook include_handlers_fail_force.yml --force-handlers -i inventory.handlers "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'included handler ran')" = "1" ]

ansible-playbook test_flush_handlers_as_handler.yml -i inventory.handlers "$@"  2>&1 | tee out.txt
grep out.txt -e "flush_handlers cannot be used as a handler"

ansible-playbook test_skip_flush.yml -i inventory.handlers "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'handler ran')" = "0" ]

ansible-playbook test_flush_in_rescue_always.yml -i inventory.handlers "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'handler ran in rescue')" = "1" ]
[ "$(grep out.txt -ce 'handler ran in always')" = "2" ]
[ "$(grep out.txt -ce 'lockstep works')" = "2" ]

ansible-playbook test_handlers_infinite_loop.yml -i inventory.handlers "$@" 2>&1

ansible-playbook test_flush_handlers_rescue_always.yml -i inventory.handlers "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'rescue ran')" = "1" ]
[ "$(grep out.txt -ce 'always ran')" = "2" ]
[ "$(grep out.txt -ce 'should run for both hosts')" = "2" ]

ansible-playbook test_fqcn_meta_flush_handlers.yml -i inventory.handlers "$@" 2>&1 | tee out.txt
grep out.txt -e "handler ran"
grep out.txt -e "after flush"

ansible-playbook 79776.yml -i inventory.handlers "$@"

ansible-playbook test_block_as_handler.yml "$@"  2>&1 | tee out.txt
grep out.txt -e "Using a block as a handler is not supported."

ansible-playbook test_block_as_handler-include.yml "$@"  2>&1 | tee out.txt
grep out.txt -e "Using a block as a handler is not supported."

ansible-playbook test_block_as_handler-import.yml "$@"  2>&1 | tee out.txt
grep out.txt -e "Using a block as a handler is not supported."

ansible-playbook test_include_role_handler_once.yml -i inventory.handlers "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'handler ran')" = "1" ]

ansible-playbook test_listen_role_dedup.yml "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'a handler from a role')" = "1" ]

ansible localhost -m include_role -a "name=r1-dep_chain-vars" "$@"

ansible-playbook test_include_tasks_in_include_role.yml "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'handler ran')" = "1" ]

ansible-playbook test_run_once.yml -i inventory.handlers "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'handler ran once')" = "1" ]

ansible-playbook force_handlers_blocks_81533-1.yml -i inventory.handlers "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'task1')" = "1" ]
[ "$(grep out.txt -ce 'task2')" = "1" ]
[ "$(grep out.txt -ce 'hosts_left')" = "1" ]

ansible-playbook force_handlers_blocks_81533-2.yml -i inventory.handlers "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'hosts_left')" = "1" ]

ansible-playbook nested_flush_handlers_failure_force.yml -i inventory.handlers "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'flush_handlers_rescued')" = "1" ]
[ "$(grep out.txt -ce 'flush_handlers_always')" = "3" ]

ansible-playbook 82241.yml -i inventory.handlers "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'included_task_from_tasks_dir')" = "1" ]

ansible-playbook handlers_lockstep_82307.yml -i inventory.handlers "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'TASK \[handler2\]')" = "0" ]

ansible-playbook handlers_lockstep_83019.yml -i inventory.handlers "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'TASK \[handler1\]')" = "0" ]

ansible-playbook handler_notify_earlier_handler.yml "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'h1_ran')" = "1" ]
[ "$(grep out.txt -ce 'h2_ran')" = "1" ]
[ "$(grep out.txt -ce 'h3_ran')" = "1" ]
[ "$(grep out.txt -ce 'h4_ran')" = "1" ]

ANSIBLE_DEBUG=1 ansible-playbook tagged_play.yml --skip-tags the_whole_play "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'META: triggered running handlers')" = "0" ]
[ "$(grep out.txt -ce 'No handler notifications for')" = "0" ]
[ "$(grep out.txt -ce 'handler_ran')" = "0" ]
[ "$(grep out.txt -ce 'handler1_ran')" = "0" ]

ansible-playbook rescue_flush_handlers.yml "$@"

ANSIBLE_DEBUG=1 ansible-playbook tagged_play.yml --tags task_tag "$@" 2>&1 | tee out.txt
[ "$(grep out.txt -ce 'META: triggered running handlers')" = "1" ]
[ "$(grep out.txt -ce 'handler_ran')" = "0" ]
[ "$(grep out.txt -ce 'handler1_ran')" = "1" ]
