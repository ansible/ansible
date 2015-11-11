#!/usr/bin/env python

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
import yaml
from stat import *

class GalaxyConfig(object):
    ''' Class to manage ~/.ansible_galaxy/config.yml '''

    def __init__(self, galaxy):
        self.galaxy = galaxy
        self.display = galaxy.display
        self.path = os.path.expanduser("~") + '/.ansible_galaxy'
        self.file = self.path + '/config.yml'
        self.config = yaml.safe_load(self.__open_config_for_read())
        if not self.config:
            self.config = {}
        
    def __open_config_for_read(self):
        if os.path.isfile(self.file):
            self.display.vvv('Opened galaxy config %s' % self.file)
            return open(self.file, 'r')
        # config.yml not found, create and chomd u+rw
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
            os.chmod(self.path,S_IRWXU) # owner has +rwx
        f = open(self.file,'w')
        f.close()
        os.chmod(self.file,S_IRUSR|S_IWUSR) # owner has +rw
        self.display.vvv('Created galaxy config %s' % self.file) 
        return open(self.file, 'r')

    def set_key(self, key, value): 
        if value in ['true','yes','True','Yes']:
            val = True
        elif value in ['false','no','False','no']:
            val = False
        else:
            val = value
        self.config[key] = val
    
    def remove_key(self, key):
        if key in self.config:
            self.config.pop(key)

    def get_key(self, key):
        val = self.config.get(key, None)
        if val in ['true','yes','True','Yes']:
            val = True
        elif val in ['false','no','False','No']:
            val = False
        return val 

    def save(self):
        with open(self.file,'w') as f:
            yaml.safe_dump(self.config,f,default_flow_style=False)
        