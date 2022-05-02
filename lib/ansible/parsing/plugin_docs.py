# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ast
import tokenize

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_text, to_native
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.utils.display import Display

display = Display()


string_to_vars = {
    'DOCUMENTATION': 'doc',
    'EXAMPLES': 'plainexamples',
    'RETURN': 'returndocs',
    'ANSIBLE_METADATA': 'metadata',  # NOTE: now unused, but kept for backwards compat
}


def _var2string(value):
    ''' reverse lookup of the dict above '''
    for k, v in string_to_vars.items():
        if v == value:
            return k


def _init_doc_dict():
    ''' initialize a return dict for docs with the expected structure '''
    return {k: None for k in string_to_vars.values()}


def read_docstring_from_yaml_file(filename, verbose=True, ignore_errors=True):
    ''' Read docs from 'sidecar' yaml file doc for a plugin '''

    data = _init_doc_dict()
    file_data = {}

    try:
        with open(filename, 'rb') as yamlfile:
            file_data = AnsibleLoader(yamlfile.read(), file_name=filename).get_single_data()
    except Exception as e:
        msg = "Unable to parse yaml file '%s': %s" % (filename, to_native(e))
        if not ignore_errors:
            raise AnsibleParserError(msg, orig_exc=e)
        elif verbose:
            display.error(msg)

    if file_data:
        for key in string_to_vars:
            data[string_to_vars[key]] = file_data.get(key, None)

    return data


def read_docstring_from_python_module(filename, verbose=True, ignore_errors=True):
    """
    Use tokenization to search for assignment of the documentation variables in the given file.
    Parse from YAML and return the resulting python structure or None together with examples as plain text.
    """

    seen = set()
    data = _init_doc_dict()

    next_string = None
    with tokenize.open(filename) as f:
        tokens = tokenize.generate_tokens(f.readline)
        for token in tokens:

            # found lable that looks like variable
            if token.type == tokenize.NAME:

                # label is expected value, in correct place and has not been seen before
                if token.start == 1 and token.string in string_to_vars and token.string not in seen:
                    # next token that is string has the docs
                    next_string = string_to_vars[token.string]
                    continue

            # previous token indicated this string is a doc string
            if next_string is not None and token.type == tokenize.STRING:

                # ensure we only process one case of it
                seen.add(token.string)

                value = token.string

                # strip string modifiers/delimiters
                if value.startswith(('r', 'b')):
                    value = value.lstrip('rb')

                if value.startswith(("'", '"')):
                    value = value.strip("'\"")

                # actually use the data
                if next_string == 'plainexamples':
                    # keep as string, can be yaml, but we let caller deal with it
                    data[next_string] = to_text(value)
                else:
                    # yaml load the data
                    try:
                        data[next_string] = AnsibleLoader(value, file_name=filename).get_single_data()
                    except Exception as e:
                        msg = "Unable to parse docs '%s' in python file '%s': %s" % (_var2string(next_string), filename, to_native(e))
                        if not ignore_errors:
                            raise AnsibleParserError(msg, orig_exc=e)
                        elif verbose:
                            display.error(msg)

                next_string = None

    # if nothing else worked, fall back to old method
    if not seen:
        data = read_docstring_from_python_file(filename, verbose, ignore_errors)

    return data


def read_docstring_from_python_file(filename, verbose=True, ignore_errors=True):
    """
    Use ast to search for assignment of the DOCUMENTATION and EXAMPLES variables in the given file.
    Parse DOCUMENTATION from YAML and return the YAML doc or None together with EXAMPLES, as plain text.
    """

    data = _init_doc_dict()

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
                        display.warning("Building documentation, failed to assign id for %s on %s, skipping" % (t, filename))
                        continue

                    if theid in string_to_vars:
                        varkey = string_to_vars[theid]
                        if isinstance(child.value, ast.Dict):
                            data[varkey] = ast.literal_eval(child.value)
                        else:
                            if theid == 'EXAMPLES':
                                # examples 'can' be yaml, but even if so, we dont want to parse as such here
                                # as it can create undesired 'objects' that don't display well as docs.
                                data[varkey] = to_text(child.value.s)
                            else:
                                # string should be yaml if already not a dict
                                data[varkey] = AnsibleLoader(child.value.s, file_name=filename).get_single_data()

                        display.debug('Documentation assigned: %s' % varkey)

    except Exception as e:
        msg = "Unable to parse documentation in python file '%s': %s" % (filename, to_native(e))
        if not ignore_errors:
            raise AnsibleParserError(msg, orig_exc=e)
        elif verbose:
            display.error(msg)

    return data


def read_docstring(filename, verbose=True, ignore_errors=True):
    ''' returns a documentation dictionary from Ansible plugin docstrings '''

    # NOTE: adjacency of doc file to code file is responsibility of caller
    if filename.endswith(C.YAML_DOC_EXTENSIONS):
        docstring = read_docstring_from_yaml_file(filename, verbose=verbose, ignore_errors=ignore_errors)
    elif filename.endswith(C.PYTHON_DOC_EXTENSIONS):
        docstring = read_docstring_from_python_module(filename, verbose=verbose, ignore_errors=ignore_errors)
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
    data = AnsibleLoader(short_description, file_name=filename).get_single_data()

    return data
