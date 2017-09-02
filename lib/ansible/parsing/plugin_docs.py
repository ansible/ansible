# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ast
import yaml

from ansible.parsing.metadata import extract_metadata
from ansible.parsing.yaml.loader import AnsibleLoader

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def read_docstring(filename, verbose=True, ignore_errors=True):
    """
    Search for assignment of the DOCUMENTATION and EXAMPLES variables in the given file.
    Parse DOCUMENTATION from YAML and return the YAML doc or None together with EXAMPLES, as plain text.
    """

    # FIXME: Should refactor this so that we have a docstring parsing
    # function and a separate variable parsing function
    # Can have a function one higher that invokes whichever is needed
    #
    # Should look roughly like this:
    # get_plugin_doc(filename, verbose=False)
    #   documentation = extract_docstring(plugin_ast, identifier, verbose=False)
    #   if not documentation and not (filter or test):
    #       documentation = extract_variables(plugin_ast)
    #   documentation['metadata'] = extract_metadata(plugin_ast)
    #   return documentation

    data = {
        'doc': None,
        'plainexamples': None,
        'returndocs': None,
        'metadata': None
    }

    try:
        b_module_data = open(filename, 'rb').read()
        data = _read_docstring(b_module_data, data, filename)
    except:
        if verbose:
            display.error("unable to parse %s" % filename)
        if not ignore_errors:
            raise

    return data


def _read_docstring(b_module_data, data, filename):
    # Separate function so that we can call it with already-ready module data
    # from the executor.

    string_to_vars = {
        'DOCUMENTATION': 'doc',
        'EXAMPLES': 'plainexamples',
        'RETURN': 'returndocs',
    }

    M = ast.parse(b_module_data)
    try:
        display.debug('Attempt first docstring is yaml docs')
        docstring = yaml.load(M.body[0].value.s)
        for string in string_to_vars.keys():
            if string in docstring:
                data[string_to_vars[string]] = docstring[string]
            display.debug('assigned :%s' % string_to_vars[string])
    except Exception as e:
        display.debug('failed docstring parsing: %s' % str(e))

    if 'docs' not in data or not data['docs']:
        display.debug('Fallback to vars parsing')
        for child in M.body:
            if isinstance(child, ast.Assign):
                for t in child.targets:
                    try:
                        theid = t.id
                    except AttributeError:
                        # skip errors can happen when trying to use the normal code
                        display.warning("Failed to assign id for %s on %s, skipping" % (t, filename))
                        continue

                    if theid in string_to_vars:
                        varkey = string_to_vars[theid]
                        if isinstance(child.value, ast.Dict):
                            data[varkey] = ast.literal_eval(child.value)
                        else:
                            if theid == 'DOCUMENTATION':
                                # string should be yaml
                                data[varkey] = AnsibleLoader(child.value.s, file_name=filename).get_single_data()
                            else:
                                # not yaml, should be a simple string
                                data[varkey] = child.value.s
                        display.debug('assigned :%s' % varkey)

    # Metadata is per-file and a dict rather than per-plugin/function and yaml
    data['metadata'] = extract_metadata(module_ast=M)[0]

    # remove version
    if data['metadata']:
        for x in ('version', 'metadata_version'):
            if x in data['metadata']:
                del data['metadata'][x]

    return data
