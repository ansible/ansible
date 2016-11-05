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


import keyring
try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

from ansible.plugins.lookup import LookupBase

class LookupModule(LookupBase):

    def run(self, terms, **kwargs):
        display.vvvv(u"keyring: %s" % keyring.get_keyring() )
        ret = []
        for term in terms:
            (servicename, username) = (term.split()[0], term.split()[1])
            display.vvvv(u"username: %s, servicename: %s " %(username,servicename))
            ret.append(keyring.get_password(servicename,username).rstrip())
        return ret

