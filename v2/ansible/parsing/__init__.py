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

import json

from ansible.errors import AnsibleParserError, AnsibleInternalError
from ansible.parsing.vault import VaultLib
from ansible.parsing.yaml import safe_load

def load(data):

    if hasattr(data, 'read') and hasattr(data.read, '__call__'):
        data = data.read()

    if isinstance(data, basestring):
        try:
            try:
                return json.loads(data)
            except:
                return safe_load(data)
        except:
            raise AnsibleParserError("data was not valid yaml")

    raise AnsibleInternalError("expected file or string, got %s" % type(data))

