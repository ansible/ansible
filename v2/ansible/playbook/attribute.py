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

#from ansible.common.errors import AnsibleError

class MyMeta(type):

    def __call__(self, *args, **kwargs):

         obj = type.__call__(self, *args)
         for name, value in kwargs.items():
             setattr(obj, name, value)
         return obj

class Attribute(object):

    __metaclass__ = MyMeta

    def load(self, data, base_object):
        ''' the loader is called to store the attribute from a datastructure when key names match.  The default is very basic '''
        self._validate(base_object, data)
        setattr(base_object, self.name,  data)

    def _validate(self, data, base_object):
        ''' validate is called after loading an object data structure to massage any input or raise errors on any incompatibilities '''
        if self.validator:
           self.validator(base_object)

    def post_validate(self, base_object):
        ''' post validate is called after templating the context of a Task (usually in Runner) to validate the types of arguments '''
        if self.post_validator:
           self.post_validator(base_object)

class FieldAttribute(Attribute):
    
    __metaclass__ = MyMeta
    pass

