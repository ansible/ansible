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

06:24 ERROR: test/integration/targets/vault/script/vault-secret.sh:5:22: SC2086: Double quote to prevent globbing and word splitting. (100%)
06:24 ERROR: test/integration/targets/vault/script/vault-secret.sh:6:21: SC2046: Quote this to prevent word splitting. (100%)
06:24 ERROR: test/integration/targets/vault/script/vault-secret.sh:6:31: SC2086
