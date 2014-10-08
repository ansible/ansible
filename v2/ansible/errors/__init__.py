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

class AnsibleError(Exception):
    def __init__(self, message, object=None):
         self.message = message
         self.object = object

    # TODO: nice __repr__ message that includes the line number if the object
    # it was constructed with had the line number

    # TODO: tests for the line number functionality

class AnsibleParserError(AnsibleError):
    ''' something was detected early that is wrong about a playbook or data file '''
    pass

class AnsibleInternalError(AnsibleError):
    ''' internal safeguards tripped, something happened in the code that should never happen '''
    pass

class AnsibleRuntimeError(AnsibleError):
    ''' ansible had a problem while running a playbook '''
    pass

class AnsibleModuleError(AnsibleRuntimeError):
    ''' a module failed somehow '''
    pass

class AnsibleConnectionFailure(AnsibleRuntimeError):
    ''' the transport / connection_plugin had a fatal error '''
    pass
