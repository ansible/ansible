# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2014, Serge van Ginderachter <serge@vanginderachter.be>
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
from __future__ import annotations

from ansible.plugins import AnsiblePlugin
from ansible.utils.path import basedir
from ansible.utils.display import Display

display = Display()


class BaseVarsPlugin(AnsiblePlugin):

    """
    Loads variables for groups and/or hosts
    """
    is_stateless = False

    def __init__(self):
        """ constructor """
        super(BaseVarsPlugin, self).__init__()
        self._display = display

    def get_vars(self, loader, path, entities):
        """ Gets variables. """
        self._basedir = basedir(path)
