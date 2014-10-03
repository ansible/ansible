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

from errors import AnsibleError
from playbook.tag import Tag

class Base(object):

    def __init__(self):
        self._tags = Tag()

    def _ensure_int(self, attr, default=0):
        value = getattr(self, attr)
        if value is None:
            setattr(self, attr, default)
        elif not isinstance(value, int):
            try:
                setattr(self, attr, int(value))
            except ValueError:
                raise AnsibleError("failed to set attr %s to an integer, got '%s' which is a %s" % (attr, value, type(value)))

    def _ensure_bool(self, attr, default=False):
        value = getattr(self, attr)
        if value is None:
            setattr(self, attr, default)
        elif not isinstance(value, bool):
            setattr(self, attr, utils.boolean(value))

    def _ensure_basestring(self, attr, default=""):
        value = getattr(self, attr)
        if value is None:
            setattr(self, attr, default)
        elif not isinstance(value, basestring):
            setattr(self, attr, "%s" % value)

    def _ensure_list_of_strings(self, attr, default=[]):
        value = getattr(self, attr)
        if value is None:
            setattr(self, attr, default)
        elif not isinstance(value, list):
            setattr(self, attr, [ str(value) ])
        else:
            changed = False
            for idx,val in enumerate(value):
                if not isinstance(val, basestring):
                    value[idx] = str(val)
                    changed = True
            if changed:
                setattr(self, attr, value)
