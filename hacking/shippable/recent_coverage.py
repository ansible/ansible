#!/usr/bin/env python

# (c) 2021 Red Hat, Inc.
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

from ansible.utils.color import stringc
import requests
import pathlib
import argparse
import datetime
import argcomplete

parser = argparse.ArgumentParser(description='Retrieve URLs of recent coverage test runs.')
parser.add_argument('--ref', help='restrict job to be run on a git ref')
parser.add_argument('--pipeline', default="20", help='pipeline to search in')
parser.add_argument('--latest', type=int, default=24, help='do not include runs that finished earlier than x hours ago')
argcomplete.autocomplete(parser)

def main():
    args = parser.parse_args()
    try:
        print_runs(args.pipeline, args.ref, args.latest)
    except KeyboardInterrupt:
        pass

def print_runs(pipeline: str, ref: str, latest: int):
    s = requests.Session()
    summary_response = s.get(f"https://dev.azure.com/ansible/ansible/_apis/pipelines/{pipeline}/runs?api-version=6.0-preview.1")
    summary_response.raise_for_status()

    for run_summary in summary_response.json()["value"][0:200]:
        run_response = s.get(run_summary['url'])
        run_response.raise_for_status()
        run = run_response.json()

        if ref and run['resources']['repositories']['self']['refName'] != f'refs/heads/{ref}':
            continue

        if 'finishedDate' in run_summary:
            dt = datetime.datetime.strptime(run['finishedDate'].split(".")[0], "%Y-%m-%dT%H:%M:%S")
            elapsed = datetime.datetime.now() - dt
            if elapsed.total_seconds()/60/60 > latest:
                return

        artifact_response = s.get(f"https://dev.azure.com/ansible/ansible/_apis/build/builds/{run['id']}/artifacts?api-version=6.0")
        artifact_response.raise_for_status()

        artifacts = artifact_response.json()['value']
        if not any([a["name"].startswith("Coverage") for a in artifacts]):
            # TODO wrongfully skipped if all jobs failed. 
            continue

        if run['state'] != 'completed':
            print(f"🤔 [{stringc('FATE', 'yellow')}] {run['id']}")
        elif run['result'] == 'succeeded':
            print(f"🙂 [{stringc('PASS', 'green')}] {run['id']} @ {run['finishedDate']}")
        else:
            print(f"😢 [{stringc('FAIL', 'red')}] {run['id']} @ {run['finishedDate']}")

if __name__ == '__main__':
    main()
