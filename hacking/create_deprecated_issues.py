#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2017, Matt Martz <matt@sivel.net>
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

import argparse
import os
import sys
import time

from collections import defaultdict

from ansible.release import __version__ as ansible_version

ansible_major_version = '.'.join(ansible_version.split('.')[:2])

try:
    from github3 import GitHub
except ImportError:
    raise SystemExit(
        'This script needs the github3.py library installed to work'
    )

if not os.getenv('GITHUB_TOKEN'):
    raise SystemExit(
        'Please set the GITHUB_TOKEN env var with your github oauth token with public_repo scope'
    )


def main():
    deprecated = defaultdict(list)

    parser = argparse.ArgumentParser()
    parser.add_argument('--template', default='deprecated_issue_template.md',
                        type=argparse.FileType('r'),
                        help='Path to markdown file template to be used for issue '
                             'body. Default: %(default)s')
    parser.add_argument('--project-name', default='', type=str,
                        help='Name of a github project to assign all issues to')
    parser.add_argument('problems', nargs=1, type=argparse.FileType('r'),
                        help='Path to file containing pylint output for the '
                             'ansible-deprecated-version check')
    args = parser.parse_args()

    body_tmpl = args.template.read()
    args.template.close()

    text = args.problems[0].read()
    args.problems[0].close()

    project_name = args.project_name.strip().lower()

    for line in text.splitlines():
        path = line.split(':')[0]
        if path.endswith('__init__.py'):
            component = os.path.basename(os.path.dirname(path))
        else:
            component, dummy = os.path.splitext(os.path.basename(path).lstrip('_'))

        title = (
            '%s contains deprecated call to be removed in %s' %
            (component, ansible_major_version)
        )
        deprecated[component].append(
            dict(title=title, path=path, line=line)
        )

    gh_conn = GitHub(token=os.getenv('GITHUB_TOKEN'))
    repo = gh_conn.repository('ansible', 'ansible')

    if project_name:
        project = None
        for project in repo.projects():
            if project.name.lower() == project_name:
                break
        else:
            print('%s was an invalid project name' % project_name)
            sys.exit(1)

        project_column = None
        for project_column in project.columns():
            if 'todo' in project_column.name.lower() or 'backlog' in project_column.name.lower():
                break
        else:
            print('unable to determine the todo column in the project.')
            sys.exit(2)

    for component, items in deprecated.items():
        title = items[0]['title']
        path = '\n'.join(set((i['path']) for i in items))
        line = '\n'.join(i['line'] for i in items)
        body = body_tmpl % dict(component=component, path=path,
                                line=line,
                                version=ansible_major_version)

        issue = repo.create_issue(title, body=body, labels=['deprecated'])
        print(issue)
        # Sleep a little, so that the API doesn't block us
        time.sleep(0.5)

        if project_column:
            project_column.create_card_with_issue(issue)
            time.sleep(0.5)


if __name__ == '__main__':
    main()
