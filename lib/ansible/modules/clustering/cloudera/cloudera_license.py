#!/usr/bin/python
#
# (c) 2017, Serghei Anicheev <serghei.anicheev@gmail.com>
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


DOCUMENTATION = '''
---
module: cloudera_license
author: "Serghei Anicheev (@sanicheev) <serghei.anicheev@gmail.com>"
version_added: '2.2.0.2'
short_description: Cloudera Manager license.
description:
    - This module can update Cloudera Manager license status.
options:
    host:
        description:
            - Cloudera Manager API host.
        required: true
    port:
        description:
            - Cloudera Manager API port.
        required: false
        default: 7180
    username:
        description:
            - Username to connect to Cloudera Manager API.
        required: false
        default: admin
    password:
        description:
            - Password to connect to Cloudera Manager API.
        required: false
        default: admin
    api_version:
        description:
            - Cloudera API version(Older API versions cannot use calls like 'configure_for_kerberos' for example).
        required: false
        default: 12
    use_tls:
        description:
            - Enable TLS(In this case port 7183 should be used!).
        required: false
        default: false
    trial:
        description:
            - Begin trial period. This option is mutually exclusive with options: license_body or license_owner.
        required: false
        default: false
    license_body:
        description:
            - License body to install. This option is mutually exclusive with option: trial. Required together with option: license_owner.
        required: false
    license_owner:
        description:
            - Owner of the license. This option is mutually exclusive with option: trial. Required together with option: license_body.
        required: false
        default: Trial License
    state:
        description:
            - The desired action to perform with the license.
        required: false
        default: install
        choices: ['install']
'''

EXAMPLES = '''
# Upload new license if it does not exists.
- name: Upload new license
  cloudera_license:
    host: 123.123.123.123
    username: admin
    password: admin
    license_body: {{ license_body }}
    license_owner: My Company
    state: install

# Install trial license
- name: Begin trial
  cloudera_license:
    host: 123.123.123.123
    username: admin
    password: admin
    trial: true
'''

def begin_trial(cloudera_manager):
    cloudera_manager.begin_trial()

def install_license(cloudera_manager, license_body):
    cloudera_manager.update_license(license_body)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(required=True, type='str'),
            port=dict(default=7180, type='int'),
            username=dict(default='admin', type='str'),
            password=dict(default='admin', no_log=True, type='str'),
            api_version=dict(default=12, type='int'),
            use_tls=dict(default=False, type='bool'),
            trial=dict(default=False, type='bool'),
            license_body=dict(default=None, type='str'),
            license_owner=dict(default='Trial License', type='str'),
            state=dict(default='install', choices=['install'])
        ),
        required_together=(
            ['license_body', 'license_owner']
        ),
        mutually_exclusive=(
            ['license_body', 'trial'],
            ['license_owner', 'trial']
        ),
        supports_check_mode=True
    )

    host = module.params['host']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
    api_version = module.params['api_version']
    use_tls = module.params['use_tls']
    trial = module.params['trial']
    license_body = module.params['license_body']
    license_owner = module.params['license_owner']
    state = module.params['state']
    changed=False

    if module.check_mode:
        module.exit_json(changed=True)

    cloudera = Cloudera(module, host, port, username, password, api_version, use_tls)
    connection = cloudera.connect()
    cloudera_manager = cloudera.cloudera_manager(connection)
    license = cloudera.license_state(cloudera_manager)

    if trial and state == 'install':
        if license is not None and license.owner == license_owner:
            module.log('Already in trial state!')
            changed = False
        else:
            begin_trial(cloudera_manager)
            changed = True
    else:
        if license is not None and license.owner == license_owner:
            module.log('License for - %s already in place. Nothing to do.' % license_owner)
            changed = False
        else:
            install_license(cloudera_manager, license_body)
            changed = True

    module.exit_json(changed=changed)

if __name__ == '__main__':
    from ansible.module_utils.basic import *
    from ansible.module_utils.cloudera import *
    main()
