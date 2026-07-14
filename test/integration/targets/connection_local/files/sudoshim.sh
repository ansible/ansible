#!/usr/bin/env bash
# A wrapper around `sudo` that replaces the expected password prompt string (if given) with a bogus value.
# This allows testing situations where the expected password prompt is not found.
# This wrapper also supports becoming an intermediate user before executing sudo, to support testing as root.

set -eu

args=("${@}")
intermediate_user_idx=''
original_prompt=''
shell_executable=''
shell_command=''
original_prompt_idx=''

# some args show up after others, but we need them before processing args that came before them
for i in "${!args[@]}"; do
  case "${args[$i]}" in
    "-p")
      original_prompt="${args[i+1]}"
      original_prompt_idx="${i}"
      ;;
    "-c")
      shell_executable="${args[i-1]}"
      shell_command="${args[i+1]}"
      ;;
  esac
done

for i in "${!args[@]}"; do
  case "${args[$i]}" in
    "--inject-stdout-noise")
      echo "stdout noise"
      unset "args[i]"
      ;;
    "--inject-stderr-noise")
      echo >&2 "stderr noise"
      unset "args[i]"
      ;;
    "--bogus-prompt")
      args[original_prompt_idx+1]="BOGUSPROMPT"
      unset "args[i]"
      ;;
    "--intermediate-user")
      intermediate_user_idx="${i}"
      ;;
    "--close-stderr")
      >&2 echo "some injected stderr, EOF now"
      exec 2>&-  # close stderr, doesn't seem to work on Ubuntu 24.04 (either not closed or not seen in Python?)
      unset "args[i]"
      ;;
    "--sleep-before-sudo")
      sleep 3
      unset "args[i]"
      ;;
    "--pretend-to-be-broken-passwordless-sudo")
      echo '{"hello":"not a module response"}'
      exit 0
      ;;
    "--pretend-to-be-broken-sudo")
      echo -n "${original_prompt}"
      read -rs
      echo
      echo "success, but not invoking given command"
      exit 0
      ;;
    "--pretend-to-be-sudo")
      echo -n "${original_prompt}"
      read -rs
      echo
      echo "success, invoking given command"
      "${shell_executable}" -c "${shell_command}"
      exit 0
      ;;
  esac
done

if [[ "${intermediate_user_idx}" ]]; then
  # The current user can sudo without a password prompt, so delegate to an intermediate user first.
  intermediate_user_name="${args[intermediate_user_idx+1]}"

  unset "args[intermediate_user_idx]"
  unset "args[intermediate_user_idx+1]"

  exec sudo -n -u "${intermediate_user_name}" sudo -k "${args[@]}"
else
  # The current user requires a password to sudo, so sudo can be used directly.
  exec sudo -k "${args[@]}"
fi
