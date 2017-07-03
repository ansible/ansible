# (c) 2017, Toshio Kuratomi <tkuratomi@ansible.com>
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

import ast
import sys

import yaml

from ansible.module_utils._text import to_text


class ParseError(Exception):
    """Thrown when parsing a file fails"""
    pass


def _seek_end_of_dict(module_data, start_line, start_col, next_node_line, next_node_col):
    """Look for the end of a dict in a set of lines

    We know the starting position of the dict and we know the start of the
    next code node but in between there may be multiple newlines and comments.
    There may also be multiple python statements on the same line (separated
    by semicolons)

    Examples::
        ANSIBLE_METADATA = {[..]}
        DOCUMENTATION = [..]

        ANSIBLE_METADATA = {[..]} # Optional comments with confusing junk => {}
        # Optional comments {}
        DOCUMENTATION = [..]

        ANSIBLE_METADATA = {
            [..]
            }
        # Optional comments {}
        DOCUMENTATION = [..]

        ANSIBLE_METADATA = {[..]} ; DOCUMENTATION = [..]

        ANSIBLE_METADATA = {}EOF
    """
    if next_node_line is None:
        # The dict is the last statement in the file
        snippet = module_data.splitlines()[start_line:]
        next_node_col = 0
        # Include the last line in the file
        last_line_offset = 0
    else:
        # It's somewhere in the middle so we need to separate it from the rest
        snippet = module_data.splitlines()[start_line:next_node_line]
        # Do not include the last line because that's where the next node
        # starts
        last_line_offset = 1

    if next_node_col == 0:
        # This handles all variants where there are only comments and blank
        # lines between the dict and the next code node

        # Step backwards through all the lines in the snippet
        for line_idx, line in tuple(reversed(tuple(enumerate(snippet))))[last_line_offset:]:
            end_col = None
            # Step backwards through all the characters in the line
            for col_idx, char in reversed(tuple(enumerate(c for c in line))):
                if not isinstance(char, bytes):
                    # Python3 wart.  slicing a byte string yields integers
                    char = bytes((char,))
                if char == b'}' and end_col is None:
                    # Potentially found the end of the dict
                    end_col = col_idx

                elif char == b'#' and end_col is not None:
                    # The previous '}' was part of a comment.  Keep trying
                    end_col = None

            if end_col is not None:
                # Found the end!
                end_line = start_line + line_idx
                break
        else:
            raise ParseError('Unable to find the end of dictionary')
    else:
        # Harder cases involving multiple statements on one line
        # Good Ansible Module style doesn't do this so we're just going to
        # treat this as an error for now:
        raise ParseError('Multiple statements per line confuses the module metadata parser.')

    return end_line, end_col


def _seek_end_of_string(module_data, start_line, start_col, next_node_line, next_node_col):
    """
    This is much trickier than finding the end of a dict.  A dict has only one
    ending character, "}".  Strings have four potential ending characters.  We
    have to parse the beginning of the string to determine what the ending
    character will be.

    Examples:
        ANSIBLE_METADATA = '''[..]''' # Optional comment with confusing chars '''
        # Optional comment with confusing chars '''
        DOCUMENTATION = [..]

        ANSIBLE_METADATA = '''
            [..]
            '''
        DOCUMENTATIONS = [..]

        ANSIBLE_METADATA = '''[..]''' ; DOCUMENTATION = [..]

        SHORT_NAME = ANSIBLE_METADATA = '''[..]''' ; DOCUMENTATION = [..]

    String marker variants:
        * '[..]'
        * "[..]"
        * '''[..]'''
        * \"\"\"[..]\"\"\"

    Each of these come in u, r, and b variants:
        * '[..]'
        * u'[..]'
        * b'[..]'
        * r'[..]'
        * ur'[..]'
        * ru'[..]'
        * br'[..]'
        * b'[..]'
        * rb'[..]'
    """
    raise NotImplementedError('Finding end of string not yet implemented')


def extract_metadata(module_ast=None, module_data=None, offsets=False):
    """Extract the metadata from a module

    :kwarg module_ast: ast representation of the module.  At least one of this
        or ``module_data`` must be given.  If the code calling
        :func:`extract_metadata` has already parsed the module_data into an ast,
        giving the ast here will save reparsing it.
    :kwarg module_data: Byte string containing a module's code.  At least one
        of this or ``module_ast`` must be given.
    :kwarg offsets: If set to True, offests into the source code will be
        returned.  This requires that ``module_data`` be set.
    :returns: a tuple of metadata (a dict), line the metadata starts on,
        column the metadata starts on, line the metadata ends on, column the
        metadata ends on, and the names the metadata is assigned to.  One of
        the names the metadata is assigned to will be ANSIBLE_METADATA.  If no
        metadata is found, the tuple will be (None, -1, -1, -1, -1, None).
        If ``offsets`` is False then the tuple will consist of
        (metadata, -1, -1, -1, -1, None).
    :raises ansible.parsing.metadata.ParseError: if ``module_data`` does not parse
    :raises SyntaxError: if ``module_data`` is needed but does not parse correctly
    """
    if offsets and module_data is None:
        raise TypeError('If offsets is True then module_data must also be given')

    if module_ast is None and module_data is None:
        raise TypeError('One of module_ast or module_data must be given')

    metadata = None
    start_line = -1
    start_col = -1
    end_line = -1
    end_col = -1
    targets = None
    if module_ast is None:
        module_ast = ast.parse(module_data)

    for root_idx, child in reversed(list(enumerate(module_ast.body))):
        if isinstance(child, ast.Assign):
            for target in child.targets:
                if target.id == 'ANSIBLE_METADATA':
                    metadata = ast.literal_eval(child.value)
                    if not offsets:
                        continue

                    try:
                        # Determine where the next node starts
                        next_node = module_ast.body[root_idx + 1]
                        next_lineno = next_node.lineno
                        next_col_offset = next_node.col_offset
                    except IndexError:
                        # Metadata is defined in the last node of the file
                        next_lineno = None
                        next_col_offset = None

                    if isinstance(child.value, ast.Dict):
                        # Determine where the current metadata ends
                        end_line, end_col = _seek_end_of_dict(module_data,
                                                              child.lineno - 1,
                                                              child.col_offset,
                                                              next_lineno,
                                                              next_col_offset)

                    elif isinstance(child.value, ast.Str):
                        metadata = yaml.safe_load(child.value.s)
                        end_line, end_col = _seek_end_of_string(module_data,
                                                                child.lineno - 1,
                                                                child.col_offset,
                                                                next_lineno,
                                                                next_col_offset)
                    elif isinstance(child.value, ast.Bytes):
                        metadata = yaml.safe_load(to_text(child.value.s, errors='surrogate_or_strict'))
                        end_line, end_col = _seek_end_of_string(module_data,
                                                                child.lineno - 1,
                                                                child.col_offset,
                                                                next_lineno,
                                                                next_col_offset)
                    else:
                        raise ParseError('Ansible plugin metadata must be a dict')

                    # Do these after the if-else so we don't pollute them in
                    # case this was a false positive
                    start_line = child.lineno - 1
                    start_col = child.col_offset
                    targets = [t.id for t in child.targets]
                    break

        if metadata is not None:
            # Once we've found the metadata we're done
            break

    return metadata, start_line, start_col, end_line, end_col, targets
