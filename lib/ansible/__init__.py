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

# patch Jinja2 >= 3.0 for backwards compatibility
try:
    import sys as _sys
    from jinja2.filters import pass_context as _passctx, pass_environment as _passenv, pass_eval_context as _passevalctx
    _mod = _sys.modules['jinja2.filters']
    _mod.contextfilter = _passctx
    _mod.environmentfilter = _passenv
    _mod.evalcontextfilter = _passevalctx
except ImportError:
    _sys = None

# Note: Do not add any code to this file.  The ansible module may be
# a namespace package when using Ansible-2.1+ Anything in this file may not be
# available if one of the other packages in the namespace is loaded first.
#
# This is for backwards compat.  Code should be ported to get these from
# ansible.release instead of from here.
from ansible.release import __version__, __author__
