# (c) 2014, Toshio Kuratomi <tkuratomi@ansible.com>
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

'''
Compat six library.  RHEL7 has python-six 1.3.0 which is too old
'''
# The following makes it easier for us to script updates of the bundled code
_BUNDLED_METADATA = { "pypi_name": "six", "version": "1.10.0" }

import os.path

try:
    import six as _system_six
except ImportError:
    _system_six = None

if _system_six:
    # If we need some things from even newer versions of six, then we need to
    # use our bundled copy instead

       if ( # Added in six-1.8.0
            not hasattr(_system_six.moves, 'shlex_quote') or
            # Added in six-1.4.0
            not hasattr(_system_six, 'byte2int') or
            not hasattr(_system_six, 'add_metaclass') or
            not hasattr(_system_six.moves, 'urllib')
            ):

        _system_six = False

if _system_six:
    six = _system_six
else:
    from . import _six as six
six_py_file = '{0}.py'.format(os.path.splitext(six.__file__)[0])
exec(open(six_py_file, 'rb').read())
