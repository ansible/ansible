# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ast
import yaml

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
        'ANSIBLE_METADATA': 'metadata'
    }

    try:
        M = ast.parse(''.join(open(filename)))
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
                                if theid in ['DOCUMENTATION', 'ANSIBLE_METADATA']:
                                    # string should be yaml
                                    data[varkey] = AnsibleLoader(child.value.s, file_name=filename).get_single_data()
                                else:
                                    # not yaml, should be a simple string
                                    data[varkey] = child.value.s
                            display.debug('assigned :%s' % varkey)

    except:
        if verbose:
            display.error("unable to parse %s" % filename)
        if not ignore_errors:
            raise

    return data
