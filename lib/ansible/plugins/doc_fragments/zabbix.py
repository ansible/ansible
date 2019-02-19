# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard documentation fragment
    DOCUMENTATION = r'''
options:
    server_url:
        description:
            - URL of Zabbix server, with protocol (http or https).
              C(url) is an alias for C(server_url).
        required: true
        type: str
        aliases: [ url ]
    login_user:
        description:
            - Zabbix user name.
        type: str
        required: true
    login_password:
        description:
            - Zabbix user password.
        type: str
        required: true
    http_login_user:
        description:
            - Basic Auth login
        type: str
        required: true
        version_added: "2.1"
    http_login_password:
        description:
            - Basic Auth password
        type: str
        version_added: "2.1"
    timeout:
        description:
            - The timeout of API request (seconds).
        type: int
        default: 10
    validate_certs:
      description:
       - If set to False, SSL certificates will not be validated. This should only be used on personally controlled sites using self-signed certificates.
      type: bool
      default: yes
      version_added: "2.5"
'''
