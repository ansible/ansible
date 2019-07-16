# (c) 2018 Toshio Kuratomi <tkuratomi@ansible.com>
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
Compat distro library.
'''
# The following makes it easier for us to script updates of the bundled code
_BUNDLED_METADATA = {"pypi_name": "distro", "version": "1.3.0"}

# The following additional changes have been made:
# * The import of argparse has been moved to __main__ (py2.6 compat)
# * A format string including {} has been changed to {0} (py2.6 compat)
# * Port two calls from subprocess.check_output to subprocess.Popen().communicate()
#   (py2.6 compat)


import sys

try:
    import distro as _system_distro
except ImportError:
    _system_distro = None

if _system_distro:
    distro = _system_distro
else:
    # Our bundled copy
    from ansible.module_utils.distro import _distro as distro
sys.modules['ansible.module_utils.distro'] = distro
