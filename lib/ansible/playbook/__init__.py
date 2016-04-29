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

from ansible.errors import AnsibleParserError
from ansible.galaxy import Galaxy
from ansible.playbook.role.requirement import read_roles_file, install_roles
from ansible.playbook.play import Play
from ansible.playbook.playbook_include import PlaybookInclude
from ansible.plugins import get_all_plugin_loaders
from ansible.template import Templar
from ansible import constants as C

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


__all__ = ['Playbook']


class Playbook:

    def __init__(self, loader):
        # Entries in the datastructure of a playbook may
        # be either a play or an include statement
        self._entries = []
        self._basedir = os.getcwd()
        self._loader  = loader
        self._file_name = None

    @staticmethod
    def load(file_name, variable_manager=None, loader=None):
        pb = Playbook(loader=loader)
        pb._load_playbook_data(file_name=file_name, variable_manager=variable_manager)
        return pb

    def _load_playbook_data(self, file_name, variable_manager):

        if os.path.isabs(file_name):
            self._basedir = os.path.dirname(file_name)
        else:
            self._basedir = os.path.normpath(os.path.join(self._basedir, os.path.dirname(file_name)))

        # set the loaders basedir
        self._loader.set_basedir(self._basedir)

        self._file_name = file_name

        # dynamically load any plugins from the playbook directory
        for name, obj in get_all_plugin_loaders():
            if obj.subdir:
                plugin_path = os.path.join(self._basedir, obj.subdir)
                if os.path.isdir(plugin_path):
                    obj.add_directory(plugin_path)

        ds = self._loader.load_from_file(os.path.basename(file_name))
        if not isinstance(ds, list):
            raise AnsibleParserError("playbooks must be a list of plays", obj=ds)

        # Parse the playbook entries. For plays, we simply parse them
        # using the Play() object, and includes are parsed using the
        # PlaybookInclude() object
        for entry in ds:
            if not isinstance(entry, dict):
                raise AnsibleParserError("playbook entries must be either a valid play or an include statement", obj=entry)

            if 'include' in entry:
                pb = PlaybookInclude.load(entry, basedir=self._basedir, variable_manager=variable_manager, loader=self._loader)
                if pb is not None:
                    self._entries.extend(pb._entries)
                else:
                    display.display("skipping playbook include '%s' due to conditional test failure" % entry.get('include', entry), color=C.COLOR_SKIP)
            else:
                all_vars = variable_manager.get_vars(loader=self._loader)
                templar = Templar(loader=self._loader, variables=all_vars)

                # Install roles if roles_file is present in play or on command line
                import pdb
                pdb.set_trace()
                roles_file = entry.get('roles_file')
                if roles_file:
                    if C.AUTO_INSTALL_ROLES:
                        if templar._contains_vars(roles_file):
                             roles_file = templar.template(roles_file)
                        roles_path = entry.get('roles_path')
                        if roles_path and templar._contains_vars(roles_path):
                            roles_path = templar.template(roles_path)
                        galaxy = Galaxy(roles_path, ignore_certs=False, api_server=C.GALAXY_SERVER,
                                        force=True, no_deps=False, ignore_errors=False)
                        roles_left = read_roles_file(galaxy, roles_file)
                        install_roles(roles_left, galaxy, use_whitelist=True)
                    else:
                        display.warning("Found roles_file in playbook %s but auto_install_roles is not on in configuration" % file_name)

                entry_obj = Play.load(entry, variable_manager=variable_manager, loader=self._loader)
                self._entries.append(entry_obj)

    def get_loader(self):
        return self._loader

    def get_plays(self):
        return self._entries[:]
