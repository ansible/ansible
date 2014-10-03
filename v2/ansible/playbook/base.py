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

#from ansible.cmmon.errors import AnsibleError
#from playbook.tag import Tag
from ansible.playbook.attribute import Attribute, FieldAttribute

class Base(object):

    def __init__(self):
        self._data = dict()
        self._attributes = dict()

    def load_data(self, ds):
        ''' walk the input datastructure and assign any values '''

        assert ds is not None

        for name in self.__class__.__dict__:

            print "DEBUG: processing attribute: %s" % name

            attribute = self.__class__.__dict__[name]

            if isinstance(attribute, FieldAttribute):
                method = getattr(self, '_load_%s' % name, None)
                if method:
                    self._attributes[name] = method(self, attribute)
                else:
                    if name in ds:
                        self._attributes[name] = ds[name]

             # implement PluginAtrribute which allows "with_" and "action" aliases.

        return self


    def attribute_value(self, name):
        return self._attributes[name]

    def validate(self):

        for name in self.__dict__:
            attribute = self.__dict__[name]
            if instanceof(attribute, FieldAttribute):
                method = getattr(self, '_validate_%s' % (prefix, name), None)
                if method:
                    method(self, attribute)

    def post_validate(self, runner_context):
        raise exception.NotImplementedError

    # TODO: __getattr__ that looks inside _attributes
