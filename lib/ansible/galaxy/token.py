########################################################################
#
# (C) 2015, Chris Houseknecht <chouse@ansible.com>
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
#
########################################################################
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
from stat import S_IRUSR, S_IWUSR

import yaml

from ansible import constants as C
from ansible.module_utils._text import to_bytes, to_text
from ansible.utils.display import Display

display = Display()


class GalaxyToken(object):
    ''' Class to storing and retrieving local galaxy token '''

    def __init__(self):
        self.b_file = to_bytes(C.GALAXY_TOKEN_PATH)
        self.config = yaml.safe_load(self.__open_config_for_read())
        if not self.config:
            self.config = {}

    def __open_config_for_read(self):

        f = None
        action = 'Opened'
        if not os.path.isfile(self.b_file):
            # token file not found, create and chomd u+rw
            f = open(self.b_file, 'w')
            f.close()
            os.chmod(self.b_file, S_IRUSR | S_IWUSR)  # owner has +rw
            action = 'Created'

        f = open(self.b_file, 'r')
        display.vvv('%s %s' % (action, to_text(self.b_file)))

        return f

    def set(self, token):
        self.config['token'] = token
        self.save()

    def get(self):
        return self.config.get('token', None)

    def save(self):
        with open(self.b_file, 'w') as f:
            yaml.safe_dump(self.config, f, default_flow_style=False)
