#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""A tool to aggregate data about Ansible source and testing into a sqlite DB for reporting."""

from __future__ import (absolute_import, print_function)

import argparse
import os
import requests
import sqlite3
import sys

DATABASE_PATH = os.path.expanduser('~/.ansible/report.db')
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')) + '/'
ANSIBLE_PATH = os.path.join(BASE_PATH, 'lib')
ANSIBLE_TEST_PATH = os.path.join(BASE_PATH, 'test/runner')

if ANSIBLE_PATH not in sys.path:
    sys.path.insert(0, ANSIBLE_PATH)

if ANSIBLE_TEST_PATH not in sys.path:
    sys.path.insert(0, ANSIBLE_TEST_PATH)

from ansible.parsing.metadata import extract_metadata
from lib.target import walk_integration_targets


def main():
    os.chdir(BASE_PATH)

    args = parse_args()
    args.func()


def parse_args():
    try:
        import argcomplete
    except ImportError:
        argcomplete = None

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(metavar='COMMAND')
    subparsers.required = True  # work-around for python 3 bug which makes subparsers optional

    populate = subparsers.add_parser('populate',
                                     help='populate report database')

    populate.set_defaults(func=populate_database)

    query = subparsers.add_parser('query',
                                  help='query report database')

    query.set_defaults(func=query_database)

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    return args


def query_database():
    if not os.path.exists(DATABASE_PATH):
        exit('error: Database not found. Did you run `report.py populate` first?')

    os.execvp('sqlite3', ('sqlite3', DATABASE_PATH))


def populate_database():
    populate_modules()
    populate_coverage()
    populate_integration_targets()


def populate_modules():
    module_dir = os.path.join(BASE_PATH, 'lib/ansible/modules/')

    modules_rows = []
    module_statuses_rows = []

    for root, dir_names, file_names in os.walk(module_dir):
        for file_name in file_names:
            module, extension = os.path.splitext(file_name)

            if module == '__init__' or extension != '.py':
                continue

            if module.startswith('_'):
                module = module[1:]

            namespace = os.path.join(root.replace(module_dir, '')).replace('/', '.')

            path = os.path.join(root, file_name)

            with open(path, 'rb') as module_fd:
                module_data = module_fd.read()

            result = extract_metadata(module_data=module_data)

            metadata = result[0]

            if not metadata:
                if module == 'async_wrapper':
                    continue

                raise Exception('no metadata for: %s' % path)

            modules_rows.append(dict(
                module=module,
                namespace=namespace,
                path=path.replace(BASE_PATH, ''),
                supported_by=metadata['supported_by'],
            ))

            for status in metadata['status']:
                module_statuses_rows.append(dict(
                    module=module,
                    status=status,
                ))

    populate_data(dict(
        modules=dict(
            rows=modules_rows,
            schema=(
                ('module', 'TEXT'),
                ('namespace', 'TEXT'),
                ('path', 'TEXT'),
                ('supported_by', 'TEXT'),
            )),
        module_statuses=dict(
            rows=module_statuses_rows,
            schema=(
                ('module', 'TEXT'),
                ('status', 'TEXT'),
            )),
    ))


def populate_coverage():
    response = requests.get('https://codecov.io/api/gh/ansible/ansible/tree/devel/?src=extension')
    data = response.json()
    files = data['commit']['report']['files']
    coverage_rows = []

    for path, data in files.items():
        report = data['t']
        coverage_rows.append(dict(
            path=path,
            coverage=float(report['c']),
            lines=report['n'],
            hit=report['h'],
            partial=report['p'],
            missed=report['m'],
        ))

    populate_data(dict(
        coverage=dict(
            rows=coverage_rows,
            schema=(
                ('path', 'TEXT'),
                ('coverage', 'REAL'),
                ('lines', 'INTEGER'),
                ('hit', 'INTEGER'),
                ('partial', 'INTEGER'),
                ('missed', 'INTEGER'),
            )),
    ))


def populate_integration_targets():
    targets = list(walk_integration_targets())

    integration_targets_rows = [dict(
        target=target.name,
        type=target.type,
        path=target.path,
        script_path=target.script_path,
    ) for target in targets]

    integration_target_aliases_rows = [dict(
        target=target.name,
        alias=alias,
    ) for target in targets for alias in target.aliases]

    integration_target_modules_rows = [dict(
        target=target.name,
        module=module,
    ) for target in targets for module in target.modules]

    populate_data(dict(
        integration_targets=dict(
            rows=integration_targets_rows,
            schema=(
                ('target', 'TEXT'),
                ('type', 'TEXT'),
                ('path', 'TEXT'),
                ('script_path', 'TEXT'),
            )),
        integration_target_aliases=dict(
            rows=integration_target_aliases_rows,
            schema=(
                ('target', 'TEXT'),
                ('alias', 'TEXT'),
            )),
        integration_target_modules=dict(
            rows=integration_target_modules_rows,
            schema=(
                ('target', 'TEXT'),
                ('module', 'TEXT'),
            )),
    ))


def create_table(cursor, name, columns):
    schema = ', '.join('%s %s' % column for column in columns)

    cursor.execute('DROP TABLE IF EXISTS %s' % name)
    cursor.execute('CREATE TABLE %s (%s)' % (name, schema))


def populate_table(cursor, rows, name, columns):
    create_table(cursor, name, columns)

    values = ', '.join([':%s' % column[0] for column in columns])

    for row in rows:
        cursor.execute('INSERT INTO %s VALUES (%s)' % (name, values), row)


def populate_data(data):
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    for table in data:
        populate_table(cursor, data[table]['rows'], table, data[table]['schema'])

    connection.commit()
    connection.close()


if __name__ == '__main__':
    main()
