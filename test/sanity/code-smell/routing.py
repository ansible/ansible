#!/usr/bin/env python
"""Make sure the data in meta/routing.yml is valid"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import glob
from pathlib import Path
import os
import re
import sys
import yaml

from voluptuous import All, Any, Match, MultipleInvalid, Required, Schema, ALLOW_EXTRA, PREVENT_EXTRA, All, Any, Invalid, Length, Required, Schema, Self, ValueInvalid
from voluptuous.humanize import humanize_error

from ansible.module_utils.six import string_types

def main():
    """Validate ansible-base' routing.yml"""
    path = 'lib/ansible/config/routing.yml'

    if not os.path.isfile(path):
        # skip if routing file doesn't exist
        sys.exit(0)

    try:
        with open(path, 'r') as f_path:
            routing = yaml.safe_load(f_path)
    except yaml.error.MarkedYAMLError as ex:
        print('%s:%d:%d: YAML load failed: %s' % (path, ex.context_mark.line +
                                                  1, ex.context_mark.column + 1, re.sub(r'\s+', ' ', str(ex))))
        sys.exit()
    except Exception as ex:  # pylint: disable=broad-except
        print('%s:%d:%d: YAML load failed: %s' %
              (path, 0, 0, re.sub(r'\s+', ' ', str(ex))))
        sys.exit()

    list_string_types = list(string_types)

    deprecation_schema = Schema(
        {
            Required('removal_date'): Any(*string_types),
            Required('warning_text'): Any(*string_types),

        },
        extra=PREVENT_EXTRA
    )

    files_schema = Any(
        Schema(*string_types),
        Schema({
            ('deprecation'): Any(deprecation_schema),
            Required('redirect'): Any(*string_types),
        },
        extra=PREVENT_EXTRA)
    )

    list_dict_file_schema = [{str_type: files_schema}
                             for str_type in string_types]

    plugin_schema = Schema({
        # FIXME: Look at how to pass an array in
        Required('action'): Any(None, *list_dict_file_schema),
        Required('become'): Any(None, *list_dict_file_schema),
        Required('cache'): Any(None, *list_dict_file_schema),
        Required('doc_fragments'): Any(None, *list_dict_file_schema),
        Required('callback'): Any(None, *list_dict_file_schema),
        Required('lookup'): Any(None, *list_dict_file_schema),
        Required('cliconf'): Any(None, *list_dict_file_schema),
        Required('connection'): Any(None, *list_dict_file_schema),
        Required('filter'): Any(None, *list_dict_file_schema),
        Required('httpapi'): Any(None, *list_dict_file_schema),
        Required('inventory'): Any(None, *list_dict_file_schema),
        Required('modules'): Any(None, *list_dict_file_schema),
        Required('module_utils'): Any(None, *list_dict_file_schema),
        Required('netconf'): Any(None, *list_dict_file_schema),
        Required('shell'): Any(None, *list_dict_file_schema),
        Required('terminal'): Any(None, *list_dict_file_schema),
    },
    extra=PREVENT_EXTRA)

    schema = Schema({
        Required('plugin_routing'): Any(plugin_schema),
        },
        extra=PREVENT_EXTRA
    )

    # Ensure schema is valid

    try:
        schema(routing)
    except MultipleInvalid as ex:
        for error in ex.errors:
            # No way to get line numbers
            print('%s:%d:%d: %s' % (path, 0, 0, humanize_error(routing, error)))

    # This maybe moved to https://github.com/ansible-community/ansibulled
#    for plugin_type in sorted(list(plugin_schema.schema.keys())):
#        for plugin, file_meta in routing['plugin_routing'][plugin_type].items():
#            namespace, collection, new_name  = routing['plugin_routing'][plugin_type][plugin]['redirect'].split('.')
#            expected_path = "/tmp/ansible_collections/%s/%s/plugins/%s" % ( namespace, collection, plugin_type)
#            found_plugin = False
#            if os.path.exists('%s/%s.py' % (expected_path, new_name)):
#                found_plugin = True
#                # FIXME: For communty.{general,network}'s modules & module_utils should we check in subdirectories?
#            elif namespace == 'community' and collection in ['general', 'network']:
#                if plugin_type in ['modules','module_utils']:
#                    if glob.glob('%s/**/%s.py' % (expected_path, new_name), recursive = True):
#                        found_plugin = True
#            if not found_plugin:
#                print("%s:%d:%d: Can't find '%s/%s.py' in %s.%s" %
#                    (path, 0, 0, plugin_type, new_name, namespace, collection))

if __name__ == '__main__':
    main()
