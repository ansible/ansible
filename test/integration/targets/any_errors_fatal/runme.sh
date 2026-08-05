#!/usr/bin/env bash

set -ux
ansible-playbook -i inventory "$@" play_level.yml| tee out.txt | grep 'any_errors_fatal_play_level_post_fail'
res=$?
cat out.txt
if [ "${res}" -eq 0 ] ; then
    exit 1
fi

ansible-playbook -i inventory "$@" on_includes.yml | tee out.txt | grep 'any_errors_fatal_this_should_never_be_reached'
res=$?
cat out.txt
if [ "${res}" -eq 0 ] ; then
    exit 1
fi

ansible-playbook -i inventory "$@" always_block.yml | tee out.txt | grep 'any_errors_fatal_always_block_start'
res=$?
cat out.txt

if [ "${res}" -ne 0 ] ; then
    exit 1
fi

for test_name in test_include_role test_include_tasks; do
  ansible-playbook -i inventory "$@" -e test_name=$test_name 50897.yml | tee out.txt | grep 'any_errors_fatal_this_should_never_be_reached'
  res=$?
  cat out.txt
  if [ "${res}" -eq 0 ] ; then
      exit 1
  fi
done

set -e

ansible-playbook -i inventory "$@" 31543.yml | tee out.txt
[ "$(grep -c 'SHOULD NOT HAPPEN' out.txt)" -eq 0 ]

ansible-playbook -i inventory "$@" 36308.yml | tee out.txt
[ "$(grep -c 'handler1 ran' out.txt)" -eq 1 ]

ansible-playbook -i inventory "$@" 73246.yml | tee out.txt
[ "$(grep -c 'PASSED' out.txt)" -eq 1 ]

ansible-playbook -i inventory "$@" 80981.yml | tee out.txt
[ "$(grep -c 'SHOULD NOT HAPPEN' out.txt)" -eq 0 ]
[ "$(grep -c 'rescuedd' out.txt)" -eq 2 ]
[ "$(grep -c 'recovered' out.txt)" -eq 2 ]

run_83292_case() {
  local playbook="$1"
  local rescue_marker="$2"
  local recovered_marker="$3"
  shift 3

  set +e
  output="$(ansible-playbook -i inventory "$@" "$playbook" 2>&1)"
  status=$?
  set -e
  printf '%s\n' "$output"
  [ "$status" -eq 0 ]
  [ "$(grep -c 'SHOULD NOT HAPPEN' <<< "$output")" -eq 0 ]
  for host in testhost testhost2; do
    [ "$(grep -cF "\"$rescue_marker $host\"" <<< "$output")" -eq 1 ]
    [ "$(grep -cF "\"$recovered_marker $host\"" <<< "$output")" -eq 1 ]
  done
}

run_83292_case 83292_explicit.yml '83292 explicit rescue' '83292 explicit recovered' "$@"
run_83292_case 83292_implicit.yml '83292 implicit rescue' '83292 implicit recovered' "$@"
run_83292_case 83292_bypass.yml '83292 bypass rescue' '83292 bypass recovered' "$@"

run_83292_nested_case() {
  for max_fail_pct in 0 1 50 100; do
    set +e
    output="$(ansible-playbook -i inventory "$@" -e max_fail_pct="$max_fail_pct" 83292_nested.yml 2>&1)"
    status=$?
    set -e
    printf '%s\n' "$output"
    [ "$status" -eq 0 ]
    [ "$(grep -c 'SHOULD NOT HAPPEN' <<< "$output")" -eq 0 ]
    for host in testhost testhost2; do
      [ "$(grep -cF '"83292 nested rescue '$host'"' <<< "$output")" -eq 1 ]
      [ "$(grep -cF '"83292 nested recovered '$host'"' <<< "$output")" -eq 1 ]
      [ "$(grep -cF '"83292 nested post '$host'"' <<< "$output")" -eq 1 ]
    done
  done
}

run_83292_nested_case "$@"

run_83292_outer_fallback_case() {
  local playbook="$1"
  local rescue_marker="$2"
  local recovered_marker="$3"
  local forbidden_task="$4"
  shift 4

  for max_fail_pct in default 0; do
    extra_args=()
    if [ "$max_fail_pct" != default ]; then
      extra_args=(-e max_fail_pct="$max_fail_pct")
    fi

    set +e
    output="$(ansible-playbook -i inventory "$@" "${extra_args[@]}" "$playbook" 2>&1)"
    status=$?
    set -e
    printf '%s\n' "$output"
    [ "$status" -eq 0 ]
    [ "$(grep -cF "TASK [$forbidden_task]" <<< "$output")" -eq 0 ]
    for host in testhost testhost2; do
      [ "$(grep -cF "\"$rescue_marker $host\"" <<< "$output")" -eq 1 ]
      [ "$(grep -cF "\"$recovered_marker $host\"" <<< "$output")" -eq 1 ]
    done
  done
}

run_83292_outer_fallback_case 83292_outer_fallback.yml '83292 outer fallback rescue' '83292 outer fallback recovered' 'Do not continue inside the failed inner block' "$@"
run_83292_outer_fallback_case 83292_outer_fallback_always.yml '83292 outer fallback always rescue' '83292 outer fallback always recovered' 'Do not continue inside the failed inner block' "$@"

run_83292_max_fail_case() {
  local playbook="$1"
  local rescue_marker="$2"
  local recovered_marker="$3"
  shift 3

  for max_fail_pct in 0 1 50 100; do
    set +e
    output="$(ansible-playbook -i inventory "$@" -e max_fail_pct="$max_fail_pct" "$playbook" 2>&1)"
    status=$?
    set -e
    printf '%s\n' "$output"
    [ "$status" -eq 0 ]
    [ "$(grep -c 'SHOULD NOT HAPPEN' <<< "$output")" -eq 0 ]
    for host in testhost testhost2; do
      [ "$(grep -cF "\"$rescue_marker $host\"" <<< "$output")" -eq 1 ]
      [ "$(grep -cF "\"$recovered_marker $host\"" <<< "$output")" -eq 1 ]
    done
  done
}

run_83292_max_fail_case 83292_max_fail_explicit.yml '83292 maxfail explicit rescue' '83292 maxfail explicit recovered' "$@"
run_83292_max_fail_case 83292_max_fail_implicit.yml '83292 maxfail implicit rescue' '83292 maxfail implicit recovered' "$@"

set +e
output="$(ansible-playbook -i inventory "$@" 83292_max_fail_control.yml 2>&1)"
status=$?
set -e
printf '%s\n' "$output"
[ "$status" -ne 0 ]
[ "$(grep -c 'SHOULD NOT HAPPEN' <<< "$output")" -eq 0 ]

run_83292_terminal_case() {
  local playbook="$1"
  local rescue_marker="$2"
  local terminal_marker="$3"
  shift 3

  set +e
  output="$(ansible-playbook -i inventory "$@" "$playbook" 2>&1)"
  status=$?
  set -e
  printf '%s\n' "$output"
  [ "$status" -ne 0 ]
  [ "$(grep -c 'SHOULD NOT HAPPEN' <<< "$output")" -eq 0 ]
  for host in testhost testhost2; do
    [ "$(grep -cF "\"$rescue_marker $host\"" <<< "$output")" -eq 1 ]
    if [ -n "$terminal_marker" ]; then
      [ "$(grep -cF "\"$terminal_marker $host\"" <<< "$output")" -eq 1 ]
    fi
  done
}

run_83292_terminal_case 83292_rescue_failure.yml '83292 rescue failure' '' "$@"
run_83292_terminal_case 83292_always_failure.yml '83292 always failure rescue' '83292 always failure always' "$@"
