# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
# Copyright (c) 2015, Marius Gedminas
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys


def get_exception():
    """Get the current exception.

    This code needs to work on Python 2.4 through 3.x, so we cannot use
    "except Exception, e:" (SyntaxError on Python 3.x) nor
    "except Exception as e:" (SyntaxError on Python 2.4-2.5).
    Instead we must use ::

        except Exception:
            e = get_exception()

    """
    return sys.exc_info()[1]

try:
    # Python 2.6+
    from ast import literal_eval
except ImportError:
    # a replacement for literal_eval that works with python 2.4. from:
    # https://mail.python.org/pipermail/python-list/2009-September/551880.html
    # which is essentially a cut/paste from an earlier (2.6) version of python's
    # ast.py
    from compiler import ast, parse
    from ansible.module_utils.six import binary_type, integer_types, string_types, text_type

    def literal_eval(node_or_string):
        """
        Safely evaluate an expression node or a string containing a Python
        expression.  The string or node provided may only consist of the  following
        Python literal structures: strings, numbers, tuples, lists, dicts,  booleans,
        and None.
        """
        _safe_names = {'None': None, 'True': True, 'False': False}
        if isinstance(node_or_string, string_types):
            node_or_string = parse(node_or_string, mode='eval')
        if isinstance(node_or_string, ast.Expression):
            node_or_string = node_or_string.node

        def _convert(node):
            if isinstance(node, ast.Const) and isinstance(node.value, (text_type, binary_type, float, complex) + integer_types):
                return node.value
            elif isinstance(node, ast.Tuple):
                return tuple(map(_convert, node.nodes))
            elif isinstance(node, ast.List):
                return list(map(_convert, node.nodes))
            elif isinstance(node, ast.Dict):
                return dict((_convert(k), _convert(v)) for k, v in node.items())
            elif isinstance(node, ast.Name):
                if node.name in _safe_names:
                    return _safe_names[node.name]
            elif isinstance(node, ast.UnarySub):
                return -_convert(node.expr)
            raise ValueError('malformed string')
        return _convert(node_or_string)

__all__ = ('get_exception', 'literal_eval')
