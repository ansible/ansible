#!/usr/bin/env bash
# Secret-masking Display-egress tests: a registered secret must be masked at every controller
# Display() boundary (banner, warning, deprecation, invocation dump, error). Secrets are
# pre-seeded via the _SECRETS_INPUT_FILES config so they are registered before any sink runs.

set -eux -o pipefail

LOG="${OUTPUT_DIR}/display.log"

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
    ansible-playbook display.yml -i ../../inventory -vvv "$@" 2>&1 | tee "${LOG}"

# No registered plaintext secret may appear anywhere in the captured output.
registered_secrets=(
    Displaywarn0050Secret
    Displaydeprec0051Secret
    Displaybanner0052Secret
    Displayerror0053Secret
    Displayinvoke0054Secret
    Displayline0055Secret
)
for secret in "${registered_secrets[@]}"; do
    if grep -q -- "${secret}" "${LOG}"; then
        echo "FAIL: registered secret '${secret}' leaked in plaintext" >&2
        grep -n -- "${secret}" "${LOG}" >&2 || true
        exit 1
    fi
done

# Each sink must have run and emitted a redacted marker.
sink_markers=(
    "SCNBANNER \$REDACTED\$"
    "SCNWARN \$REDACTED\$"
    "SCNDEPR \$REDACTED\$"
    "SCNINVOKE \$REDACTED\$"
    "SCNERROR \$REDACTED\$"
    "SCNLINE \$REDACTED\$"
)
for marker in "${sink_markers[@]}"; do
    if ! grep -qF -- "${marker}" "${LOG}"; then
        echo "FAIL: expected redacted marker not found: '${marker}'" >&2
        exit 1
    fi
done
