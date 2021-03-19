#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

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

"""CLI tool for downloading results from Shippable CI runs."""

import argparse
import zipfile
import requests
import io
import pathlib
import json
import argcomplete

def download_coverage(destination: pathlib.Path,  pipeline_id: str, build_id: str):
    s = requests.Session()
    run_info_response = s.get(f'https://dev.azure.com/ansible/ansible/_apis/pipelines/{pipeline_id}/runs/{build_id}?api-version=6.0-preview.1 ')
    run_info_response.raise_for_status()
    run_info = run_info_response.json()
    destination = destination/build_id
    destination.mkdir(parents=True, exist_ok=True)
    meta = {
        "git_object": run_info["resources"]["repositories"]["self"]["version"],
        "build_id": build_id,
    }
    (destination/"meta.json").open("wt").write(json.dumps(meta)+'\n')

    artifact_list_response = s.get(f'https://dev.azure.com/ansible/ansible/_apis/build/builds/{build_id}/artifacts?api-version=6.0')
    artifact_list_response.raise_for_status()
    for artifact in artifact_list_response.json()['value']:
        name = artifact['name']
        print(f"downloading `{name}`")
        response = s.get(artifact['resource']['downloadUrl'])
        response.raise_for_status()
        archive = zipfile.ZipFile(io.BytesIO(response.content))
        archive.extractall(path=destination)

parser = argparse.ArgumentParser(description='download coverage reports from CI')
parser.add_argument('build', help="build ID to fetch the report from.")
parser.add_argument('--dest', type=pathlib.Path, default=pathlib.Path(__file__).resolve().parent/"coverage",
                    help="destination directory where coverage files will be dumped in. Will be created if not existing.")
parser.add_argument('--pipeline', default="20", help='pipeline to search in')
argcomplete.autocomplete(parser)

def main():
    args = parser.parse_args()
    download_coverage(args.dest, args.pipeline, args.build)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
