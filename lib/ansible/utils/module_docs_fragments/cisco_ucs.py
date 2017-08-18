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
#


class ModuleDocFragment(object):

    # Cisco UCS doc fragment
    DOCUMENTATION = '''

options:
    ucs_ip:
        description:
            - IP address or hostname of the Cisco UCS server.
        type: str
    ucs_username:
        description:
            - Username as configured on Cisco UCS server.
        type: str
        default: admin
    ucs_password:
        description:
            - Password as configured on Cisco UCS server.
        type: str
    port:
        description:
            - Port number to be used during connection.(By default uses 443 for https and 80 for http connection)
        type: int
        default: null
    secure:
        description:
            - True for secure connection, otherwise False.
        type: bool
        default: null
    proxy:
        description:
            - Proxy to be used for connection.
        type: str
        default: null
    ucs_server:
        description:
            - UcsHandle object to interact with Cisco UCS server.
        type: UcsHandle
        default: null
'''
