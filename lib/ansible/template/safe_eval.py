# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ast
import sys

from ansible.compat.six import string_types
from ansible.compat.six.moves import builtins

from ansible import constants as C
from ansible.plugins import filter_loader, test_loader

def safe_eval(expr, locals={}, include_exceptions=False):
    '''
    This is intended for allowing things like:
    with_items: a_list_variable

    Where Jinja2 would return a string but we do not want to allow it to
    call functions (outside of Jinja2, where the env is constrained). If
    the input data to this function came from an untrusted (remote) source,
    it should first be run through _clean_data_struct() to ensure the data
    is further sanitized prior to evaluation.

    Based on:
    http://stackoverflow.com/questions/12523516/using-ast-and-whitelists-to-make-pythons-eval-safe
    '''

    # define certain JSON types
    # eg. JSON booleans are unknown to python eval()
    JSON_TYPES = {
        'false': False,
        'null': None,
        'true': True,
    }

    # this is the whitelist of AST nodes we are going to
    # allow in the evaluation. Any node type other than
    # those listed here will raise an exception in our custom
    # visitor class defined below.
    SAFE_NODES = set(
        (
            ast.Add,
            ast.BinOp,
            ast.Call,
            ast.Compare,
            ast.Dict,
            ast.Div,
            ast.Expression,
            ast.List,
            ast.Load,
            ast.Mult,
            ast.Num,
            ast.Name,
            ast.Str,
            ast.Sub,
            ast.Tuple,
            ast.UnaryOp,
        )
    )

    # AST node types were expanded after 2.6
    if sys.version_info[:2] >= (2, 7):
        SAFE_NODES.update(
            set(
                (ast.Set,)
            )
        )

    # And in Python 3.4 too
    if sys.version_info[:2] >= (3, 4):
        SAFE_NODES.update(
            set(
                (ast.NameConstant,)
            )
        )

    filter_list = []
    for filter in filter_loader.all():
        filter_list.extend(filter.filters().keys())

    test_list = []
    for test in test_loader.all():
        test_list.extend(test.tests().keys())

    CALL_WHITELIST = C.DEFAULT_CALLABLE_WHITELIST + filter_list + test_list

    class CleansingNodeVisitor(ast.NodeVisitor):
        def generic_visit(self, node, inside_call=False):
            if type(node) not in SAFE_NODES:
                raise Exception("invalid expression (%s)" % expr)
            elif isinstance(node, ast.Call):
                inside_call = True
            elif isinstance(node, ast.Name) and inside_call:
                if hasattr(builtins, node.id) and node.id not in CALL_WHITELIST:
                    raise Exception("invalid function: %s" % node.id)
            # iterate over all child nodes
            for child_node in ast.iter_child_nodes(node):
                self.generic_visit(child_node, inside_call)

    if not isinstance(expr, string_types):
        # already templated to a datastructure, perhaps?
        if include_exceptions:
            return (expr, None)
        return expr

    cnv = CleansingNodeVisitor()
    try:
        parsed_tree = ast.parse(expr, mode='eval')
        cnv.visit(parsed_tree)
        compiled = compile(parsed_tree, expr, 'eval')
        result = eval(compiled, JSON_TYPES, dict(locals))

        if include_exceptions:
            return (result, None)
        else:
            return result
    except SyntaxError as e:
        # special handling for syntax errors, we just return
        # the expression string back as-is
        if include_exceptions:
            return (expr, None)
        return expr
    except Exception as e:
        if include_exceptions:
            return (expr, e)
        return expr

