#!/usr/bin/env bash

source virtualenv.sh
export ANSIBLE_ROLES_PATH=../
set -euvx

ansible-playbook test.yml "$@"

ansible-inventory -i with_untrusted.yml --list > "$OUTPUT_DIR/with_untrusted_actual.json"

diff with_untrusted_expected.json "$OUTPUT_DIR/with_untrusted_actual.json"
