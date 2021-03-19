#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

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

"""CLI tool for reporting on incidental test coverage."""

import argparse
import json
import re
import subprocess
import sys
import hashlib
import pathlib
import typing
import re
import dataclasses
import argcomplete

parser = argparse.ArgumentParser(description='Report on incidental test coverage downloaded from CI.')

parser.add_argument('download', type=pathlib.Path, help='directory that was downloaded with the download script')
parser.add_argument('--output', type=pathlib.Path, default=pathlib.Path(".")/"incidental",
                    help='path to directory where reports should be written')
parser.add_argument('--repo', type=pathlib.Path, default=pathlib.Path("./../.."),
                    help='path to git repository containing Ansible source')
target_arg = parser.add_mutually_exclusive_group()
target_arg.add_argument('--target', type=re.compile, default=re.compile(r'^incidental_'),
                    help='regex for targets to analyze, default: %(default)s')
target_arg.add_argument('--plugin-path', type=pathlib.Path, help='path to plugin to report incidental coverage on')
argcomplete.autocomplete(parser)

ANALYSE_COMMAND = ('ansible-test', 'coverage', 'analyze', 'targets')

class Error(Exception):
    pass

def get_target_name_from_plugin_path(path: pathlib.Path):
    plugin_name = path.stem

    if path.is_relative_to('lib/ansible/modules/'):
        return plugin_name
    elif path.is_relative_to('lib/ansible/plugins/'):
        return f"{path.parts[3]}_{plugin_name}"
    elif path.is_relative_to('lib/ansible/module_utils/'):
        return f"module_utils_{plugin_name}"
    elif path.is_relative_to('plugins/'):
        return f"{path.parts[1]}_{plugin_name}"
    raise Error(f"Cannot determine plugin type from plugin path: {path}")

@dataclasses.dataclass
class Target:
    pattern: str
    missing: bool = False
    name: str = None
    include_path: pathlib.Path = None
    cache_path_format: str = "{}"

@dataclasses.dataclass
class Paths:
    repo: pathlib.Path 
    data: pathlib.Path
    reports: pathlib.Path
    combined: pathlib.Path
    coverage_paths: tuple[pathlib.Path]

    def git_show(self, *args):
        return subprocess.check_output(("git", "show")+args, cwd=self.repo)

def inc(args: argparse.Namespace):
    meta = json.load((args.download/"meta.json").open())
    p = paths(meta, args.repo, args.download, args.output)
    target = Target(pattern=args.target)
    if args.plugin_path:
        target.cache_path_format = f"{{}}-for-{args.plugin_path.stem}"
        target.target_name = get_target_name_from_plugin_path(args.plugin_path)
        target.pattern = f'^{target.name}$'
        target.include_path = args.plugin_path
        target.missing = True
    incidental_report(meta, p, target)

def paths(meta: dict[str, str], repo: pathlib.Path, download: pathlib.Path, output: pathlib.Path):
    # TODO files need to be absolute for ansible-test
    download = download.resolve()
    output = output.resolve()
    repo = repo.resolve()

    coverage_paths = list(download.glob("*/coverage-analyze-targets.json"))
    coverage_paths.sort()

    path_hash = hashlib.sha256(b'\n'.join(str(p).encode() for p in coverage_paths)).hexdigest()
    output = output/path_hash
    paths = Paths(repo=repo, data=output/'data', reports=output/'reports', combined=output/'combined.json', coverage_paths=coverage_paths)
    paths.data.mkdir(parents=True, exist_ok=True)    
    paths.reports.mkdir(parents=True, exist_ok=True)

    try:
        paths.git_show(meta['git_object'], '--')
    except subprocess.CalledProcessError:
        raise Error(f"{repo}: commit {meta['git_object']} not found. Make sure your source repository is up-to-date")

    if not coverage_paths:
        raise Error("no coverage data found. make sure the downloaded results are from a code coverage run on Shippable")

    

    subprocess.check_call((ANALYSE_COMMAND+('combine',)+tuple(coverage_paths[0:1])+(paths.combined,)))

    return paths

def incidental_report(meta: dict[str, str], paths: Paths, target: Target):
    # identify integration test targets to analyze
    combined = json.load(paths.combined.open())
    target_names = sorted(combined['targets'])
    #print(target.pattern)
    #print([tn for tn in target_names])
    incidental_target_names = [tn for tn in target_names ] # if re.search(target.pattern, tn)

    if not incidental_target_names:
        if target.name:
            # if the plugin has no tests we still want to know what coverage is missing
            incidental_target_names = [target.name]
        else:
            raise Error('no targets to analyze')

    # exclude test support plugins from analysis
    # also exclude six, which for an unknown reason reports bogus coverage lines (indicating coverage of comments)
    exclude_path = '^(test/support/|lib/ansible/module_utils/six/)'

    # process coverage for each target and then generate a report
    # save sources for generating a summary report at the end
    summary = {}
    report_paths = {}

    for target_name in incidental_target_names:
        cache_name = target.cache_path_format.format(target_name)


        filter_args = []
        if target.include_path:
            filter_args.extend(['--include-path', target.include_path])
        if exclude_path:
            filter_args.extend(['--exclude-path', exclude_path])

        only_target_path = paths.data/f"only-{cache_name}.json"
        without_target_path = paths.data/f"without-{cache_name}.json"
        
        extra_args = ('--include-target', target_name) if target_name else ()
        subprocess.check_call(ANALYSE_COMMAND + ('filter', paths.combined, only_target_path) + extra_args + tuple(filter_args))

        extra_args = ('--exclude-target', target_name) if target_name else ()
        subprocess.check_call(ANALYSE_COMMAND + ('filter', paths.combined, without_target_path) + extra_args + tuple(filter_args))

        if target.missing:
            source_target_path = missing_target_path = paths.data/f"missing-{cache_name}.json"
            coverage_missing(without_target_path, only_target_path, missing_target_path, only_gaps=True)
        else:
            source_target_path = exclusive_target_path = paths.data/f"exclusive-cache_name.json"
            coverage_missing(only_target_path, without_target_path, exclusive_target_path, only_gaps=True)

        source_expanded_target_path = source_target_path.parent/f"expanded-{source_target_path.name}"

        subprocess.check_call(ANALYSE_COMMAND + ('expand', source_target_path, source_expanded_target_path))

        sources = []
        data = json.load(source_expanded_target_path.open())
        for path_coverage in data.values():
            for path, path_data in path_coverage.items():
                sources.append(SourceFile(path, paths.git_show(f"{meta['git_object']}:{path}"), path_data))

        summary[target_name] = sources 

        txt_report_path = paths.reports/f"{cache_name}.txt"
        generate_report(meta, sources, txt_report_path, target.name, missing=target.missing)

        report_paths[target_name] = txt_report_path

    # provide a summary report of results
    for target_name in incidental_target_names:
        sources = summary[target_name]

        print(f"{target_name}: {sum(len(s.covered_arcs) for s in sources)} arcs, "
              f"{sum(len(s.covered_lines) for s in sources)} lines, {len(sources)} files - {report_paths[target_name]}")

    if not target.missing:
        sys.stderr.write('NOTE: This report shows only coverage exclusive to the reported targets. '
                         'As targets are removed, exclusive coverage on the remaining targets will increase.\n')


def coverage_missing(from_path: pathlib.Path, to_path: pathlib.Path, output: pathlib.Path, only_gaps: bool =False):
    args = ['missing', from_path, to_path, output]

    if only_gaps:
        args.append('--only-gaps')

    subprocess.check_call(ANALYSE_COMMAND + tuple(args))

@dataclasses.dataclass
class SourceFile:
    path: pathlib.Path
    lines: tuple[str]
    coverage_points: str
    covered_points: set
    covered_arcs: set
    covered_lines: set

    def __init__(self, path: pathlib.Path, source: str, coverage_points: str):
        self.path = path
        self.coverage_points = coverage_points
        self.lines = source.splitlines()

        parse = int
        is_arcs = ':' in dict(coverage_points).popitem()[0]
        if is_arcs:
            parse = lambda v: tuple(int(v) for v in v.split(':'))
        self.covered_points = set(parse(v) for v in coverage_points)
        self.covered_arcs = self.covered_points if is_arcs else None

        self.covered_lines = set(abs(p[0]) for p in self.covered_points) | set(abs(p[1]) for p in self.covered_points)


def generate_report(meta: dict[str, str], sources: list[SourceFile], report_path:pathlib.Path, target_name: str, missing: bool):
    ro = report_path.open('tw')
    ro.write(f"Target: {target_name} ({'missing' if missing else 'exclusive'} coverage)\n")
    ro.write(f"CI: https://dev.azure.com/ansible/ansible/_build/results?buildId={meta['build_id']}\n\n")

    for source in sources:
        if source.covered_arcs:
            ro.write(f"Source: {source.path} ({len(source.covered_arcs)} arcs, {len(source.covered_lines)}/{len(source.lines)} lines):\n")
            ro.write(f"GitHub: https://github.com/ansible/ansible/blob/{meta['git_object']}/{source.path}\n\n")
        else:
            ro.write(f"Source: {source.path} ({len(source.covered_lines)}/{len(source.lines)} lines)\n"),
            ro.write(f"GitHub: {source.github_url}\n\n")

        last_line_no = 0

        for line_no, line in enumerate(source.lines, start=1):
            if line_no not in source.covered_lines:
                continue

            if last_line_no and last_line_no != line_no - 1:
                ro.write("\n")

            notes = ''

            if source.covered_arcs:
                from_lines = sorted(p[0] for p in source.covered_points if abs(p[1]) == line_no)
                to_lines = sorted(p[1] for p in source.covered_points if abs(p[0]) == line_no)

                if from_lines:
                    notes += f"  ### {', '.join(str(from_line) for from_line in from_lines)} -> (here)"

                if to_lines:
                    notes += f"  ### (here) -> {', '.join(str(to_line) for to_line in to_lines)}"

            ro.write(f"{line_no}  {line}{notes}")
            last_line_no = line_no


def main():
    args = parser.parse_args()
    try:
        inc(args)
    except Error as e:
        sys.stderr.write(str(e))
        sys.stderr.write('\n')
        sys.stderr.flush()
        sys.exit(1)

if __name__ == '__main__':
    main()