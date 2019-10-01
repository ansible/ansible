#!/usr/bin/env python
"""Verify the currently executing Shippable test matrix matches the one defined in the "shippable.yml" file."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import json
import os
import re
import sys
import time

try:
    from typing import NoReturn
except ImportError:
    NoReturn = None

try:
    # noinspection PyCompatibility
    from urllib2 import urlopen  # pylint: disable=ansible-bad-import-from
except ImportError:
    # noinspection PyCompatibility
    from urllib.request import urlopen


def main():  # type: () -> None
    """Main entry point."""
    repo_full_name = os.environ['REPO_FULL_NAME']
    required_repo_full_name = 'ansible/ansible'

    if repo_full_name != required_repo_full_name:
        sys.stderr.write('Skipping matrix check on repo "%s" which is not "%s".\n' % (repo_full_name, required_repo_full_name))
        return

    with open('shippable.yml', 'rb') as yaml_file:
        yaml = yaml_file.read().decode('utf-8').splitlines()

    defined_matrix = [match.group(1) for match in [re.search(r'^ *- env: T=(.*)$', line) for line in yaml] if match and match.group(1) != 'none']

    if not defined_matrix:
        fail('No matrix entries found in the "shippable.yml" file.',
             'Did you modify the "shippable.yml" file?')

    run_id = os.environ['SHIPPABLE_BUILD_ID']
    sleep = 1
    jobs = []

    for attempts_remaining in range(4, -1, -1):
        try:
            jobs = json.loads(urlopen('https://api.shippable.com/jobs?runIds=%s' % run_id).read())

            if not isinstance(jobs, list):
                raise Exception('Shippable run %s data is not a list.' % run_id)

            break
        except Exception as ex:
            if not attempts_remaining:
                fail('Unable to retrieve Shippable run %s matrix.' % run_id,
                     str(ex))

            sys.stderr.write('Unable to retrieve Shippable run %s matrix: %s\n' % (run_id, ex))
            sys.stderr.write('Trying again in %d seconds...\n' % sleep)
            time.sleep(sleep)
            sleep *= 2

    if len(jobs) != len(defined_matrix):
        if len(jobs) == 1:
            hint = '\n\nMake sure you do not use the "Rebuild with SSH" option.'
        else:
            hint = ''

        fail('Shippable run %s has %d jobs instead of the expected %d jobs.' % (run_id, len(jobs), len(defined_matrix)),
             'Try re-running the entire matrix.%s' % hint)

    actual_matrix = dict((job.get('jobNumber'), dict(tuple(line.split('=', 1)) for line in job.get('env', [])).get('T', '')) for job in jobs)
    errors = [(job_number, test, actual_matrix.get(job_number)) for job_number, test in enumerate(defined_matrix, 1) if actual_matrix.get(job_number) != test]

    if len(errors):
        error_summary = '\n'.join('Job %s expected "%s" but found "%s" instead.' % (job_number, expected, actual) for job_number, expected, actual in errors)

        fail('Shippable run %s has a job matrix mismatch.' % run_id,
             'Try re-running the entire matrix.\n\n%s' % error_summary)


def fail(message, output):  # type: (str, str) -> NoReturn
    # Include a leading newline to improve readability on Shippable "Tests" tab.
    # Without this, the first line becomes indented.
    output = '\n' + output.strip()

    timestamp = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

    # hack to avoid requiring junit-xml, which isn't pre-installed on Shippable outside our test containers
    xml = '''
<?xml version="1.0" encoding="utf-8"?>
<testsuites disabled="0" errors="1" failures="0" tests="1" time="0.0">
\t<testsuite disabled="0" errors="1" failures="0" file="None" log="None" name="ansible-test" skipped="0" tests="1" time="0" timestamp="%s" url="None">
\t\t<testcase classname="timeout" name="timeout">
\t\t\t<error message="%s" type="error">%s</error>
\t\t</testcase>
\t</testsuite>
</testsuites>
''' % (timestamp, message, output)

    with open('test/results/junit/check-matrix.xml', 'w') as junit_fd:
        junit_fd.write(xml.lstrip())

    sys.stderr.write(message + '\n')
    sys.stderr.write(output + '\n')

    sys.exit(1)


if __name__ == '__main__':
    main()
