# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Jorge Rodriguez <jorge.rodriguez@tiriel.eu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Parameters for RabbitMQ modules
    DOCUMENTATION = r'''
options:
    login_user:
        description:
            - RabbitMQ user for connection.
        type: str
        default: guest
    login_password:
        description:
            - RabbitMQ password for connection.
        type: str
    login_host:
        description:
            - RabbitMQ host for connection.
        type: str
        default: localhost
    login_port:
        description:
            - RabbitMQ management API port.
        type: str
        default: '15672'
    login_protocol:
        description:
            - RabbitMQ management API protocol.
        type: str
        choices: [ http , https ]
        default: http
        version_added: "2.3"
    ca_cert:
        description:
            - CA certificate to verify SSL connection to management API.
        type: path
        version_added: "2.3"
        aliases: [ cacert ]
    client_cert:
        description:
            - Client certificate to send on SSL connections to management API.
        type: path
        version_added: "2.3"
        aliases: [ cert ]
    client_key:
        description:
            - Private key matching the client certificate.
        type: path
        version_added: "2.3"
        aliases: [ key ]
    vhost:
        description:
            - RabbitMQ virtual host.
        type: str
        default: "/"
'''
