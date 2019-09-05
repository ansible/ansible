#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: mso_schema_template_deploy
short_description: Deploy schema templates to sites
description:
- Deploy schema templates to sites.
author:
- Dag Wieers (@dagwieers)
version_added: '2.8'
options:
  schema:
    description:
    - The name of the schema.
    type: str
    required: yes
  template:
    description:
    - The name of the template.
    type: str
    aliases: [ name ]
  site:
    description:
    - The name of the site B(to undeploy).
    type: str
  state:
    description:
    - Use C(deploy) to deploy schema template.
    - Use C(status) to get deployment status.
    - Use C(undeploy) to deploy schema template from a site.
    type: str
    choices: [ deploy, status, undeploy ]
    default: deploy
seealso:
- module: mso_schema_site
- module: mso_schema_template
extends_documentation_fragment: mso
'''

EXAMPLES = r'''
- name: Deploy a schema template
  mso_schema_template_deploy:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    state: deploy
  delegate_to: localhost

- name: Undeploy a schema template
  mso_schema_template_deploy:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    site: Site 1
    state: undeploy
  delegate_to: localhost

- name: Get deployment status
  mso_schema:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    state: status
  delegate_to: localhost
  register: status_result
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.mso import MSOModule, mso_argument_spec


def main():
    argument_spec = mso_argument_spec()
    argument_spec.update(
        schema=dict(type='str', required=True),
        template=dict(type='str', required=True, aliases=['name']),
        site=dict(type='str'),
        state=dict(type='str', default='deploy', choices=['deploy', 'status', 'undeploy']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'undeploy', ['site']],
        ],
    )

    schema = module.params['schema']
    template = module.params['template']
    site = module.params['site']
    state = module.params['state']

    mso = MSOModule(module)

    # Get schema
    schema_id = mso.lookup_schema(schema)

    payload = dict(
        schemaId=schema_id,
        templateName=template,
    )

    qs = None
    if state == 'deploy':
        path = 'execute/schema/{0}/template/{1}'.format(schema_id, template)
    elif state == 'status':
        path = 'status/schema/{0}/template/{1}'.format(schema_id, template)
    elif state == 'undeploy':
        path = 'execute/schema/{0}/template/{1}'.format(schema_id, template)
        site_id = mso.lookup_site(site)
        qs = dict(undeploy=site_id)

    if not module.check_mode:
        status = mso.request(path, method='GET', data=payload, qs=qs)

    mso.exit_json(**status)


if __name__ == "__main__":
    main()
