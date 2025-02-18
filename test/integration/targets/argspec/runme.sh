#!/usr/bin/env bash

set -eu

ansible testhost -i ../../inventory -m include_role -a name=argspec --playbook-dir . "${@}"
