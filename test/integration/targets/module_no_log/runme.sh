#!/usr/bin/env bash

set -eux -o pipefail

ansible-playbook test_syslog.yml "$@"

ansible-playbook test_no_log.yml "$@" -vvvvv 2>&1 | tee "${OUTPUT_DIR}/output.log"

[ "$(grep -c "something_dangerous" "${OUTPUT_DIR}/output.log")" = "0" ]
[ "$(grep -c "1234567" "${OUTPUT_DIR}/output.log")" = "0" ]
[ "$(grep -c "123456.789" "${OUTPUT_DIR}/output.log")" = "0" ]
