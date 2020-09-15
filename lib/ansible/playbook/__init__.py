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

from ansible import constants as C
from ansible.errors import AnsibleParserError
from ansible.module_utils._text import to_text, to_native
from ansible.playbook.play import Play
from ansible.playbook.playbook_include import PlaybookInclude
from ansible.plugins.loader import add_all_plugin_dirs
from ansible.utils.display import Display

display = Display()


__all__ = ['Playbook']


class Playbook:

    def __init__(self, loader):
        # Entries in the datastructure of a playbook may
        # be either a play or an include statement
        self._entries = []
        self._basedir = to_text(os.getcwd(), errors='surrogate_or_strict')
        self._loader = loader
        self._file_name = None

    @staticmethod
    def load(file_name, variable_manager=None, loader=None):
        pb = Playbook(loader=loader)
        pb._load_playbook_data(file_name=file_name, variable_manager=variable_manager)
        return pb

    def _load_playbook_data(self, file_name, variable_manager, vars=None):

        if os.path.isabs(file_name):
            self._basedir = os.path.dirname(file_name)
        else:
            self._basedir = os.path.normpath(os.path.join(self._basedir, os.path.dirname(file_name)))

        # set the loaders basedir
        cur_basedir = self._loader.get_basedir()
        self._loader.set_basedir(self._basedir)

        add_all_plugin_dirs(self._basedir)

        self._file_name = file_name

        try:
            ds = self._loader.load_from_file(os.path.basename(file_name))
        except UnicodeDecodeError as e:
            raise AnsibleParserError("Could not read playbook (%s) due to encoding issues: %s" % (file_name, to_native(e)))

        # check for errors and restore the basedir in case this error is caught and handled
        if ds is None:
            self._loader.set_basedir(cur_basedir)
            raise AnsibleParserError("Empty playbook, nothing to do", obj=ds)
        elif not isinstance(ds, list):
            self._loader.set_basedir(cur_basedir)
            raise AnsibleParserError("A playbook must be a list of plays, got a %s instead" % type(ds), obj=ds)
        elif not ds:
            display.deprecated("Empty plays will currently be skipped, in the future they will cause a syntax error", version='2.12')

        # Parse the playbook entries. For plays, we simply parse them
        # using the Play() object, and includes are parsed using the
        # PlaybookInclude() object
        for entry in ds:
            if not isinstance(entry, dict):
                # restore the basedir in case this error is caught and handled
                self._loader.set_basedir(cur_basedir)
                raise AnsibleParserError("playbook entries must be either a valid play or an include statement", obj=entry)

            if any(action in entry for action in ('import_playbook', 'include')):
                if 'include' in entry:
                    display.deprecated("'include' for playbook includes. You should use 'import_playbook' instead", version="2.12")
                pb = PlaybookInclude.load(entry, basedir=self._basedir, variable_manager=variable_manager, loader=self._loader)
                if pb is not None:
                    self._entries.extend(pb._entries)
                else:
                    which = entry.get('import_playbook', entry.get('include', entry))
                    display.display("skipping playbook '%s' due to conditional test failure" % which, color=C.COLOR_SKIP)
            else:
                entry_obj = Play.load(entry, variable_manager=variable_manager, loader=self._loader, vars=vars)
                self._entries.append(entry_obj)

        # we're done, so restore the old basedir in the loader
        self._loader.set_basedir(cur_basedir)

    def get_loader(self):
        return self._loader

    def get_plays(self):
        return self._entries[:]
