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
        'Please set the GITHUB_TOKEN env var with your github oauth token'
    )

deprecated = defaultdict(list)


parser = argparse.ArgumentParser()
parser.add_argument('--template', default='deprecated_issue_template.md',
                    type=argparse.FileType('r'),
                    help='Path to markdown file template to be used for issue '
                         'body. Default: %(default)s')
parser.add_argument('problems', nargs=1, type=argparse.FileType('r'),
                    help='Path to file containing pylint output for the '
                         'ansible-deprecated-version check')
args = parser.parse_args()


body_tmpl = args.template.read()
args.template.close()

text = args.problems[0].read()
args.problems[0].close()


for line in text.splitlines():
    path = line.split(':')[0]
    if path.endswith('__init__.py'):
        component = os.path.basename(os.path.dirname(path))
    else:
        component, ext_ = os.path.splitext(os.path.basename(path).lstrip('_'))

    title = (
        '%s contains deprecated call to be removed in %s' %
        (component, ansible_major_version)
    )
    deprecated[component].append(
        dict(title=title, path=path, line=line)
    )


g = GitHub(token=os.getenv('GITHUB_TOKEN'))
repo = g.repository('ansible', 'ansible')

# Not enabled by default, this fetches the column of a project,
# so that we can later add the issue to a project column
# You will need the project and column IDs for this to work
# and then update the below lines
# project = repo.project(2141803)
# project_column = project.column(4348504)

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
    # Uncomment the next 2 lines if you want to add issues to a project
    # Needs to be done in combination with the above code for selecting
    # the project/column
    # project_column.create_card_with_issue(issue)
    # time.sleep(0.5)
