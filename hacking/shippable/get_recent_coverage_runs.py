#!/usr/bin/env python

# (c) 2020 Red Hat, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.utils.color import stringc
import requests
import sys

BRANCH = 'devel'

if len(sys.argv) > 1:
    BRANCH = sys.argv[1]


def get_coverage_runs():
    response = requests.get(
        'https://api.shippable.com/runs?projectIds=573f79d02a8192902e20e34b'
        '&branch=%s&limit=1000' % BRANCH)

    if response.status_code != 200:
        raise Exception(response.content)

    runs = response.json()

    coverage_runs = []
    criteria = ['COMPLETE="yes"', 'COVERAGE="yes"']

    for run in runs:
        injected_vars = run.get('cleanRunYml', {}).get('env', {}).get('injected')
        if not injected_vars:
            continue
        if all(criterion in injected_vars for criterion in criteria):
            coverage_runs.append(run)

    return coverage_runs


def pretty_coverage_runs(runs):
    ended = []
    in_progress = []
    for run in runs:
        if run.get('endedAt'):
            ended.append(run)
        else:
            in_progress.append(run)

    for run in sorted(ended, key=lambda x: x['endedAt']):
        if run['statusCode'] == 30:
            print('🙂 [%s] https://app.shippable.com/github/ansible/ansible/runs/%s (%s)' % (
                stringc('PASS', 'green'),
                run['runNumber'],
                run['endedAt']))
        else:
            print('😢 [%s] https://app.shippable.com/github/ansible/ansible/runs/%s (%s)' % (
                stringc('FAIL', 'red'),
                run['runNumber'],
                run['endedAt']))

    if in_progress:
        print('The following runs are ongoing:')
        for run in in_progress:
            print('🤔 [%s] https://app.shippable.com/github/ansible/ansible/runs/%s' % (
                stringc('FATE', 'yellow'),
                run['runNumber']))


def main():
    pretty_coverage_runs(get_coverage_runs())


if __name__ == '__main__':
    main()
