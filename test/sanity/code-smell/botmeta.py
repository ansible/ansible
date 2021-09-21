"""Make sure the data in BOTMETA.yml is valid"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import glob
import os
import re
import sys
import yaml

from voluptuous import All, Any, Match, MultipleInvalid, Required, Schema
from voluptuous.humanize import humanize_error

from ansible.module_utils.six import string_types


def main():
    """Validate BOTMETA"""
    path = '.github/BOTMETA.yml'

    try:
        with open(path, 'r') as f_path:
            botmeta = yaml.safe_load(f_path)
    except yaml.error.MarkedYAMLError as ex:
        print('%s:%d:%d: YAML load failed: %s' % (path, ex.context_mark.line + 1, ex.context_mark.column + 1, re.sub(r'\s+', ' ', str(ex))))
        sys.exit()
    except Exception as ex:  # pylint: disable=broad-except
        print('%s:%d:%d: YAML load failed: %s' % (path, 0, 0, re.sub(r'\s+', ' ', str(ex))))
        sys.exit()

    list_string_types = list(string_types)

    files_schema = Any(
        Schema(*string_types),
        Schema({
            'ignored': Any(list_string_types, *string_types),
            'keywords': Any(list_string_types, *string_types),
            'labels': Any(list_string_types, *string_types),
            'maintainers': Any(list_string_types, *string_types),
            'migrated_to': All(
                Any(*string_types),
                Match(r'^\w+\.\w+$'),
            ),
            'notified': Any(list_string_types, *string_types),
            'supershipit': Any(list_string_types, *string_types),
            'support': Any("core", "network", "community"),
        })
    )

    list_dict_file_schema = [{str_type: files_schema}
                             for str_type in string_types]

    schema = Schema({
        Required('automerge'): bool,
        Required('collection_redirect'): bool,
        Required('notifications'): bool,
        Required('files'): Any(None, *list_dict_file_schema),
        Required('macros'): dict,  # Any(*list_macros_schema),
    })

    # Ensure schema is valid

    try:
        schema(botmeta)
    except MultipleInvalid as ex:
        for error in ex.errors:
            # No way to get line numbers
            print('%s:%d:%d: %s' % (path, 0, 0, humanize_error(botmeta, error)))

    # Ensure botmeta is always support:core
    botmeta_support = botmeta.get('files', {}).get('.github/BOTMETA.yml', {}).get('support', '')
    if botmeta_support != 'core':
        print('%s:%d:%d: .github/BOTMETA.yml MUST be support: core' % (path, 0, 0))

    # Find all path (none-team) macros so we can substitute them
    macros = botmeta.get('macros', {})
    path_macros = []
    for macro in macros:
        if macro.startswith('team_'):
            continue
        path_macros.append(macro)


if __name__ == '__main__':
    main()

# Possible future work
# * Schema for `macros:` - currently ignored due to team_ansible
# * Ensure that all $teams mention in `files:` exist in `$macros`
# * Validate GitHub names - possibly expensive lookup needed - No should be validated when module is added - gundalow
