#!/usr/bin/python
#
# (c) 2017 Apstra Inc, <community@apstra.com>
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
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: aos_login
author: jeremy@apstra.com (@jeremyschulman)
version_added: "2.3"
short_description: Login to AOS server for session token
deprecated:
    removed_in: "2.9"
    why: This module does not support AOS 2.1 or later
    alternative: See new modules at U(https://www.ansible.com/ansible-apstra).
description:
  - Obtain the AOS server session token by providing the required
    username and password credentials.  Upon successful authentication,
    this module will return the session-token that is required by all
    subsequent AOS module usage. On success the module will automatically populate
    ansible facts with the variable I(aos_session)
    This module is not idempotent and do not support check mode.
requirements:
  - "aos-pyez >= 0.6.1"
options:
  server:
    description:
      - Address of the AOS Server on which you want to open a connection.
    required: true
  port:
    description:
      - Port number to use when connecting to the AOS server.
    default: 443
  user:
    description:
      - Login username to use when connecting to the AOS server.
    default: admin
  passwd:
    description:
      - Password to use when connecting to the AOS server.
    default: admin
'''

EXAMPLES = '''

- name: Create a session with the AOS-server
  aos_login:
    server: "{{ inventory_hostname }}"
    user: admin
    passwd: admin

- name: Use the newly created session (register is not mandatory)
  aos_ip_pool:
    session: "{{ aos_session }}"
    name: my_ip_pool
    state: present
'''

RETURNS = '''
aos_session:
  description: Authenticated session information
  returned: always
  type: dict
  sample: { 'url': <str>, 'headers': {...} }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aos.aos import check_aos_version

try:
    from apstra.aosom.session import Session
    import apstra.aosom.exc as aosExc

    HAS_AOS_PYEZ = True
except ImportError:
    HAS_AOS_PYEZ = False


def aos_login(module):

    mod_args = module.params

    aos = Session(server=mod_args['server'], port=mod_args['port'],
                  user=mod_args['user'], passwd=mod_args['passwd'])

    try:
        aos.login()
    except aosExc.LoginServerUnreachableError:
        module.fail_json(
            msg="AOS-server [%s] API not available/reachable, check server" % aos.server)

    except aosExc.LoginAuthError:
        module.fail_json(msg="AOS-server login credentials failed")

    module.exit_json(changed=False,
                     ansible_facts=dict(aos_session=aos.session),
                     aos_session=dict(aos_session=aos.session))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server=dict(required=True),
            port=dict(default='443', type="int"),
            user=dict(default='admin'),
            passwd=dict(default='admin', no_log=True)))

    if not HAS_AOS_PYEZ:
        module.fail_json(msg='aos-pyez is not installed.  Please see details '
                             'here: https://github.com/Apstra/aos-pyez')

    # Check if aos-pyez is present and match the minimum version
    check_aos_version(module, '0.6.1')

    aos_login(module)

if __name__ == '__main__':
    main()
