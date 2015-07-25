#!/usr/bin/python
#
# Create Webfaction domains and subdomains using Ansible and the Webfaction API
#
# ------------------------------------------
#
# (c) Quentin Stafford-Fraser 2015
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

DOCUMENTATION = '''
---
module: webfaction_domain
short_description: Add or remove domains and subdomains on Webfaction
description:
    - Add or remove domains or subdomains on a Webfaction host. Further documentation at http://github.com/quentinsf/ansible-webfaction.
author: Quentin Stafford-Fraser (@quentinsf)
version_added: "2.0"
notes:
    - If you are I(deleting) domains by using C(state=absent), then note that if you specify subdomains, just those particular subdomains will be deleted.  If you don't specify subdomains, the domain will be deleted.
    - "You can run playbooks that use this on a local machine, or on a Webfaction host, or elsewhere, since the scripts use the remote webfaction API - the location is not important. However, running them on multiple hosts I(simultaneously) is best avoided. If you don't specify I(localhost) as your host, you may want to add C(serial: 1) to the plays."
    - See `the webfaction API <http://docs.webfaction.com/xmlrpc-api/>`_ for more info.

options:

    name:
        description:
            - The name of the domain
        required: true

    state:
        description:
            - Whether the domain should exist
        required: false
        choices: ['present', 'absent']
        default: "present"

    subdomains:
        description:
            - Any subdomains to create.
        required: false
        default: null

    login_name:
        description:
            - The webfaction account to use
        required: true

    login_password:
        description:
            - The webfaction password to use
        required: true
'''

EXAMPLES = '''
  - name: Create a test domain
    webfaction_domain:
      name: mydomain.com
      state: present
      subdomains:
       - www
       - blog
      login_name: "{{webfaction_user}}"
      login_password: "{{webfaction_passwd}}"

  - name: Delete test domain and any subdomains
    webfaction_domain:
      name: mydomain.com
      state: absent
      login_name: "{{webfaction_user}}"
      login_password: "{{webfaction_passwd}}"

'''

import socket
import xmlrpclib

webfaction = xmlrpclib.ServerProxy('https://api.webfaction.com/')

def main():

    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            state = dict(required=False, choices=['present', 'absent'], default='present'),
            subdomains = dict(required=False, default=[]),
            login_name = dict(required=True),
            login_password = dict(required=True),
        ),
        supports_check_mode=True
    )
    domain_name  = module.params['name']
    domain_state = module.params['state']
    domain_subdomains = module.params['subdomains']

    session_id, account = webfaction.login(
        module.params['login_name'],
        module.params['login_password']
    )

    domain_list = webfaction.list_domains(session_id)
    domain_map = dict([(i['domain'], i) for i in domain_list])
    existing_domain = domain_map.get(domain_name)

    result = {}
    
    # Here's where the real stuff happens

    if domain_state == 'present':

        # Does an app with this name already exist?
        if existing_domain:

            if set(existing_domain['subdomains']) >= set(domain_subdomains):
                # If it exists with the right subdomains, we don't change anything.
                module.exit_json(
                    changed = False,
                )

        positional_args = [session_id, domain_name] + domain_subdomains

        if not module.check_mode:
            # If this isn't a dry run, create the app
            # print positional_args
            result.update(
                webfaction.create_domain(
                    *positional_args
                )
            )

    elif domain_state == 'absent':

        # If the app's already not there, nothing changed.
        if not existing_domain:
            module.exit_json(
                changed = False,
            )

        positional_args = [session_id, domain_name] + domain_subdomains

        if not module.check_mode:
            # If this isn't a dry run, delete the app
            result.update(
                webfaction.delete_domain(*positional_args)
            )

    else:
        module.fail_json(msg="Unknown state specified: {}".format(domain_state))

    module.exit_json(
        changed = True,
        result = result
    )

from ansible.module_utils.basic import *
main()

