# (c) 2016, Samuel Boucher <boucher.samuel.c@gmail.com>
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



from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
'''
Lookup plugin to grab secrets from the OS keyring.
========================================================================================

Warning the secret will be output to the screen

Example:
---
- hosts: localhost
  tasks:
    - name : test
      debug:
        msg: "Password: {{item}}"
      with_keyring:
        - 'servicename username'

ansible localhost -m debug -a "msg=\"{{item}}\" with_keyring= 'servicename username'"

'''
HAS_KEYRING = True

from ansible.errors import AnsibleError

try:
    import keyring
except ImportError:
    HAS_KEYRING = False


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

from ansible.plugins.lookup import LookupBase

class LookupModule(LookupBase):

    def run(self, terms, **kwargs):
        if not HAS_KEYRING:
            raise AnsibleError(u"Can't LOOKUP(keyring): missing required python library 'keyring'")

        display.vvvv(u"keyring: %s" % keyring.get_keyring() )
        ret = []
        for term in terms:
            (servicename, username) = (term.split()[0], term.split()[1])
            display.vvvv(u"username: %s, servicename: %s " %(username,servicename))
            password = keyring.get_password(servicename,username)
            if password is None:
                raise AnsibleError(u"servicename: %s for user %s not found" % (servicename, username))
            ret.append(password.rstrip())
        return ret

