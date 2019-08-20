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


class NoTokenSentinel(object):
    """ Represents an ansible.cfg server with not token defined (will ignore cmdline and GALAXY_TOKEN_PATH. """
    def __new__(cls, *args, **kwargs):
        return cls


class GalaxyToken(object):
    ''' Class to storing and retrieving local galaxy token '''

    def __init__(self, token=None):
        self.b_file = to_bytes(C.GALAXY_TOKEN_PATH, errors='surrogate_or_strict')
        # Done so the config file is only opened when set/get/save is called
        self._config = None
        self._token = token

    @property
    def config(self):
        if not self._config:
            self._config = self._read()

        # Prioritise the token passed into the constructor
        if self._token:
            self._config['token'] = None if self._token is NoTokenSentinel else self._token

        return self._config

    def _read(self):
        action = 'Opened'
        if not os.path.isfile(self.b_file):
            # token file not found, create and chomd u+rw
            open(self.b_file, 'w').close()
            os.chmod(self.b_file, S_IRUSR | S_IWUSR)  # owner has +rw
            action = 'Created'

        with open(self.b_file, 'r') as f:
            config = yaml.safe_load(f)

        display.vvv('%s %s' % (action, to_text(self.b_file)))

        return config or {}

    def set(self, token):
        self._token = token
        self.save()

    def get(self):
        return self.config.get('token', None)

    def save(self):
        with open(self.b_file, 'w') as f:
            yaml.safe_dump(self.config, f, default_flow_style=False)
