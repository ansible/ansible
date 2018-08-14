# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ast
import yaml

from ansible.module_utils._text import to_text
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

    data = {
        'doc': None,
        'plainexamples': None,
        'returndocs': None,
        'metadata': None
    }

    string_to_vars = {
        'DOCUMENTATION': 'doc',
        'EXAMPLES': 'plainexamples',
        'RETURN': 'returndocs',
    }

    try:
        b_module_data = open(filename, 'rb').read()
        M = ast.parse(b_module_data)

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
                                data[varkey] = to_text(child.value.s)
                        display.debug('assigned :%s' % varkey)

        # Metadata is per-file and a dict rather than per-plugin/function and yaml
        data['metadata'] = extract_metadata(module_ast=M)[0]

        # remove version
        if data['metadata']:
            for x in ('version', 'metadata_version'):
                if x in data['metadata']:
                    del data['metadata'][x]
    except:
        if verbose:
            display.error("unable to parse %s" % filename)
        if not ignore_errors:
            raise

    return data


def read_docstub(filename, verbose=True, ignore_errors=True):
    """
    Quickly find short_description using string methods instead of node parsing.
    This does not return a full set of documentation strings and is intended for
    operations like ansible-doc -l.
    """

    data = {
        'doc': None,
        'plainexamples': None,
        'returndocs': None,
        'metadata': None
    }

    try:
        t_module_data = open(filename, 'r')
        capturing = False
        doc_stub = []

        for line in t_module_data:
            # start capturing the stub until indentation returns
            if capturing and line[0] == ' ':
                doc_stub.append(line)
            elif capturing and line[0] != ' ':
                break
            if 'short_description:' in line:
                capturing = True
                doc_stub.append(line)

        data['doc'] = AnsibleLoader(r"".join(doc_stub), file_name=filename).get_single_data()

    except:
        if verbose:
            display.error("unable to parse %s" % filename)
        if not ignore_errors:
            raise

    return data
