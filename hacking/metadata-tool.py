#!/usr/bin/env python
# (c) 2016-2017, Toshio Kuratomi <tkuratomi@ansible.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ast
import csv
import os
import sys
from collections import defaultdict
from distutils.version import StrictVersion
from pprint import pformat, pprint

from ansible.parsing.metadata import ParseError, extract_metadata
from ansible.plugins import module_loader


# There's a few files that are not new-style modules.  Have to blacklist them
NONMODULE_PY_FILES = frozenset(('async_wrapper.py',))
NONMODULE_MODULE_NAMES = frozenset(os.path.splitext(p)[0] for p in NONMODULE_PY_FILES)

# Default metadata
DEFAULT_METADATA = {'metadata_version': '1.0', 'status': ['preview'], 'supported_by': 'community'}


class MissingModuleError(Exception):
    """Thrown when unable to find a plugin"""
    pass


def usage():
    print("""Usage:
      metadata-tool.py report [--version X]
      metadata-tool.py add [--version X] [--overwrite] CSVFILE
      metadata-tool.py add-default [--version X] [--overwrite]
      medatada-tool.py upgrade [--version X]""")
    sys.exit(1)


def parse_args(arg_string):
    if len(arg_string) < 1:
        usage()

    action = arg_string[0]

    version = None
    if '--version' in arg_string:
        version_location = arg_string.index('--version')
        arg_string.pop(version_location)
        version = arg_string.pop(version_location)

    overwrite = False
    if '--overwrite' in arg_string:
        overwrite = True
        arg_string.remove('--overwrite')

    csvfile = None
    if len(arg_string) == 2:
        csvfile = arg_string[1]
    elif len(arg_string) > 2:
        usage()

    return action, {'version': version, 'overwrite': overwrite, 'csvfile': csvfile}


def find_documentation(module_data):
    """Find the DOCUMENTATION metadata for a module file"""
    start_line = -1
    mod_ast_tree = ast.parse(module_data)
    for child in mod_ast_tree.body:
        if isinstance(child, ast.Assign):
            for target in child.targets:
                if target.id == 'DOCUMENTATION':
                    start_line = child.lineno - 1
                    break

    return start_line


def remove_metadata(module_data, start_line, start_col, end_line, end_col):
    """Remove a section of a module file"""
    lines = module_data.split('\n')
    new_lines = lines[:start_line]
    if start_col != 0:
        new_lines.append(lines[start_line][:start_col])

    next_line = lines[end_line]
    if len(next_line) - 1 != end_col:
        new_lines.append(next_line[end_col:])

    if len(lines) > end_line:
        new_lines.extend(lines[end_line + 1:])
    return '\n'.join(new_lines)


def insert_metadata(module_data, new_metadata, insertion_line, targets=('ANSIBLE_METADATA',)):
    """Insert a new set of metadata at a specified line"""
    assignments = ' = '.join(targets)
    pretty_metadata = pformat(new_metadata, width=1).split('\n')

    new_lines = []
    new_lines.append('{} = {}'.format(assignments, pretty_metadata[0]))

    if len(pretty_metadata) > 1:
        for line in pretty_metadata[1:]:
            new_lines.append('{}{}'.format(' ' * (len(assignments) - 1 + len(' = {')), line))

    old_lines = module_data.split('\n')
    lines = old_lines[:insertion_line] + new_lines + [''] + old_lines[insertion_line:]
    return '\n'.join(lines)


def parse_assigned_metadata_initial(csvfile):
    """
    Fields:
        :0: Module name
        :1: Core (x if so)
        :2: Extras (x if so)
        :3: Category
        :4: Supported/SLA
        :5: Curated
        :6: Stable
        :7: Deprecated
        :8: Notes
        :9: Team Notes
        :10: Notes 2
        :11: final supported_by field
    """
    with open(csvfile, 'rb') as f:
        for record in csv.reader(f):
            module = record[0]

            if record[12] == 'core':
                supported_by = 'core'
            elif record[12] == 'curated':
                supported_by = 'curated'
            elif record[12] == 'community':
                supported_by = 'community'
            else:
                print('Module %s has no supported_by field.  Using community' % record[0])
                supported_by = 'community'
                supported_by = DEFAULT_METADATA['supported_by']

            status = []
            if record[6]:
                status.append('stableinterface')
            if record[7]:
                status.append('deprecated')
            if not status:
                status.extend(DEFAULT_METADATA['status'])

            yield (module, {'version': DEFAULT_METADATA['metadata_version'], 'supported_by': supported_by, 'status': status})


def parse_assigned_metadata(csvfile):
    """
    Fields:
        :0: Module name
        :1: supported_by  string.  One of the valid support fields
            core, community, curated
        :2: stableinterface
        :3: preview
        :4: deprecated
        :5: removed

        https://github.com/ansible/proposals/issues/30
    """
    with open(csvfile, 'rb') as f:
        for record in csv.reader(f):
            module = record[0]
            supported_by = record[1]

            status = []
            if record[2]:
                status.append('stableinterface')
            if record[4]:
                status.append('deprecated')
            if record[5]:
                status.append('removed')
            if not status or record[3]:
                status.append('preview')

            yield (module, {'metadata_version': '1.0', 'supported_by': supported_by, 'status': status})


def write_metadata(filename, new_metadata, version=None, overwrite=False):
    with open(filename, 'rb') as f:
        module_data = f.read()

    try:
        current_metadata, start_line, start_col, end_line, end_col, targets = \
            extract_metadata(module_data=module_data, offsets=True)
    except SyntaxError:
        if filename.endswith('.py'):
            raise
        # Probably non-python modules.  These should all have python
        # documentation files where we can place the data
        raise ParseError('Could not add metadata to {}'.format(filename))

    if current_metadata is None:
        # No current metadata so we can just add it
        start_line = find_documentation(module_data)
        if start_line < 0:
            if os.path.basename(filename) in NONMODULE_PY_FILES:
                # These aren't new-style modules
                return

            raise Exception('Module file {} had no ANSIBLE_METADATA or DOCUMENTATION'.format(filename))

        module_data = insert_metadata(module_data, new_metadata, start_line, targets=('ANSIBLE_METADATA',))

    elif overwrite or (version is not None and ('metadata_version' not in current_metadata or
                                                StrictVersion(current_metadata['metadata_version']) < StrictVersion(version))):
        # Current metadata that we do not want.  Remove the current
        # metadata and put the new version in its place
        module_data = remove_metadata(module_data, start_line, start_col, end_line, end_col)
        module_data = insert_metadata(module_data, new_metadata, start_line, targets=targets)

    else:
        # Current metadata and we don't want to overwrite it
        return

    # Save the new version of the module
    with open(filename, 'wb') as f:
        f.write(module_data)


def return_metadata(plugins):
    """Get the metadata for all modules

    Handle duplicate module names

    :arg plugins: List of plugins to look for
    :returns: Mapping of plugin name to metadata dictionary
    """
    metadata = {}
    for name, filename in plugins:
        # There may be several files for a module (if it is written in another
        # language, for instance) but only one of them (the .py file) should
        # contain the metadata.
        if name not in metadata or metadata[name] is not None:
            with open(filename, 'rb') as f:
                module_data = f.read()
            metadata[name] = extract_metadata(module_data=module_data, offsets=True)[0]
    return metadata


def metadata_summary(plugins, version=None):
    """Compile information about the metadata status for a list of modules

    :arg plugins: List of plugins to look for.  Each entry in the list is
        a tuple of (module name, full path to module)
    :kwarg version: If given, make sure the modules have this version of
        metadata or higher.
    :returns: A tuple consisting of a list of modules with no metadata at the
        required version and a list of files that have metadata at the
        required version.
    """
    no_metadata = {}
    has_metadata = {}
    supported_by = defaultdict(set)
    status = defaultdict(set)
    requested_version = StrictVersion(version)

    all_mods_metadata = return_metadata(plugins)
    for name, filename in plugins:
        # Does the module have metadata?
        if name not in no_metadata and name not in has_metadata:
            metadata = all_mods_metadata[name]
            if metadata is None:
                no_metadata[name] = filename
            elif version is not None and ('metadata_version' not in metadata or StrictVersion(metadata['metadata_version']) < requested_version):
                no_metadata[name] = filename
            else:
                has_metadata[name] = filename

        # What categories does the plugin belong in?
        if all_mods_metadata[name] is None:
            # No metadata for this module.  Use the default metadata
            supported_by[DEFAULT_METADATA['supported_by']].add(filename)
            status[DEFAULT_METADATA['status'][0]].add(filename)
        else:
            supported_by[all_mods_metadata[name]['supported_by']].add(filename)
            for one_status in all_mods_metadata[name]['status']:
                status[one_status].add(filename)

    return list(no_metadata.values()), list(has_metadata.values()), supported_by, status

# Filters to convert between metadata versions


def convert_metadata_pre_1_0_to_1_0(metadata):
    """
    Convert pre-1.0 to 1.0 metadata format

    :arg metadata: The old metadata
    :returns: The new metadata

    Changes from pre-1.0 to 1.0:
    * ``version`` field renamed to ``metadata_version``
    * ``supported_by`` field value ``unmaintained`` has been removed (change to
      ``community`` and let an external list track whether a module is unmaintained)
    * ``supported_by`` field value ``committer`` has been renamed to ``curated``
    """
    new_metadata = {'metadata_version': '1.0',
                    'supported_by': metadata['supported_by'],
                    'status': metadata['status']
                    }
    if new_metadata['supported_by'] == 'unmaintained':
        new_metadata['supported_by'] = 'community'
    elif new_metadata['supported_by'] == 'committer':
        new_metadata['supported_by'] = 'curated'

    return new_metadata

# Subcommands


def add_from_csv(csv_file, version=None, overwrite=False):
    """Implement the subcommand to add metadata from a csv file
    """
    # Add metadata for everything from the CSV file
    diagnostic_messages = []
    for module_name, new_metadata in parse_assigned_metadata_initial(csv_file):
        filename = module_loader.find_plugin(module_name, mod_type='.py')
        if filename is None:
            diagnostic_messages.append('Unable to find the module file for {}'.format(module_name))
            continue

        try:
            write_metadata(filename, new_metadata, version, overwrite)
        except ParseError as e:
            diagnostic_messages.append(e.args[0])
            continue

    if diagnostic_messages:
        pprint(diagnostic_messages)

    return 0


def add_default(version=None, overwrite=False):
    """Implement the subcommand to add default metadata to modules

    Add the default metadata to any plugin which lacks it.
    :kwarg version: If given, the metadata must be at least this version.
        Otherwise, treat the module as not having existing metadata.
    :kwarg overwrite: If True, overwrite any existing metadata.  Otherwise,
        do not modify files which have metadata at an appropriate version
    """
    # List of all plugins
    plugins = module_loader.all(path_only=True)
    plugins = ((os.path.splitext((os.path.basename(p)))[0], p) for p in plugins)
    plugins = (p for p in plugins if p[0] not in NONMODULE_MODULE_NAMES)

    # Iterate through each plugin
    processed = set()
    diagnostic_messages = []
    for name, filename in (info for info in plugins if info[0] not in processed):
        try:
            write_metadata(filename, DEFAULT_METADATA, version, overwrite)
        except ParseError as e:
            diagnostic_messages.append(e.args[0])
            continue
        processed.add(name)

    if diagnostic_messages:
        pprint(diagnostic_messages)

    return 0


def upgrade_metadata(version=None):
    """Implement the subcommand to upgrade the default metadata in modules.

    :kwarg version: If given, the version of the metadata to upgrade to.  If
        not given, upgrade to the latest format version.
    """
    if version is None:
        # Number larger than any of the defined metadata formats.
        version = 9999999
    requested_version = StrictVersion(version)

    # List all plugins
    plugins = module_loader.all(path_only=True)
    plugins = ((os.path.splitext((os.path.basename(p)))[0], p) for p in plugins)
    plugins = (p for p in plugins if p[0] not in NONMODULE_MODULE_NAMES)

    processed = set()
    diagnostic_messages = []
    for name, filename in (info for info in plugins if info[0] not in processed):
        # For each plugin, read the existing metadata
        with open(filename, 'rb') as f:
            module_data = f.read()
        metadata = extract_metadata(module_data=module_data, offsets=True)[0]

        # If the metadata isn't the requested version, convert it to the new
        # version
        if 'metadata_version' not in metadata or metadata['metadata_version'] != version:
            #
            # With each iteration of metadata, add a new conditional to
            # upgrade from the previous version
            #

            if 'metadata_version' not in metadata:
                # First version, pre-1.0 final metadata
                metadata = convert_metadata_pre_1_0_to_1_0(metadata)

            if metadata['metadata_version'] == '1.0' and StrictVersion('1.0') < requested_version:
                # 1.0 version => XXX.  We don't yet have anything beyond 1.0
                # so there's nothing here
                pass

            # Replace the existing metadata with the new format
            try:
                write_metadata(filename, metadata, version, overwrite=True)
            except ParseError as e:
                diagnostic_messages.append(e.args[0])
                continue

        processed.add(name)

    if diagnostic_messages:
        pprint(diagnostic_messages)

    return 0


def report(version=None):
    """Implement the report subcommand

    Print out all the modules that have metadata and all the ones that do not.

    :kwarg version: If given, the metadata must be at least this version.
        Otherwise return it as not having metadata
    """
    # List of all plugins
    plugins = module_loader.all(path_only=True)
    plugins = ((os.path.splitext((os.path.basename(p)))[0], p) for p in plugins)
    plugins = (p for p in plugins if p[0] not in NONMODULE_MODULE_NAMES)
    plugins = list(plugins)

    no_metadata, has_metadata, support, status = metadata_summary(plugins, version=version)

    print('== Has metadata ==')
    pprint(sorted(has_metadata))
    print('')

    print('== Has no metadata ==')
    pprint(sorted(no_metadata))
    print('')

    print('== Supported by core ==')
    pprint(sorted(support['core']))
    print('== Supported by value curated ==')
    pprint(sorted(support['curated']))
    print('== Supported by community ==')
    pprint(sorted(support['community']))
    print('')

    print('== Status: stableinterface ==')
    pprint(sorted(status['stableinterface']))
    print('== Status: preview ==')
    pprint(sorted(status['preview']))
    print('== Status: deprecated ==')
    pprint(sorted(status['deprecated']))
    print('== Status: removed ==')
    pprint(sorted(status['removed']))
    print('')

    print('== Summary ==')
    print('No Metadata: {0}             Has Metadata: {1}'.format(len(no_metadata), len(has_metadata)))
    print('Supported by core: {0}      Supported by community: {1}    Supported by value curated: {2}'.format(len(support['core']),
          len(support['community']), len(support['curated'])))
    print('Status StableInterface: {0} Status Preview: {1}            Status Deprecated: {2}      Status Removed: {3}'.format(len(status['stableinterface']),
          len(status['preview']), len(status['deprecated']), len(status['removed'])))

    return 0


if __name__ == '__main__':
    action, args = parse_args(sys.argv[1:])

    if action == 'report':
        rc = report(version=args['version'])
    elif action == 'add':
        rc = add_from_csv(args['csvfile'], version=args['version'], overwrite=args['overwrite'])
    elif action == 'add-default':
        rc = add_default(version=args['version'], overwrite=args['overwrite'])
    elif action == 'upgrade':
        rc = upgrade_metadata(version=args['version'])

    sys.exit(rc)
