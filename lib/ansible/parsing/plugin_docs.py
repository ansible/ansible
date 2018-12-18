# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ast
import yaml

from ansible.module_utils._text import to_text
from ansible.parsing.metadata import extract_metadata
from ansible.parsing.yaml.loader import AnsibleLoader
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
        'metadata': None,
        'seealso': None,
    }

    string_to_vars = {
        'DOCUMENTATION': 'doc',
        'EXAMPLES': 'plainexamples',
        'RETURN': 'returndocs',
    }

    try:
        with open(filename, 'rb') as b_module_data:
            M = ast.parse(b_module_data.read())

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

        if data['metadata']:
            # remove version
            for x in ('version', 'metadata_version'):
                if x in data['metadata']:
                    del data['metadata'][x]
        else:
            # Add default metadata
            data['metadata'] = {'supported_by': 'community',
                                'status': ['preview']}
    except Exception:
        if verbose:
            display.error("unable to parse %s" % filename)
        if not ignore_errors:
            raise

    return data


def read_docstub(filename):
    """
    Quickly find short_description using string methods instead of node parsing.
    This does not return a full set of documentation strings and is intended for
    operations like ansible-doc -l.
    """

    t_module_data = open(filename, 'r')
    in_documentation = False
    capturing = False
    indent_detection = ''
    doc_stub = []

    for line in t_module_data:
        if in_documentation:
            # start capturing the stub until indentation returns
            if capturing and line.startswith(indent_detection):
                doc_stub.append(line)

            elif capturing and not line.startswith(indent_detection):
                break

            elif line.lstrip().startswith('short_description:'):
                capturing = True
                # Detect that the short_description continues on the next line if it's indented more
                # than short_description itself.
                indent_detection = ' ' * (len(line) - len(line.lstrip()) + 1)
                doc_stub.append(line)

        elif line.startswith('DOCUMENTATION') and '=' in line:
            in_documentation = True

    short_description = r''.join(doc_stub).strip().rstrip('.')
    data = AnsibleLoader(short_description, file_name=filename).get_single_data()

    return data
