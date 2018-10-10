# Copyright: (c) 2016, Jorge Rodriguez <jorge.rodriguez@tiriel.eu>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Parameters for RabbitMQ modules
    DOCUMENTATION = '''
options:
    login_user:
        description:
            - rabbitMQ user for connection.
        required: false
        default: guest
    login_password:
        description:
            - rabbitMQ password for connection.
        required: false
        default: false
    login_host:
        description:
            - rabbitMQ host for connection.
        required: false
        default: localhost
    login_port:
        description:
            - rabbitMQ management API port.
        required: false
        default: 15672
    login_protocol:
        description:
            - rabbitMQ management API protocol.
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
            - rabbitMQ virtual host.
        required: false
        default: "/"
'''
