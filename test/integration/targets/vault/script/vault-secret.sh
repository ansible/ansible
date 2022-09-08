#!/usr/bin/env bash

set -eu

# shellcheck disable=SC2086
basename="$(basename $0)"
# shellcheck disable=SC2046
# shellcheck disable=SC2086
dirname="$(basename $(dirname $0))"
basename_prefix="get-password"
default_password="foo-bar"

case "${basename}" in
  "${basename_prefix}"-*)
    password="${default_password}-${basename#${basename_prefix}-}"
    ;;
  *)
    password="${default_password}"
    ;;
esac

echo "${password}_${dirname}"
