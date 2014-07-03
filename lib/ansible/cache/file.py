# (c) 2014, Michael DeHaan <michael.dehaan@gmail.com>
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
from __future__ import absolute_import

import collections
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime

from ansible import constants as C
from ansible.cache.memory import CacheModule as MemoryCacheModule


class CacheModule(MemoryCacheModule):
    def __init__(self):
        super(CacheModule, self).__init__()
        self._timeout = int(C.CACHE_PLUGIN_TIMEOUT)
        self._filename = '/tmp/ansible_facts.json'

        if os.access(self._filename, os.R_OK):
            mtime = datetime.fromtimestamp(os.path.getmtime(self._filename))
            if self._timeout == 0 or (datetime.now() - mtime).total_seconds() < self._timeout:
                with open(self._filename, 'rb') as f:
                    # we could make assumptions about the MemoryCacheModule here if we wanted
                    # to be more efficient, but performance isn't the priority with this module
                    data = json.load(f)
                    if isinstance(data, collections.Mapping):
                        for k, v in data.items():
                            super(CacheModule, self).set(k, v)

    def set(self, *args, **kwargs):
        super(CacheModule, self).set(*args, **kwargs)
        self.fsync()

    def delete(self, *args, **kwargs):
        super(CacheModule, self).delete(*args, **kwargs)
        self.fsync()

    def fsync(self):
        temp = tempfile.TemporaryFile('r+b')

        try:
            json.dump(self._cache, temp, separators=(',', ':'))
            temp.seek(0)
            with open(self._filename, 'w+b') as f:
                shutil.copyfileobj(temp, f)
        finally:
            temp.close()

    def flush(self):
        super(CacheModule, self).flush()
        self.fsync()
