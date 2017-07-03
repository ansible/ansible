# (c) 2014, Brian Coca, Josh Drake, et al
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
'''
DOCUMENTATION:
    cache: jsonfile
    short_description: JSON formatted files.
    description:
        - This cache uses JSON formatted, per host, files saved to the filesystem.
    version_added: "1.9"
    author: Brian Coca (@bcoca)
'''
# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import codecs

try:
    import simplejson as json
except ImportError:
    import json

from ansible.parsing.utils.jsonify import jsonify
from ansible.plugins.cache import BaseFileCacheModule


class CacheModule(BaseFileCacheModule):
    """
    A caching module backed by json files.
    """

    def _load(self, filepath):
        # Valid JSON is always UTF-8 encoded.
        with codecs.open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _dump(self, value, filepath):
        with codecs.open(filepath, 'w', encoding='utf-8') as f:
            f.write(jsonify(value, format=True))
