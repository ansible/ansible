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

import os
import subprocess

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.utils.path import is_executable

def read_vault_file(vault_password_file):
    """
    Read a vault password from a file or if executable, execute the script and
    retrieve password from STDOUT
    """

    this_path = os.path.realpath(os.path.expanduser(vault_password_file))
    if not os.path.exists(this_path):
        raise AnsibleError("The vault password file %s was not found" % this_path)

    if is_executable(this_path):
        try:
            # STDERR not captured to make it easier for users to prompt for input in their scripts
            p = subprocess.Popen(this_path, stdout=subprocess.PIPE)
        except OSError as e:
            raise AnsibleError("Problem running vault password script %s (%s). If this is not a script, remove the executable bit from the file." % (' '.join(this_path), e))
        stdout, stderr = p.communicate()
        vault_pass = stdout.strip('\r\n')
    else:
        try:
            f = open(this_path, "rb")
            vault_pass=f.read().strip()
            f.close()
        except (OSError, IOError) as e:
            raise AnsibleError("Could not read vault password file %s: %s" % (this_path, e))

    return vault_pass

