#!/usr/bin/env bash

set -eux -o pipefail

# the invocation is only returned in the task result when this is enabled
export ANSIBLE_INJECT_INVOCATION=1

check_no_leaks() {
    # every value the playbooks expect to be redacted is named SECRET_*, so none of them may reach the output
    if grep -E 'SECRET_[A-Z_]+' "$1"; then
        echo "FAIL: a header value which should have been redacted leaked into the output of $1" >&2
        exit 1
    fi
}

# no configuration: only the well-known headers are redacted
ansible-playbook defaults.yml -i ../../inventory "$@" 2>&1 | tee "${OUTPUT_DIR}/defaults.log"
check_no_leaks "${OUTPUT_DIR}/defaults.log"

# additional headers from the environment variable
ANSIBLE_REDACT_HTTP_HEADERS='X-Api-Key, X-Token' \
    ansible-playbook configured.yml -i ../../inventory "$@" 2>&1 | tee "${OUTPUT_DIR}/env.log"
check_no_leaks "${OUTPUT_DIR}/env.log"

# additional headers from the ini configuration file
ANSIBLE_CONFIG=redact_http_headers.cfg \
    ansible-playbook configured.yml -i ../../inventory "$@" 2>&1 | tee "${OUTPUT_DIR}/ini.log"
check_no_leaks "${OUTPUT_DIR}/ini.log"

# additional headers from a variable
ansible-playbook configured_vars.yml -i ../../inventory "$@" 2>&1 | tee "${OUTPUT_DIR}/vars.log"
check_no_leaks "${OUTPUT_DIR}/vars.log"
