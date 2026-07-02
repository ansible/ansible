#!/usr/bin/env bash
# A command wrapper that delegates to sudo after lowering privilege through an intermediate user (via sudo).
# This allows forcing an environment that always requires a password prompt for sudo.

set -eu

args=("${@}")

for i in "${!args[@]}"; do
  case "${args[$i]}" in
    "--intermediate-user")
      intermediate_user_idx="${i}"
      ;;
  esac
done

intermediate_user_name="${args[intermediate_user_idx+1]}"

unset "args[intermediate_user_idx]"
unset "args[intermediate_user_idx+1]"

exec sudo -n -u "${intermediate_user_name}" sudo -k "${args[@]}"
