#!/usr/bin/env bash
# Check the test results and set variables for use in later steps.

set -o pipefail -eu

if [[ "$PWD" =~ /ansible_collections/ ]]; then
    output_path="tests/output"
else
    output_path="test/results"
fi

echo "##vso[task.setVariable variable=outputPath]${output_path}"

if compgen -G "${output_path}"'/junit/*.xml' > /dev/null; then
    echo "##vso[task.setVariable variable=haveTestResults]true"
fi

if compgen -G "${output_path}"'/bot/ansible-test-*' > /dev/null; then
    echo "##vso[task.setVariable variable=haveBotResults]true"
fi

if compgen -G "${output_path}"'/coverage/*' > /dev/null; then
    echo "##vso[task.setVariable variable=haveCoverageData]true"
fi
