#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

# (c) 2016 Red Hat, Inc.
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
"""CLI tool for downloading results from Shippable CI runs."""

from __future__ import print_function

# noinspection PyCompatibility
import argparse
import json
import os
import re
import requests

try:
    import argcomplete
except ImportError:
    argcomplete = None


def main():
    """Main program body."""
    api_key = get_api_key()

    parser = argparse.ArgumentParser(description='Download results from a Shippable run.')

    parser.add_argument('run_id',
                        metavar='RUN',
                        help='shippable run id, run url or run name formatted as: account/project/run_number')

    parser.add_argument('-v', '--verbose',
                        dest='verbose',
                        action='store_true',
                        help='show what is being downloaded')

    parser.add_argument('-t', '--test',
                        dest='test',
                        action='store_true',
                        help='show what would be downloaded without downloading')

    parser.add_argument('--key',
                        dest='api_key',
                        default=api_key,
                        required=api_key is None,
                        help='api key for accessing Shippable')

    parser.add_argument('--console-logs',
                        action='store_true',
                        help='download console logs')

    parser.add_argument('--test-results',
                        action='store_true',
                        help='download test results')

    parser.add_argument('--coverage-results',
                        action='store_true',
                        help='download code coverage results')

    parser.add_argument('--job-metadata',
                        action='store_true',
                        help='download job metadata')

    parser.add_argument('--run-metadata',
                        action='store_true',
                        help='download run metadata')

    parser.add_argument('--all',
                        action='store_true',
                        help='download everything')

    parser.add_argument('--job-number',
                        metavar='N',
                        action='append',
                        type=int,
                        help='limit downloads to the given job number')

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    old_runs_prefix = 'https://app.shippable.com/runs/'

    if args.run_id.startswith(old_runs_prefix):
        args.run_id = args.run_id[len(old_runs_prefix):]

    if args.all:
        args.console_logs = True
        args.test_results = True
        args.coverage_results = True
        args.job_metadata = True
        args.run_metadata = True

    selections = (
        args.console_logs,
        args.test_results,
        args.coverage_results,
        args.job_metadata,
        args.run_metadata,
    )

    if not any(selections):
        parser.error('At least one download option is required.')

    headers = dict(
        Authorization='apiToken %s' % args.api_key,
    )

    match = re.search(
        r'^https://app.shippable.com/github/(?P<account>[^/]+)/(?P<project>[^/]+)/runs/(?P<run_number>[0-9]+)(?:/summary|(/(?P<job_number>[0-9]+)))?$',
        args.run_id)

    if not match:
        match = re.search(r'^(?P<account>[^/]+)/(?P<project>[^/]+)/(?P<run_number>[0-9]+)$', args.run_id)

    if match:
        account = match.group('account')
        project = match.group('project')
        run_number = int(match.group('run_number'))
        job_number = int(match.group('job_number')) if match.group('job_number') else None

        if job_number:
            if args.job_number:
                exit('ERROR: job number found in url and specified with --job-number')

            args.job_number = [job_number]

        url = 'https://api.shippable.com/projects'
        response = requests.get(url, dict(projectFullNames='%s/%s' % (account, project)), headers=headers)

        if response.status_code != 200:
            raise Exception(response.content)

        project_id = response.json()[0]['id']

        url = 'https://api.shippable.com/runs?projectIds=%s&runNumbers=%s' % (project_id, run_number)

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(response.content)

        run = [run for run in response.json() if run['runNumber'] == run_number][0]

        args.run_id = run['id']
    elif re.search('^[a-f0-9]+$', args.run_id):
        url = 'https://api.shippable.com/runs/%s' % args.run_id

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(response.content)

        run = response.json()

        account = run['subscriptionOrgName']
        project = run['projectName']
        run_number = run['runNumber']
    else:
        exit('ERROR: invalid run: %s' % args.run_id)

    output_dir = '%s/%s/%s' % (account, project, run_number)

    response = requests.get('https://api.shippable.com/jobs?runIds=%s' % args.run_id, headers=headers)

    if response.status_code != 200:
        raise Exception(response.content)

    jobs = sorted(response.json(), key=lambda job: int(job['jobNumber']))

    if not args.test:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    if args.run_metadata:
        path = os.path.join(output_dir, 'run.json')
        contents = json.dumps(run, sort_keys=True, indent=4)

        if args.verbose or args.test:
            print(path)

        if not args.test:
            with open(path, 'w') as metadata_fd:
                metadata_fd.write(contents)

    for j in jobs:
        job_id = j['id']
        job_number = j['jobNumber']

        if args.job_number and job_number not in args.job_number:
            continue

        if args.job_metadata:
            path = os.path.join(output_dir, '%s/job.json' % job_number)
            contents = json.dumps(j, sort_keys=True, indent=4)

            if args.verbose or args.test:
                print(path)

            if not args.test:
                directory = os.path.dirname(path)

                if not os.path.exists(directory):
                    os.makedirs(directory)

                with open(path, 'w') as metadata_fd:
                    metadata_fd.write(contents)

        if args.console_logs:
            path = os.path.join(output_dir, '%s/console.log' % job_number)
            url = 'https://api.shippable.com/jobs/%s/consoles?download=true' % job_id
            download(args, headers, path, url, is_json=False)

        if args.test_results:
            path = os.path.join(output_dir, '%s/test.json' % job_number)
            url = 'https://api.shippable.com/jobs/%s/jobTestReports' % job_id
            download(args, headers, path, url)
            extract_contents(args, path, os.path.join(output_dir, '%s/test' % job_number))

        if args.coverage_results:
            path = os.path.join(output_dir, '%s/coverage.json' % job_number)
            url = 'https://api.shippable.com/jobs/%s/jobCoverageReports' % job_id
            download(args, headers, path, url)
            extract_contents(args, path, os.path.join(output_dir, '%s/coverage' % job_number))


def extract_contents(args, path, output_dir):
    """
    :type args: any
    :type path: str
    :type output_dir: str
    """
    if not args.test:
        if not os.path.exists(path):
            return

        with open(path, 'r') as json_fd:
            items = json.load(json_fd)

            for item in items:
                contents = item['contents'].encode('utf-8')
                path = output_dir + '/' + re.sub('^/*', '', item['path'])

                directory = os.path.dirname(path)

                if not os.path.exists(directory):
                    os.makedirs(directory)

                if args.verbose:
                    print(path)

                if path.endswith('.json'):
                    contents = json.dumps(json.loads(contents), sort_keys=True, indent=4)

                if not os.path.exists(path):
                    with open(path, 'w') as output_fd:
                        output_fd.write(contents)


def download(args, headers, path, url, is_json=True):
    """
    :type args: any
    :type headers: dict[str, str]
    :type path: str
    :type url: str
    :type is_json: bool
    """
    if args.verbose or args.test:
        print(path)

    if os.path.exists(path):
        return

    if not args.test:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            path += '.error'

        if is_json:
            content = json.dumps(response.json(), sort_keys=True, indent=4)
        else:
            content = response.content

        directory = os.path.dirname(path)

        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(path, 'w') as content_fd:
            content_fd.write(content)


def get_api_key():
    """
    rtype: str
    """
    key = os.environ.get('SHIPPABLE_KEY', None)

    if key:
        return key

    path = os.path.join(os.environ['HOME'], '.shippable.key')

    try:
        with open(path, 'r') as key_fd:
            return key_fd.read().strip()
    except IOError:
        return None


if __name__ == '__main__':
    main()
