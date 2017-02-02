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

from __future__ import print_function

import json
import os
import re
import requests

from argparse import ArgumentParser

try:
    import argcomplete
except ImportError:
    argcomplete = None


def main():
    api_key = get_api_key()

    parser = ArgumentParser(description='Download results from a Shippable run.')

    parser.add_argument('run_id',
                        help='shippable run id.')

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

    parser.add_argument('--all',
                        action='store_true',
                        help='download everything')

    parser.add_argument('--job-number',
                        action='append',
                        type=int,
                        help='limit downloads to the given job number')

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    if args.all:
        args.console_logs = True
        args.test_results = True
        args.coverage_results = True

    if not args.console_logs and not args.test_results and not args.coverage_results:
        parser.error('At least one download option is required: --console-logs, --test-results, --coverage-results')

    headers = dict(
        Authorization='apiToken %s' % args.api_key,
    )

    response = requests.get('https://api.shippable.com/jobs?runIds=%s' % args.run_id, headers=headers)

    if response.status_code != 200:
        raise Exception(response.content)

    body = response.json()
    output_dir = args.run_id

    if not args.test:
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

    for j in body:
        job_id = j['id']
        job_number = j['jobNumber']

        if args.job_number and job_number not in args.job_number:
            continue

        if args.console_logs:
            path = os.path.join(output_dir, '%s-console.log' % job_number)
            url = 'https://api.shippable.com/jobs/%s/consoles?download=true' % job_id
            download(args, headers, path, url)

        if args.test_results:
            path = os.path.join(output_dir, '%s-test.json' % job_number)
            url = 'https://api.shippable.com/jobs/%s/jobTestReports' % job_id
            download(args, headers, path, url)
            extract_contents(args, path, os.path.join(output_dir, '%s-test' % job_number))

        if args.coverage_results:
            path = os.path.join(output_dir, '%s-coverage.json' % job_number)
            url = 'https://api.shippable.com/jobs/%s/jobCoverageReports' % job_id
            download(args, headers, path, url)
            extract_contents(args, path, os.path.join(output_dir, '%s-coverage' % job_number))


def extract_contents(args, path, output_dir):
    if not args.test:
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

                if not os.path.exists(path):
                    with open(path, 'w') as output_fd:
                        output_fd.write(contents)


def download(args, headers, path, url):
    if args.verbose or args.test:
        print(path)

    if os.path.exists(path):
        return

    if not args.test:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(response.content)

        content = response.content

        with open(path, 'w') as f:
            f.write(content)


def get_api_key():
    path = os.path.join(os.environ['HOME'], '.shippable.key')

    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except IOError:
        return None


if __name__ == '__main__':
    main()
