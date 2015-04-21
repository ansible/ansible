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

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.playbook.attribute import Attribute, FieldAttribute
#from ansible.utils.display import deprecated

class Become:

    # Privlege escalation
    _become              = FieldAttribute(isa='bool', default=False)
    _become_method       = FieldAttribute(isa='string')
    _become_user         = FieldAttribute(isa='string')
    _become_pass         = FieldAttribute(isa='string')

    def __init__(self):
        return super(Become, self).__init__()

    def _detect_privilege_escalation_conflict(self, ds):

        # Fail out if user specifies conflicting privelege escalations
        has_become = 'become' in ds or 'become_user'in ds
        has_sudo   = 'sudo' in ds or 'sudo_user' in ds
        has_su     = 'su' in ds or 'su_user' in ds

        if has_become:
            msg = 'The become params ("become", "become_user") and'
            if has_sudo:
                raise AnsibleParserError('%s sudo params ("sudo", "sudo_user") cannot be used together' % msg)
            elif has_su:
                raise AnsibleParserError('%s su params ("su", "su_user") cannot be used together' % msg)
        elif has_sudo and has_su:
            raise AnsibleParserError('sudo params ("sudo", "sudo_user") and su params ("su", "su_user") cannot be used together')

    def _preprocess_data_become(self, ds):
        """Preprocess the playbook data for become attributes

        This is called from the Base object's preprocess_data() method which
        in turn is called pretty much anytime any sort of playbook object
        (plays, tasks, blocks, etc) are created.
        """

        self._detect_privilege_escalation_conflict(ds)

        # Setting user implies setting become/sudo/su to true
        if 'become_user' in ds and not ds.get('become', False):
            ds['become'] = True

        # Privilege escalation, backwards compatibility for sudo/su
        if 'sudo' in ds or 'sudo_user' in ds:
            ds['become_method'] = 'sudo'
            if 'sudo' in ds:
                ds['become'] = ds['sudo']
                del ds['sudo']
            else:
                ds['become'] = True
            if 'sudo_user' in ds:
                ds['become_user'] = ds['sudo_user']
                del ds['sudo_user']

            #deprecated("Instead of sudo/sudo_user, use become/become_user and set become_method to 'sudo' (default)")

        elif 'su' in ds or 'su_user' in ds:
            ds['become_method'] = 'su'
            if 'su' in ds:
                ds['become'] = ds['su']
                del ds['su']
            else:
                ds['become'] = True
            if 'su_user' in ds:
                ds['become_user'] = ds['su_user']
                del ds['su_user']

            #deprecated("Instead of su/su_user, use become/become_user and set become_method to 'su' (default is sudo)")

        # if we are becoming someone else, but some fields are unset,
        # make sure they're initialized to the default config values
        if ds.get('become', False):
            if ds.get('become_method', None) is None:
                ds['become_method'] = C.DEFAULT_BECOME_METHOD
            if ds.get('become_user', None) is None:
                ds['become_user'] = C.DEFAULT_BECOME_USER

        return ds

    def _get_attr_become(self):
        '''
        Override for the 'become' getattr fetcher, used from Base.
        '''
        if hasattr(self, '_get_parent_attribute'):
            return self._get_parent_attribute('become')
        else:
            return self._attributes['become']

    def _get_attr_become_method(self):
        '''
        Override for the 'become_method' getattr fetcher, used from Base.
        '''
        if hasattr(self, '_get_parent_attribute'):
            return self._get_parent_attribute('become_method')
        else:
            return self._attributes['become_method']

    def _get_attr_become_user(self):
        '''
        Override for the 'become_user' getattr fetcher, used from Base.
        '''
        if hasattr(self, '_get_parent_attribute'):
            return self._get_parent_attribute('become_user')
        else:
            return self._attributes['become_user']

    def _get_attr_become_password(self):
        '''
        Override for the 'become_password' getattr fetcher, used from Base.
        '''
        if hasattr(self, '_get_parent_attribute'):
            return self._get_parent_attribute('become_password')
        else:
            return self._attributes['become_password']


