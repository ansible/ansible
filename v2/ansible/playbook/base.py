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


# general concept
#  FooObject.load(datastructure) -> Foo
#  FooObject._load_field # optional
#  FooObject._validate_field # optional
#  FooObject._post_validate_field # optional
# FooObject.evaluate(host_context) -> FooObject ?  (calls post_validators, templates all members)
# question - are there some things that need to be evaluated *before* host context, i.e. globally?
# most things should be templated but want to provide as much early checking as possible
# TODO: also check for fields in datastructure that are not valid
# TODO: PluginAttribute(type) allows all the valid plugins as valid types of names
#   lookupPlugins start with "with_", ModulePluginAttribute allows any key

class Base(object):

    def __init__(self):
        self._data = dict()
        self._attributes = dict()
        
        for name in self.__class__.__dict__:
            aname = name[1:]
            if isinstance(aname, Attribute) and not isinstance(aname, FieldAttribute):
                self._attributes[aname] = None

    def load_data(self, ds):
        ''' walk the input datastructure and assign any values '''

        assert ds is not None

        for (name, attribute) in self.__class__.__dict__.iteritems():
            aname = name[1:]

            # process Fields
            if isinstance(attribute, FieldAttribute):
                method = getattr(self, '_load_%s' % aname, None)
                if method:
                    self._attributes[aname] = method(self, attribute)
                else:
                    if aname in ds:
                        self._attributes[aname] = ds[aname]

             # TODO: implement PluginAtrribute which allows "with_" and "action" aliases.

        return self


    def validate(self):
        # TODO: finish
        for name in self.__dict__:
            aname = name[1:]
            attribute = self.__dict__[aname]
            if instanceof(attribute, FieldAttribute):
                method = getattr(self, '_validate_%s' % (prefix, aname), None)
                if method:
                    method(self, attribute)

    def post_validate(self, runner_context):
        # TODO: finish
        raise exception.NotImplementedError

    def __getattr__(self, needle):
        if needle in self._attributes:
            return self._attributes[needle]
        if needle in self.__dict__:
            return self.__dict__[needle]
        raise AttributeError

    #def __setattr__(self, needle, value):
    #    if needle in self._attributes:
    #        self._attributes[needle] = value
    #    if needle in self.__dict__:
    #        super(Base, self).__setattr__(needle, value)
    #        # self.__dict__[needle] = value
    #    raise AttributeError


