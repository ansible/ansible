# (c) 2016, Jorge Rodriguez <jorge.rodriguez@tiriel.eu>
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
    # Parameters for RabbitMQ modules
    DOCUMENTATION = '''
options:
    login_user:
        description:
            - rabbitMQ user for connection
        required: false
        default: guest
    login_password:
        description:
            - rabbitMQ password for connection
        required: false
        default: false
    login_host:
        description:
            - rabbitMQ host for connection
        required: false
        default: localhost
    login_port:
        description:
            - rabbitMQ management api port
        required: false
        default: 15672
    login_protocol:
        description:
            - rabbitMQ management api protocol
        choices: [ http , https ]
        required: false
        default: http
        version_added: "2.3"
    cacert:
        description:
            - CA certificate to verify SSL connection to management API.
        required: false
        version_added: "2.3"
    cert:
        description:
            - Client certificate to send on SSL connections to management API.
        required: false
        version_added: "2.3"
    key:
        description:
            - Private key matching the client certificate.
        required: false
        version_added: "2.3"
    vhost:
        description:
            - rabbitMQ virtual host
        required: false
        default: "/"
'''
