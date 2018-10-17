#!/usr/bin/env bash

set -eux

# test skip_host meta task, with when conditional
for test_strategy in linear free; do
  out="$(ansible-playbook test_skip_host.yml -i ../../inventory -e test_strategy=$test_strategy -vv "$@")"

  grep -q "META: skip_host conditional evaluated to false, continuing execution for testhost" <<< "$out"
  grep -q "META: skipping testhost2 for the rest of the play" <<< "$out"
  grep -q "testhost not skipped" <<< "$out"
  grep -qv "testhost2 not skipped" <<< "$out"
done

# test skip_host meta task, on all hosts
for test_strategy in linear free; do
  out="$(ansible-playbook test_skip_host_all.yml -i ../../inventory -e test_strategy=$test_strategy -vv "$@")"

  grep -q "META: skipping testhost for the rest of the play" <<< "$out"
  grep -q "META: skipping testhost2 for the rest of the play" <<< "$out"
  grep -qv "testhost not skipped" <<< "$out"
  grep -qv "testhost2 not skipped" <<< "$out"
done
