#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, sky-joker
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: zabbix_user_info
short_description: Gather information about Zabbix user
author:
    - sky-joker (@sky-joker)
version_added: '2.10'
description:
    - This module allows you to search for Zabbix user entries.
requirements:
    - "python >= 2.6"
    - "zabbix-api >= 0.5.4"
options:
    alias:
        description:
            - Name of the user alias in Zabbix.
        required: true
        type: str
extends_documentation_fragment:
  - zabbix
'''

EXAMPLES = '''
- name: Get zabbix user info
  zabbix_user_info:
    server_url: "http://zabbix.example.com/zabbix/"
    login_user: admin
    login_password: secret
    alias: example
'''

RETURN = '''
zabbix_user:
  description: example
  returned: always
  type: dict
  sample: {
  "alias": "example",
  "attempt_clock": "0",
  "attempt_failed": "0",
  "attempt_ip": "",
  "autologin": "0",
  "autologout": "0",
  "debug_mode": "0",
  "gui_access": "0",
  "lang": "en_GB",
  "medias": [
      {
        "active": "0",
        "mediaid": "668",
        "mediatypeid": "1",
        "period": "1-7,00:00-24:00",
        "sendto": "example@example.com",
        "severity": "63",
        "userid": "660"
      }
    ],
    "name": "user",
    "refresh": "30s",
    "rows_per_page": "50",
    "surname": "example",
    "theme": "default",
    "type": "1",
    "url": "",
    "userid": "660",
    "users_status": "0",
    "usrgrps": [
      {
        "debug_mode": "0",
        "gui_access": "0",
        "name": "Guests",
        "users_status": "0",
        "usrgrpid": "8"
      }
    ]
  }
'''

import atexit
import traceback

try:
    from zabbix_api import ZabbixAPI

    HAS_ZABBIX_API = True
except ImportError:
    ZBX_IMP_ERR = traceback.format_exc()
    HAS_ZABBIX_API = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


class User(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    def get_user_by_user_alias(self, alias):
        zabbix_user = ""
        try:
            zabbix_user = self._zapi.user.get({'output': 'extend', 'filter': {'alias': alias},
                                               'getAccess': True, 'selectMedias': 'extend',
                                               'selectUsrgrps': 'extend'})
        except Exception as e:
            self._zapi.logout()
            self._module.fail_json(msg="Failed to get user information: %s" % e)

        if not zabbix_user:
            zabbix_user = {}
        else:
            zabbix_user = zabbix_user[0]

        return zabbix_user


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            alias=dict(type='str', required=True),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg=missing_required_lib('zabbix-api', url='https://pypi.org/project/zabbix-api/'),
                         exception=ZBX_IMP_ERR)

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    alias = module.params['alias']
    timeout = module.params['timeout']

    zbx = None

    # login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                        validate_certs=validate_certs)
        zbx.login(login_user, login_password)
        atexit.register(zbx.logout)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    user = User(module, zbx)
    zabbix_user = user.get_user_by_user_alias(alias)
    zbx.logout()
    module.exit_json(changed=False, zabbix_user=zabbix_user)


if __name__ == "__main__":
    main()
