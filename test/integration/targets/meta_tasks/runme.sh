#!/usr/bin/env bash

set -eux

# test end_host meta task, with when conditional
for test_strategy in linear free; do
  out="$(ansible-playbook test_end_host.yml -i inventory.yml -e test_strategy=$test_strategy -vv "$@")"

  grep -q "META: end_host conditional evaluated to False, continuing execution for testhost" <<< "$out"
  grep -q "META: ending play for testhost2" <<< "$out"
  grep -q '"skip_reason": "end_host conditional evaluated to False, continuing execution for testhost"' <<< "$out"
  grep -q "play not ended for testhost" <<< "$out"
  grep -qv "play not ended for testhost2" <<< "$out"

  out="$(ansible-playbook test_end_host_fqcn.yml -i inventory.yml -e test_strategy=$test_strategy -vv "$@")"

  grep -q "META: end_host conditional evaluated to False, continuing execution for testhost" <<< "$out"
  grep -q "META: ending play for testhost2" <<< "$out"
  grep -q '"skip_reason": "end_host conditional evaluated to False, continuing execution for testhost"' <<< "$out"
  grep -q "play not ended for testhost" <<< "$out"
  grep -qv "play not ended for testhost2" <<< "$out"
done

# test end_host meta task, on all hosts
for test_strategy in linear free; do
  out="$(ansible-playbook test_end_host_all.yml -i inventory.yml -e test_strategy=$test_strategy -vv "$@")"

  grep -q "META: ending play for testhost" <<< "$out"
  grep -q "META: ending play for testhost2" <<< "$out"
  grep -qv "play not ended for testhost" <<< "$out"
  grep -qv "play not ended for testhost2" <<< "$out"

  out="$(ansible-playbook test_end_host_all_fqcn.yml -i inventory.yml -e test_strategy=$test_strategy -vv "$@")"

  grep -q "META: ending play for testhost" <<< "$out"
  grep -q "META: ending play for testhost2" <<< "$out"
  grep -qv "play not ended for testhost" <<< "$out"
  grep -qv "play not ended for testhost2" <<< "$out"
done

# test end_play meta task
for test_strategy in linear free; do
  out="$(ansible-playbook test_end_play.yml -i inventory.yml -e test_strategy=$test_strategy -vv "$@")"

  grep -q "META: ending play" <<< "$out"
  grep -qv 'Failed to end using end_play' <<< "$out"

  out="$(ansible-playbook test_end_play_fqcn.yml -i inventory.yml -e test_strategy=$test_strategy -vv "$@")"

  grep -q "META: ending play" <<< "$out"
  grep -qv 'Failed to end using end_play' <<< "$out"

  out="$(ansible-playbook test_end_play_serial_one.yml -i inventory.yml -e test_strategy=$test_strategy -vv "$@")"

  [ "$(grep -c "Testing end_play on host" <<< "$out" )" -eq 1 ]
  grep -q "META: ending play" <<< "$out"
  grep -qv 'Failed to end using end_play' <<< "$out"

  out="$(ansible-playbook test_end_play_multiple_plays.yml -i inventory.yml -e test_strategy=$test_strategy -vv "$@")"

  grep -q "META: ending play" <<< "$out"
  grep -q "Play 1" <<< "$out"
  grep -q "Play 2" <<< "$out"
  grep -qv 'Failed to end using end_play' <<< "$out"
done

# test end_batch meta task
for test_strategy in linear free; do
  out="$(ansible-playbook test_end_batch.yml -i inventory.yml -e test_strategy=$test_strategy -vv "$@")"

  [ "$(grep -c "Using end_batch" <<< "$out" )" -eq 2 ]
  [ "$(grep -c "META: ending batch" <<< "$out" )" -eq 2 ]
  grep -qv 'Failed to end_batch' <<< "$out"
done

# test refresh
ansible-playbook -i inventory_refresh.yml refresh.yml "$@"
ansible-playbook -i inventory_refresh.yml refresh_preserve_dynamic.yml "$@"

# test rc when end_host in the rescue section
ANSIBLE_FORCE_HANDLERS=0 ansible-playbook test_end_host_rescue_rc.yml
