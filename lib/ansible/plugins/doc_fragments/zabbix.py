# Copyright (c) 2017 Ansible, Inc
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


class ModuleDocFragment(object):

    # Standard documentation fragment
    DOCUMENTATION = '''
options:
    server_url:
        description:
            - URL of Zabbix server, with protocol (http or https).
              C(url) is an alias for C(server_url).
        required: true
        aliases: [ "url" ]
    login_user:
        description:
            - Zabbix user name.
        required: true
    login_password:
        description:
            - Zabbix user password.
        required: true
    http_login_user:
        description:
            - Basic Auth login
        version_added: "2.1"
    http_login_password:
        description:
            - Basic Auth password
        version_added: "2.1"
    timeout:
        description:
            - The timeout of API request (seconds).
        default: 10
    validate_certs:
      description:
       - If set to False, SSL certificates will not be validated. This should only be used on personally controlled sites using self-signed certificates.
      type: bool
      default: 'yes'
      version_added: "2.5"
'''
