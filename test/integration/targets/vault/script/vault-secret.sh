#!/usr/bin/env bash

set -eu

basename="$(basename $0)"
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
