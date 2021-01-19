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

from ansible import constants as C
from ansible.module_utils.common.text.converters import container_to_text, to_native
from ansible.module_utils.six import string_types, PY2
from ansible.module_utils.six.moves import builtins
from ansible.plugins.loader import filter_loader, test_loader


def safe_eval(expr, locals=None, include_exceptions=False):
    '''
    This is intended for allowing things like:
    with_items: a_list_variable

    Where Jinja2 would return a string but we do not want to allow it to
    call functions (outside of Jinja2, where the env is constrained).

    Based on:
    http://stackoverflow.com/questions/12523516/using-ast-and-whitelists-to-make-pythons-eval-safe
    '''
    locals = {} if locals is None else locals

    # define certain JSON types
    # eg. JSON booleans are unknown to python eval()
    OUR_GLOBALS = {
        '__builtins__': {},  # avoid global builtins as per eval docs
        'false': False,
        'null': None,
        'true': True,
        # also add back some builtins we do need
        'True': True,
        'False': False,
        'None': None
    }

    # this is the whitelist of AST nodes we are going to
    # allow in the evaluation. Any node type other than
    # those listed here will raise an exception in our custom
    # visitor class defined below.
    SAFE_NODES = set(
        (
            ast.Add,
            ast.BinOp,
            # ast.Call,
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
            ast.USub,
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

    # And in Python 3.6 too, although not encountered until Python 3.8, see https://bugs.python.org/issue32892
    if sys.version_info[:2] >= (3, 6):
        SAFE_NODES.update(
            set(
                (ast.Constant,)
            )
        )

    filter_list = []
    for filter_ in filter_loader.all():
        filter_list.extend(filter_.filters().keys())

    test_list = []
    for test in test_loader.all():
        test_list.extend(test.tests().keys())

    CALL_ENABLED = C.CALLABLE_ACCEPT_LIST + filter_list + test_list

    class CleansingNodeVisitor(ast.NodeVisitor):
        def generic_visit(self, node, inside_call=False):
            if type(node) not in SAFE_NODES:
                raise Exception("invalid expression (%s)" % expr)
            elif isinstance(node, ast.Call):
                inside_call = True
            elif isinstance(node, ast.Name) and inside_call:
                # Disallow calls to builtin functions that we have not vetted
                # as safe.  Other functions are excluded by setting locals in
                # the call to eval() later on
                if hasattr(builtins, node.id) and node.id not in CALL_ENABLED:
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
        compiled = compile(parsed_tree, '<expr %s>' % to_native(expr), 'eval')
        # Note: passing our own globals and locals here constrains what
        # callables (and other identifiers) are recognized.  this is in
        # addition to the filtering of builtins done in CleansingNodeVisitor
        result = eval(compiled, OUR_GLOBALS, dict(locals))
        if PY2:
            # On Python 2 u"{'key': 'value'}" is evaluated to {'key': 'value'},
            # ensure it is converted to {u'key': u'value'}.
            result = container_to_text(result)

        if include_exceptions:
            return (result, None)
        else:
            return result
    except SyntaxError as e:
        # special handling for syntax errors, we just return
        # the expression string back as-is to support late evaluation
        if include_exceptions:
            return (expr, None)
        return expr
    except Exception as e:
        if include_exceptions:
            return (expr, e)
        return expr
