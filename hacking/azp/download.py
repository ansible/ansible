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
"""CLI tool for downloading results from Azure Pipelines CI runs."""

from __future__ import annotations

# noinspection PyCompatibility
import argparse
import json
import os
import re
import io
import zipfile

import requests

try:
    import argcomplete
except ImportError:
    argcomplete = None

# Following changes should be made to improve the overall style:
# TODO use new style formatting method.
# TODO use requests session.
# TODO type hints.
# TODO pathlib.


def main():
    """Main program body."""

    args = parse_args()
    download_run(args)


def run_id_arg(arg):
    m = re.fullmatch(r"(?:https:\/\/dev\.azure\.com\/ansible\/ansible\/_build\/results\?buildId=)?(\d+)", arg)
    if not m:
        raise ValueError("run does not seems to be a URI or an ID")
    return m.group(1)


def parse_args():
    """Parse and return args."""

    parser = argparse.ArgumentParser(description='Download results from a CI run.')

    parser.add_argument('run', metavar='RUN', type=run_id_arg, help='AZP run id or URI')

    parser.add_argument('-v', '--verbose',
                        dest='verbose',
                        action='store_true',
                        help='show what is being downloaded')

    parser.add_argument('-t', '--test',
                        dest='test',
                        action='store_true',
                        help='show what would be downloaded without downloading')

    parser.add_argument('-p', '--pipeline-id', type=int, default=20, help='pipeline to download the job from')

    parser.add_argument('--artifacts',
                        action='store_true',
                        help='download artifacts')

    parser.add_argument('--console-logs',
                        action='store_true',
                        help='download console logs')

    parser.add_argument('--run-metadata',
                        action='store_true',
                        help='download run metadata')

    parser.add_argument('--all',
                        action='store_true',
                        help='download everything')

    parser.add_argument('--match-artifact-name',
                        default=re.compile('.*'),
                        type=re.compile,
                        help='only download artifacts which names match this regex')

    parser.add_argument('--match-job-name',
                        default=re.compile('.*'),
                        type=re.compile,
                        help='only download artifacts from jobs which names match this regex')

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    if args.all:
        args.artifacts = True
        args.run_metadata = True
        args.console_logs = True

    selections = (
        args.artifacts,
        args.run_metadata,
        args.console_logs
    )

    if not any(selections):
        parser.error('At least one download option is required.')

    return args


def download_run(args):
    """Download a run."""

    output_dir = '%s' % args.run

    if not args.test and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if args.run_metadata:
        run_url = 'https://dev.azure.com/ansible/ansible/_apis/pipelines/%s/runs/%s?api-version=6.0-preview.1' % (args.pipeline_id, args.run)
        run_info_response = requests.get(run_url)
        run_info_response.raise_for_status()
        run = run_info_response.json()

        path = os.path.join(output_dir, 'run.json')
        contents = json.dumps(run, sort_keys=True, indent=4)

        if args.verbose:
            print(path)

        if not args.test:
            with open(path, 'w') as metadata_fd:
                metadata_fd.write(contents)

    timeline_response = requests.get('https://dev.azure.com/ansible/ansible/_apis/build/builds/%s/timeline?api-version=6.0' % args.run)
    timeline_response.raise_for_status()
    timeline = timeline_response.json()
    roots = set()
    by_id = {}
    children_of = {}
    parent_of = {}
    for r in timeline['records']:
        thisId = r['id']
        parentId = r['parentId']

        by_id[thisId] = r

        if parentId is None:
            roots.add(thisId)
        else:
            parent_of[thisId] = parentId
            children_of[parentId] = children_of.get(parentId, []) + [thisId]

    allowed = set()

    def allow_recursive(ei):
        allowed.add(ei)
        for ci in children_of.get(ei, []):
            allow_recursive(ci)

    for ri in roots:
        r = by_id[ri]
        allowed.add(ri)
        for ci in children_of.get(r['id'], []):
            c = by_id[ci]
            if not args.match_job_name.match("%s %s" % (r['name'], c['name'])):
                continue
            allow_recursive(c['id'])

    if args.artifacts:
        artifact_list_url = 'https://dev.azure.com/ansible/ansible/_apis/build/builds/%s/artifacts?api-version=6.0' % args.run
        artifact_list_response = requests.get(artifact_list_url)
        artifact_list_response.raise_for_status()
        for artifact in artifact_list_response.json()['value']:
            if artifact['source'] not in allowed or not args.match_artifact_name.match(artifact['name']):
                continue
            if args.verbose:
                print('%s/%s' % (output_dir, artifact['name']))
            if not args.test:
                response = requests.get(artifact['resource']['downloadUrl'])
                response.raise_for_status()
                archive = zipfile.ZipFile(io.BytesIO(response.content))
                archive.extractall(path=output_dir)

    if args.console_logs:
        for r in timeline['records']:
            if not r['log'] or r['id'] not in allowed or not args.match_artifact_name.match(r['name']):
                continue
            names = []
            parent_id = r['id']
            while parent_id is not None:
                p = by_id[parent_id]
                name = p['name']
                if name not in names:
                    names = [name] + names
                parent_id = parent_of.get(p['id'], None)

            path = " ".join(names)

            # Some job names have the separator in them.
            path = path.replace(os.sep, '_')

            log_path = os.path.join(output_dir, '%s.log' % path)
            if args.verbose:
                print(log_path)
            if not args.test:
                log = requests.get(r['log']['url'])
                log.raise_for_status()
                open(log_path, 'wb').write(log.content)


if __name__ == '__main__':
    main()
