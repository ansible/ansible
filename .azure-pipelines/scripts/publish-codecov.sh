#!/usr/bin/env bash
# Upload code coverage reports to codecov.io.
# Multiple coverage files from multiple languages are accepted and aggregated after upload.
# Python coverage, as well as PowerShell and Python stubs can all be uploaded.

set -o pipefail -eu

output_path="$1"

curl --silent --show-error https://ansible-ci-files.s3.us-east-1.amazonaws.com/codecov/codecov.sh > codecov.sh

for file in "${output_path}"/reports/coverage*.xml; do
    name="${file}"
    name="${name##*/}"  # remove path
    name="${name##coverage=}"  # remove 'coverage=' prefix if present
    name="${name%.xml}"  # remove '.xml' suffix

    bash codecov.sh \
        -f "${file}" \
        -n "${name}" \
        -X coveragepy \
        -X gcov \
        -X fix \
        -X search \
        -X xcode \
        || echo "Failed to upload code coverage report to codecov.io: ${file}"
done
