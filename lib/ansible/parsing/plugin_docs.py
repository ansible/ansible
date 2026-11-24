# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import yaml

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils.common.text.converters import to_native
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.utils.display import Display
from ansible.utils.doc_extractor import ast_py_docs
from ansible._internal._datatag import _tags

display = Display()


string_to_vars = {
    'DOCUMENTATION': 'doc',
    'EXAMPLES': 'plainexamples',
    'RETURN': 'returndocs',
    'ANSIBLE_METADATA': 'metadata',  # NOTE: now unused, but kept for backwards compat
}


def _init_doc_dict():
    """ initialize a return dict for docs with the expected structure """
    return {k: None for k in string_to_vars.values()}


def read_docstring_from_yaml_file(filename, verbose=True, ignore_errors=True):
    """ Read docs from 'sidecar' yaml file doc for a plugin """

    data = _init_doc_dict()
    file_data = {}

    try:
        with open(filename, 'rb') as yamlfile:
            file_data = yaml.load(yamlfile, Loader=AnsibleLoader)
    except Exception as ex:
        msg = f"Unable to parse yaml file {filename}"
        # DTFIX-FUTURE: find a better pattern for this (can we use the new optional error behavior?)
        if not ignore_errors:
            raise AnsibleParserError(f'{msg}.') from ex
        elif verbose:
            display.error(f'{msg}: {ex}')

    if file_data:
        for key in string_to_vars:
            data[string_to_vars[key]] = file_data.get(key, None)

    return data


def read_docstring_from_python_file(filename, verbose=True, ignore_errors=True):
    """
    Use ast to search for assignment of the DOCUMENTATION and EXAMPLES variables in the given file.
    Parse DOCUMENTATION from YAML and return the YAML doc or None together with EXAMPLES, as plain text.
    """
    data = _init_doc_dict()

    try:
        raw = ast_py_docs(filename, raise_on_error=True)
    except Exception as ex:
        msg = f"Unable to parse documentation in python file {filename!r}"
        # DTFIX-FUTURE: better pattern to conditionally raise/display
        if not ignore_errors:
            raise AnsibleParserError(f'{msg}.') from ex
        elif verbose:
            display.error(f'{msg}: {ex}.')
        return data

    for key, varkey in string_to_vars.items():
        if key in raw:
            data[varkey] = raw[key]
            display.debug('Documentation assigned: %s' % varkey)

    return data


def read_docstring(filename, verbose=True, ignore_errors=True):
    """ returns a documentation dictionary from Ansible plugin docstrings """

    # NOTE: adjacency of doc file to code file is responsibility of caller
    if filename.endswith(C.YAML_DOC_EXTENSIONS):
        docstring = read_docstring_from_yaml_file(filename, verbose=verbose, ignore_errors=ignore_errors)
    elif filename.endswith(C.PYTHON_DOC_EXTENSIONS):
        docstring = read_docstring_from_python_file(filename, verbose=verbose, ignore_errors=ignore_errors)
    elif not ignore_errors:
        raise AnsibleError("Unknown documentation format: %s" % to_native(filename))

    if not docstring and not ignore_errors:
        raise AnsibleError("Unable to parse documentation for: %s" % to_native(filename))

    # cause seealso is specially processed from 'doc' later on
    # TODO: stop any other 'overloaded' implementation in main doc
    docstring['seealso'] = None

    return docstring


def read_docstub(filename):
    """
    Quickly find short_description using string methods instead of node parsing.
    This does not return a full set of documentation strings and is intended for
    operations like ansible-doc -l.
    """

    in_documentation = False
    capturing = False
    indent_detection = ''
    doc_stub = []

    with open(filename, 'r') as t_module_data:
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

            elif line.startswith('DOCUMENTATION') and ('=' in line or ':' in line):
                in_documentation = True

    short_description = r''.join(doc_stub).strip().rstrip('.')
    data = yaml.load(_tags.Origin(path=str(filename)).tag(short_description), Loader=AnsibleLoader)

    return data
