#!/usr/bin/env python
"""Make sure the data in BOTMETA.yml is valid"""

import os.path
import glob
import sys
import yaml

from voluptuous import Any, MultipleInvalid, Required, Schema
from voluptuous.humanize import humanize_error

from ansible.module_utils.six import string_types
list_string_types = list(string_types)

def main():
    """Validate BOTMETA"""
    path = '.github/BOTMETA.yml'
    with open(path, 'r') as f_path:
        botmeta = yaml.safe_load(f_path)
    f_path.close()

    files_schema = Any(
        Schema(*string_types),
        Schema({
            'ignored': Any(list_string_types, *string_types),
            'keywords': Any(list_string_types, *string_types),
            'labels': Any(list_string_types, *string_types),
            'maintainers': Any(list_string_types, *string_types),
            'notified': Any(list_string_types, *string_types),
            'support': Any("core", "network", "community"),
        })
    )

    list_dict_file_schema = [{str_type: files_schema}
                             for str_type in string_types]

    schema = Schema({
        Required('automerge'): bool,
        Required('files'): Any(None, *list_dict_file_schema),
        Required('macros'): dict,  # Any(*list_macros_schema),
    })

   # Ensure schema is valid

    try:
        schema(botmeta)
    except MultipleInvalid as ex:
        for error in ex.errors:
            # No way to get line numbers
            print('%s: %s' % (path, humanize_error(botmeta, error)))

    # We have two macros to define locations, ensure they haven't been removed
    if botmeta['macros']['module_utils'] != 'lib/ansible/module_utils':
        print('%s: [macros][module_utils] has been removed' % path)

    if botmeta['macros']['modules'] != 'lib/ansible/modules':
        print('%s: [macros][modules] has been removed' % path)

    # See if all `files:` are valid
    for file in botmeta['files']:
        file = file.replace('$module_utils', botmeta['macros']['module_utils'])
        file = file.replace('$modules', botmeta['macros']['modules'])
        if not os.path.exists(file):
            # Not a file or directory, though maybe the prefix to one?
            # https://github.com/ansible/ansibullbot/pull/1023
            if not glob.glob('%s*' % file):
                print("%s: Can't find '%s.*' in this branch" % (path, file))


if __name__ == '__main__':
    main()

# Possible future work
# * Schema for `macros:` - currently ignored due to team_ansible
# * Ensure that all $teams mention in `files:` exist in `$macros`
# * Validate GitHub names - possibly expensive lookup needed
