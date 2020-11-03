#!/usr/bin/env bash

set -eux

# test end_host meta task, with when conditional
for test_strategy in linear free; do
  out="$(ansible-playbook test_end_host.yml -i inventory.yml -e test_strategy=$test_strategy -vv "$@")"

  grep -q "META: end_host conditional evaluated to false, continuing execution for testhost" <<< "$out"
  grep -q "META: ending play for testhost2" <<< "$out"
  grep -q "play not ended for testhost" <<< "$out"
  grep -qv "play not ended for testhost2" <<< "$out"

  out="$(ansible-playbook test_end_host_fqcn.yml -i inventory.yml -e test_strategy=$test_strategy -vv "$@")"

  grep -q "META: end_host conditional evaluated to false, continuing execution for testhost" <<< "$out"
  grep -q "META: ending play for testhost2" <<< "$out"
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
done
