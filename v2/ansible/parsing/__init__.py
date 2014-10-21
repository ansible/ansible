# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

import json

from yaml import YAMLError

from ansible.errors import AnsibleError, AnsibleInternalError
from ansible.parsing.vault import VaultLib
from ansible.parsing.yaml import safe_load


def process_common_errors(msg, probline, column):
    replaced = probline.replace(" ","")

    if ":{{" in replaced and "}}" in replaced:
        msg = msg + """
This one looks easy to fix.  YAML thought it was looking for the start of a
hash/dictionary and was confused to see a second "{".  Most likely this was
meant to be an ansible template evaluation instead, so we have to give the
parser a small hint that we wanted a string instead. The solution here is to
just quote the entire value.

For instance, if the original line was:

    app_path: {{ base_path }}/foo

It should be written as:

    app_path: "{{ base_path }}/foo"
"""
        return msg

    elif len(probline) and len(probline) > 1 and len(probline) > column and probline[column] == ":" and probline.count(':') > 1:
        msg = msg + """
This one looks easy to fix.  There seems to be an extra unquoted colon in the line
and this is confusing the parser. It was only expecting to find one free
colon. The solution is just add some quotes around the colon, or quote the
entire line after the first colon.

For instance, if the original line was:

    copy: src=file.txt dest=/path/filename:with_colon.txt

It can be written as:

    copy: src=file.txt dest='/path/filename:with_colon.txt'

Or:

    copy: 'src=file.txt dest=/path/filename:with_colon.txt'


"""
        return msg
    else:
        parts = probline.split(":")
        if len(parts) > 1:
            middle = parts[1].strip()
            match = False
            unbalanced = False
            if middle.startswith("'") and not middle.endswith("'"):
                match = True
            elif middle.startswith('"') and not middle.endswith('"'):
                match = True
            if len(middle) > 0 and middle[0] in [ '"', "'" ] and middle[-1] in [ '"', "'" ] and probline.count("'") > 2 or probline.count('"') > 2:
                unbalanced = True
            if match:
                msg = msg + """
This one looks easy to fix.  It seems that there is a value started
with a quote, and the YAML parser is expecting to see the line ended
with the same kind of quote.  For instance:

    when: "ok" in result.stdout

Could be written as:

   when: '"ok" in result.stdout'

or equivalently:

   when: "'ok' in result.stdout"

"""
                return msg

            if unbalanced:
                msg = msg + """
We could be wrong, but this one looks like it might be an issue with
unbalanced quotes.  If starting a value with a quote, make sure the
line ends with the same set of quotes.  For instance this arbitrary
example:

    foo: "bad" "wolf"

Could be written as:

    foo: '"bad" "wolf"'

"""
                return msg

    return msg

def process_yaml_error(exc, data, path=None, show_content=True):
    if hasattr(exc, 'problem_mark'):
        mark = exc.problem_mark
        if show_content:
            if mark.line -1 >= 0:
                before_probline = data.split("\n")[mark.line-1]
            else:
                before_probline = ''
            probline = data.split("\n")[mark.line]
            arrow = " " * mark.column + "^"
            msg = """Syntax Error while loading YAML script, %s
Note: The error may actually appear before this position: line %s, column %s

%s
%s
%s""" % (path, mark.line + 1, mark.column + 1, before_probline, probline, arrow)

            unquoted_var = None
            if '{{' in probline and '}}' in probline:
                if '"{{' not in probline or "'{{" not in probline:
                    unquoted_var = True

            if not unquoted_var:
                msg = process_common_errors(msg, probline, mark.column)
            else:
                msg = msg + """
We could be wrong, but this one looks like it might be an issue with
missing quotes.  Always quote template expression brackets when they
start a value. For instance:

    with_items:
      - {{ foo }}

Should be written as:

    with_items:
      - "{{ foo }}"

"""
        else:
            # most likely displaying a file with sensitive content,
            # so don't show any of the actual lines of yaml just the
            # line number itself
            msg = """Syntax error while loading YAML script, %s
The error appears to have been on line %s, column %s, but may actually
be before there depending on the exact syntax problem.
""" % (path, mark.line + 1, mark.column + 1)

    else:
        # No problem markers means we have to throw a generic
        # "stuff messed up" type message. Sry bud.
        if path:
            msg = "Could not parse YAML. Check over %s again." % path
        else:
            msg = "Could not parse YAML."
    raise errors.AnsibleYAMLValidationFailed(msg)


def load_data(data):

    if isinstance(data, file):
        fd = open(f)
        data = fd.read()
        fd.close()

    if isinstance(data, basestring):
        try:
            return json.loads(data)
        except:
            return safe_load(data)

    raise AnsibleInternalError("expected file or string, got %s" % type(data))

def load_data_from_file(path, vault_password=None):
    '''
    Convert a yaml file to a data structure. 
    Was previously 'parse_yaml_from_file()'.
    '''

    data = None
    show_content = True

    try:
        data = open(path).read()
    except IOError:
        raise errors.AnsibleError("file could not read: %s" % path)

    vault = VaultLib(password=vault_password)
    if vault.is_encrypted(data):
        # if the file is encrypted and no password was specified,
        # the decrypt call would throw an error, but we check first
        # since the decrypt function doesn't know the file name
        if vault_password is None:
            raise errors.AnsibleError("A vault password must be specified to decrypt %s" % path)
        data = vault.decrypt(data)
        show_content = False

    try:
        return load_data(data)
    except YAMLError as exc:
        process_yaml_error(exc, data, path, show_content)
