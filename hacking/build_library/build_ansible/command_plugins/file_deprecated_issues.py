# -*- coding: utf-8 -*-
# (c) 2017, Matt Martz <matt@sivel.net>
# (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import argparse
import os
import time

from collections import defaultdict

from ansible.release import __version__ as ansible_version

# Pylint doesn't understand Python3 namespace modules.
from ..commands import Command  # pylint: disable=relative-beyond-top-level
from .. import errors  # pylint: disable=relative-beyond-top-level

ANSIBLE_MAJOR_VERSION = '.'.join(ansible_version.split('.')[:2])


def get_token(token_file):
    if token_file:
        return token_file.read().strip()

    token = os.getenv('GITHUB_TOKEN').strip()
    if not token:
        raise errors.MissingUserInput(
            'Please provide a file containing a github oauth token with public_repo scope'
            ' via the --github-token argument or set the GITHUB_TOKEN env var with your'
            ' github oauth token'
        )
    return token


def parse_deprecations(problems_file_handle):
    deprecated = defaultdict(list)
    deprecation_errors = problems_file_handle.read()
    for line in deprecation_errors.splitlines():
        path = line.split(':')[0]
        if path.endswith('__init__.py'):
            component = os.path.basename(os.path.dirname(path))
        else:
            component, dummy = os.path.splitext(os.path.basename(path).lstrip('_'))

        title = (
            '%s contains deprecated call to be removed in %s' %
            (component, ANSIBLE_MAJOR_VERSION)
        )
        deprecated[component].append(
            dict(title=title, path=path, line=line)
        )
    return deprecated


def find_project_todo_column(repo, project_name):
    project = None
    for project in repo.projects():
        if project.name.lower() == project_name:
            break
    else:
        raise errors.InvalidUserInput('%s was an invalid project name' % project_name)

    for project_column in project.columns():
        column_name = project_column.name.lower()
        if 'todo' in column_name or 'backlog' in column_name or 'to do' in column_name:
            return project_column

    raise Exception('Unable to determine the todo column in'
                    ' project %s' % project_name)


def create_issues(deprecated, body_tmpl, repo):
    issues = []

    for component, items in deprecated.items():
        title = items[0]['title']
        path = '\n'.join(set((i['path']) for i in items))
        line = '\n'.join(i['line'] for i in items)
        body = body_tmpl % dict(component=component, path=path,
                                line=line,
                                version=ANSIBLE_MAJOR_VERSION)

        issue = repo.create_issue(title, body=body, labels=['deprecated'])
        print(issue)
        issues.append(issue)

        # Sleep a little, so that the API doesn't block us
        time.sleep(0.5)

    return issues


class FileDeprecationTickets(Command):
    name = 'file-deprecation-tickets'

    @classmethod
    def init_parser(cls, add_parser):
        parser = add_parser(cls.name, description='File tickets to cleanup deprecated features for'
                            ' the next release')
        parser.add_argument('--template', default='deprecated_issue_template.md',
                            type=argparse.FileType('r'),
                            help='Path to markdown file template to be used for issue '
                                 'body. Default: %(default)s')
        parser.add_argument('--project-name', default='', type=str,
                            help='Name of a github project to assign all issues to')
        parser.add_argument('--github-token', type=argparse.FileType('r'),
                            help='Path to file containing a github token with public_repo scope.'
                                 ' This token in this file will be used to open the deprcation'
                                 ' tickets and add them to the github project.  If not given,'
                                 ' the GITHUB_TOKEN environment variable will be tried')
        parser.add_argument('problems', type=argparse.FileType('r'),
                            help='Path to file containing pylint output for the '
                                 'ansible-deprecated-version check')

    @staticmethod
    def main(args):
        try:
            from github3 import GitHub
        except ImportError:
            raise errors.DependencyError(
                'This command needs the github3.py library installed to work'
            )

        token = get_token(args.github_token)
        args.github_token.close()

        deprecated = parse_deprecations(args.problems)
        args.problems.close()

        body_tmpl = args.template.read()
        args.template.close()

        project_name = args.project_name.strip().lower()

        gh_conn = GitHub(token=token)
        repo = gh_conn.repository('abadger', 'ansible')

        if project_name:
            project_column = find_project_todo_column(repo, project_name)

        issues = create_issues(deprecated, body_tmpl, repo)

        if project_column:
            for issue in issues:
                project_column.create_card_with_issue(issue)
                time.sleep(0.5)

        return 0
