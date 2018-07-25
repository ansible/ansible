#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) mateusz@sysadmins.pl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

RETURN = '''
---
host_groups:
  description: List of Zabbix groups.
  returned: success
  type: dict
  sample: [ { "flags": "0", "groupid": "33", "internal": "0", "name": "Hostgruup A" } ]
'''

DOCUMENTATION = '''
---
module: zabbix_group_facts
short_description: Gather facts about Zabbix hostgroup
description:
   - This module allows you to search for Zabbix hostgroup entries.
version_added: "2.6"
author:
    - "(@redwhitemiko)"
requirements:
    - "python >= 2.6"
    - zabbix-api
options:
    hostgroup_name:
        description:
            - Name of the hostgroup in Zabbix.
            - hostgroup is the unique identifier used and cannot be updated using this module.
        required: true
extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = '''
- name: Get hostgroup info
  local_action:
    module: zabbix_group_facts
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    hostgroup_name:
      - ExampleHostgroup
    timeout: 10
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from zabbix_api import ZabbixAPI, ZabbixAPISubClass

    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False

class Configuration(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    def import_template(self, filename,rules):
        f = open(filename,'r') 
        import_string = f.read()
        import_result = self._zapi.configuration.import_({'format': 'xml', 'source' : import_string , 'rules' : rules })
        return import_result

def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            import_file=dict(type='str', required=True),
            rules=dict(type='dict', required=True),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing requried zabbix-api module (check docs or install with: pip install zabbix-api)")

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    import_file = module.params['import_file']
    timeout = module.params['timeout']
    rules = module.params['rules']

    zbx = None
    # login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                               validate_certs=validate_certs)
        zbx.login(login_user, login_password)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    # Validate parameters
    if 'application' not in rules:
         rules['applications']={}
    if 'createMissing' not in rules['applications']:
        rules['applications']['createMissing'] = True
    if 'deleteMissing' not in rules['applications']:
        rules['applications']['deleteMissing'] = True
        
    conf = Configuration(module, zbx)
    import_task = conf.import_template(import_file,rules)

    module.exit_json(import_task=import_task)

if __name__ == '__main__':
    main()
