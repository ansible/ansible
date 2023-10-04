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

from __future__ import annotations

from ansible.utils.color import stringc
import requests
import sys
import datetime

# Following changes should be made to improve the overall style:
# TODO use argparse for arguments.
# TODO use new style formatting method.
# TODO use requests session.
# TODO type hints.

BRANCH = 'devel'
PIPELINE_ID = 20
MAX_AGE = datetime.timedelta(hours=24)

if len(sys.argv) > 1:
    BRANCH = sys.argv[1]


def get_coverage_runs():
    list_response = requests.get("https://dev.azure.com/ansible/ansible/_apis/pipelines/%s/runs?api-version=6.0-preview.1" % PIPELINE_ID)
    list_response.raise_for_status()

    runs = list_response.json()

    coverage_runs = []
    for run_summary in runs["value"][0:1000]:
        run_response = requests.get(run_summary['url'])

        if run_response.status_code == 500 and 'Cannot serialize type Microsoft.Azure.Pipelines.WebApi.ContainerResource' in run_response.json()['message']:
            # This run used a container resource, which AZP can no longer serialize for anonymous requests.
            # Assume all older requests have this issue as well and stop further processing of runs.
            # The issue was reported here: https://developercommunity.visualstudio.com/t/Pipelines-API-serialization-error-for-an/10294532
            # A work-around for this issue was applied in: https://github.com/ansible/ansible/pull/80299
            break

        run_response.raise_for_status()
        run = run_response.json()

        if run['resources']['repositories']['self']['refName'] != 'refs/heads/%s' % BRANCH:
            continue

        if 'finishedDate' in run_summary:
            age = datetime.datetime.now() - datetime.datetime.strptime(run['finishedDate'].split(".")[0], "%Y-%m-%dT%H:%M:%S")
            if age > MAX_AGE:
                break

        artifact_response = requests.get("https://dev.azure.com/ansible/ansible/_apis/build/builds/%s/artifacts?api-version=6.0" % run['id'])
        artifact_response.raise_for_status()

        artifacts = artifact_response.json()['value']
        if any(a["name"].startswith("Coverage") for a in artifacts):
            # TODO wrongfully skipped if all jobs failed.
            coverage_runs.append(run)

    return coverage_runs


def pretty_coverage_runs(runs):
    ended = []
    in_progress = []
    for run in runs:
        if run.get('finishedDate'):
            ended.append(run)
        else:
            in_progress.append(run)

    for run in sorted(ended, key=lambda x: x['finishedDate']):
        if run['result'] == "succeeded":
            print('🙂 [%s] https://dev.azure.com/ansible/ansible/_build/results?buildId=%s (%s)' % (
                stringc('PASS', 'green'),
                run['id'],
                run['finishedDate']))
        else:
            print('😢 [%s] https://dev.azure.com/ansible/ansible/_build/results?buildId=%s (%s)' % (
                stringc('FAIL', 'red'),
                run['id'],
                run['finishedDate']))

    if in_progress:
        print('The following runs are ongoing:')
        for run in in_progress:
            print('🤔 [%s] https://dev.azure.com/ansible/ansible/_build/results?buildId=%s' % (
                stringc('FATE', 'yellow'),
                run['id']))


def main():
    pretty_coverage_runs(get_coverage_runs())


if __name__ == '__main__':
    main()
