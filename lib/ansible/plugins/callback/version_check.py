# (c) 2015, Tadej Janez <tadej.j@nez.si>
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

import os.path

from ansible.plugins.callback import CallbackBase
from ansible import __version__ as ansible_version


REQUIREMENTS_FILE = "requirements.txt"


def get_requirements_version(req_path):
    """
    Return Ansible version specified in the given requirements file.

    If the version of Ansible is not specified, return None.

    """
    version = None
    with open(req_path) as req_file:
        for req in req_file.readlines():
            req = req.strip()
            if req.lower().startswith("ansible"):
                req_split = req.split("==")
                if len(req_split) == 2:
                    version = req_split[1]
                break
    return version


class CallbackModule(CallbackBase):
    """
    This callback module checks if the Ansible version that is used to run the
    playbook matches the Ansible version specified in the requirements file.

    To use it, just place 'requirements.txt' file in your playbook directory
    with the following contents (replace '2.0.0' with your required version):

    ansible=2.0.0

    NOTE: This file is an ordinary Python requirements file and can contain
    other Python packages.

    Then enable the callback by adding it to the 'callback_whitelist' in your
    Ansible configuration file:
    http://docs.ansible.com/ansible/intro_configuration.html#callback-whitelist

    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'version_check'
    CALLBACK_NEEDS_WHITELIST = True

    def v2_playbook_on_start(self, playbook):
        """
        Check if Ansible version that is used to run the playbook matches the
        Ansible version specified in the requirements file.

        If the versions don't match, display warning.

        """
        req_path = os.path.join(playbook._basedir, REQUIREMENTS_FILE)
        req_version = get_requirements_version(req_path)
        if req_version is None:
            msg = ("Ansible version not found in the requirements file at "
                   "'%s'!" % req_path)
            self._display.warning(msg)
        elif ansible_version != req_version:
            msg = ("Ansible version you are running (%s) does not match the "
                   "Ansible version specified in the requirements file (%s) "
                   "at '%s'!" % (ansible_version, req_version, req_path))
            self._display.warning(msg)
