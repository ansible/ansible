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

"""CLI tool for starting new CI runs."""

from __future__ import annotations

# noinspection PyCompatibility
import argparse
import json
import os
import sys
import requests
import requests.auth

try:
    import argcomplete
except ImportError:
    argcomplete = None

# TODO: Dev does not have a token for AZP, somebody please test this.

# Following changes should be made to improve the overall style:
# TODO use new style formatting method.
# TODO type hints.


def main():
    """Main program body."""

    args = parse_args()

    key = os.environ.get('AZP_TOKEN', None)
    if not key:
        sys.stderr.write("please set you AZP token in AZP_TOKEN")
        sys.exit(1)

    start_run(args, key)


def parse_args():
    """Parse and return args."""

    parser = argparse.ArgumentParser(description='Start a new CI run.')

    parser.add_argument('-p', '--pipeline-id', type=int, default=20, help='pipeline to download the job from')
    parser.add_argument('--ref', help='git ref name to run on')

    parser.add_argument('--env',
                        nargs=2,
                        metavar=('KEY', 'VALUE'),
                        action='append',
                        help='environment variable to pass')

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    return args


def start_run(args, key):
    """Start a new CI run."""

    url = "https://dev.azure.com/ansible/ansible/_apis/pipelines/%s/runs?api-version=6.0-preview.1" % args.pipeline_id
    payload = {"resources": {"repositories": {"self": {"refName": args.ref}}}}

    resp = requests.post(url, auth=requests.auth.HTTPBasicAuth('user', key), data=payload)
    resp.raise_for_status()

    print(json.dumps(resp.json(), indent=4, sort_keys=True))


if __name__ == '__main__':
    main()
