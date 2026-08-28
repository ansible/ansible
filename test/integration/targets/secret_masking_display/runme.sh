#!/usr/bin/env bash

set -eux -o pipefail

LOG="${OUTPUT_DIR}/display.log"
ANSIBLE_LOG="${OUTPUT_DIR}/ansible_log_path.log"
rm -f "${ANSIBLE_LOG}"

SEED='version: 1
secrets:
  - Displaywarn0050Secret
  - Displaydeprec0051Secret
  - Displaybanner0052Secret
  - Displayerror0053Secret
  - Displayinvoke0054Secret
  - Displayline0055Secret
'

_ANSIBLE_SECRETS_INPUT_FILES=<(printf '%s' "${SEED}") \
ANSIBLE_INJECT_INVOCATION=True \
ANSIBLE_DEPRECATION_WARNINGS=True \
ANSIBLE_DISPLAY_TRACEBACK=always \
ANSIBLE_LOG_PATH="${ANSIBLE_LOG}" \
ANSIBLE_LOG_VERBOSITY=3 \
    ansible-playbook display.yml -i ../../inventory -vvv "$@" 2>&1 | tee "${LOG}"

registered_secrets=(
    Displaywarn0050Secret
    Displaydeprec0051Secret
    Displaybanner0052Secret
    Displayerror0053Secret
    Displayinvoke0054Secret
    Displayline0055Secret
)
sink_markers=(
    "MARKERBANNER \$REDACTED\$"
    "MARKERWARN \$REDACTED\$"
    "MARKERDEPR \$REDACTED\$"
    "MARKERINVOKE \$REDACTED\$"
    "MARKERERROR \$REDACTED\$"
    "MARKERLINE \$REDACTED\$"
)

# assert_masked FILE
#   No registered plaintext secret may appear anywhere in FILE, each sink must have emitted a redacted
#   marker, and the error sink must have rendered a real Python traceback (ANSIBLE_DISPLAY_TRACEBACK=always),
#   proving the traceback egress path ran; the plaintext scan already guarantees nothing in it leaked.
assert_masked() {
    local file="$1" secret marker

    for secret in "${registered_secrets[@]}"; do
        if grep -q -- "${secret}" "${file}"; then
            echo "FAIL: registered secret '${secret}' leaked in plaintext (${file})" >&2
            grep -n -- "${secret}" "${file}" >&2 || true
            exit 1
        fi
    done

    for marker in "${sink_markers[@]}"; do
        if ! grep -qF -- "${marker}" "${file}"; then
            echo "FAIL: expected redacted marker not found: '${marker}' (${file})" >&2
            exit 1
        fi
    done

    if ! grep -qF -- "Traceback (most recent call last):" "${file}"; then
        echo "FAIL: expected a rendered traceback (ANSIBLE_DISPLAY_TRACEBACK=always) but found none (${file})" >&2
        exit 1
    fi
}

# stdout/stderr captured from the run
assert_masked "${LOG}"

# The ANSIBLE_LOG_PATH file is fed by the same Display sinks and must be masked in the same way.
cat "${ANSIBLE_LOG}"
assert_masked "${ANSIBLE_LOG}"
