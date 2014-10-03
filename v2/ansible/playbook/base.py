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

class Base(object):

    def __init__(self, attribute):
        pass

    def add_attribute(self):
        self.attributes.push(attribute)

    def load(self, data):
        for attribute in self.attributes:
            attribute.load(data)

    def validate(self):
        for attribute in self.attributes:
            attribute.validate(self)


