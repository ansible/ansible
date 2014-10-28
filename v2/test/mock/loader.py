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

from ansible.parsing.yaml import DataLoader

class DictDataLoader(DataLoader):

    def __init__(self, file_mapping=dict()):
        assert type(file_mapping) == dict

        self._file_mapping = file_mapping
        self._build_known_directories()

        super(DictDataLoader, self).__init__()

    def load_from_file(self, path):
        if path in self._file_mapping:
            return self.load(self._file_mapping[path], path)
        return None

    def path_exists(self, path):
        return path in self._file_mapping or path in self._known_directories

    def is_file(self, path):
        return path in self._file_mapping

    def is_directory(self, path):
        return path in self._known_directories

    def _add_known_directory(self, directory):
        if directory not in self._known_directories:
            self._known_directories.append(directory)

    def _build_known_directories(self):
        self._known_directories  = []
        for path in self._file_mapping:
            dirname = os.path.dirname(path)
            while dirname not in ('/', ''):
                self._add_known_directory(dirname)
                dirname = os.path.dirname(dirname)

    def push(self, path, content):
        rebuild_dirs = False
        if path not in self._file_mapping:
            rebuild_dirs = True
    
        self._file_mapping[path] = content

        if rebuild_dirs:
            self._build_known_directories()

    def pop(self, path):
        if path in self._file_mapping:
            del self._file_mapping[path]
            self._build_known_directories()

    def clear(self):
        self._file_mapping = dict()
        self._known_directories = []

