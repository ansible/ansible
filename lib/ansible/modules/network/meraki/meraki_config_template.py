#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Kevin Breit (@kbreit) <kevin.breit@kevinbreit.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: meraki_config_template
short_description: Manage configuration templates in the Meraki cloud
version_added: "2.7"
description:
- Allows for querying, deleting, binding, and unbinding of configuration templates.
notes:
- Module is not idempotent as the Meraki API is limited in what information it provides about configuration templates.
- Meraki's API does not support creating new configuration templates.
- To use the configuration template, simply pass its ID via C(net_id) parameters in Meraki modules.
options:
    state:
        description:
        - Specifies whether configuration template information should be queried, modified, or deleted.
        choices: ['absent', 'query', 'present']
        default: query
    org_name:
        description:
        - Name of organization containing the configuration template.
    org_id:
        description:
        - ID of organization associated to a configuration template.
    config_template:
        description:
        - Name of the configuration template within an organization to manipulate.
        aliases: ['name']
    net_name:
        description:
        - Name of the network to bind or unbind configuration template to.
    net_id:
        description:
        - ID of the network to bind or unbind configuration template to.
    auto_bind:
        description:
        - Optional boolean indicating whether the network's switches should automatically bind to profiles of the same model.
        - This option only affects switch networks and switch templates.
        - Auto-bind is not valid unless the switch template has at least one profile and has at most one profile per switch model.
        type: bool

author:
- Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Query configuration templates
  meraki_config_template:
    auth_key: abc12345
    org_name: YourOrg
    state: query
  delegate_to: localhost

- name: Bind a template from a network
  meraki_config_template:
    auth_key: abc123
    state: present
    org_name: YourOrg
    net_name: YourNet
    config_template: DevConfigTemplate
  delegate_to: localhost

- name: Unbind a template from a network
  meraki_config_template:
    auth_key: abc123
    state: absent
    org_name: YourOrg
    net_name: YourNet
    config_template: DevConfigTemplate
  delegate_to: localhost

- name: Delete a configuration template
  meraki_config_template:
    auth_key: abc123
    state: absent
    org_name: YourOrg
    config_template: DevConfigTemplate
  delegate_to: localhost
'''

RETURN = r'''
data:
    description: Information about queried object.
    returned: success
    type: complex
    contains:
        id:
          description: Unique identification number of organization
          returned: success
          type: int
          sample: L_2930418
        name:
          description: Name of configuration template
          returned: success
          type: string
          sample: YourTemplate
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def get_config_templates(meraki, org_id):
    path = meraki.construct_path('get_all', org_id=org_id)
    response = meraki.request(path, 'GET')
    if meraki.status != 200:
        meraki.fail_json(msg='Unable to get configuration templates')
    return response


def get_template_id(meraki, name, data):
    for template in data:
        if name == template['name']:
            return template['id']
    meraki.fail_json(msg='No configuration template named {0} found'.format(name))


def is_network_bound(meraki, nets, net_id, template_id):
    for net in nets:
        if net['id'] == net_id:
            try:
                if net['configTemplateId'] == template_id:
                    return True
            except KeyError:
                pass
    return False


def delete_template(meraki, org_id, name, data):
    template_id = get_template_id(meraki, name, data)
    path = meraki.construct_path('delete', org_id=org_id)
    path = path + '/' + template_id
    response = meraki.request(path, 'DELETE')
    if meraki.status != 200:
        meraki.fail_json(msg='Unable to remove configuration template')
    return response


def bind(meraki, org_name, net_id, nets, name, data):
    template_id = get_template_id(meraki, name, data)
    if is_network_bound(meraki, nets, net_id, template_id) is False:
        path = meraki.construct_path('bind', function='config_template', net_id=net_id)
        payload = dict()
        payload['configTemplateId'] = template_id
        if meraki.params['auto_bind']:
            payload['autoBind'] = meraki.params['auto_bind']
        meraki.result['changed'] = True
        r = meraki.request(path, method='POST', payload=json.dumps(payload))
        if meraki.status != 200:
            meraki.fail_json(msg='Unable to bind configuration template to network')
        return r


def unbind(meraki, org_name, net_id, nets, name, data):
    template_id = get_template_id(meraki, name, data)
    if is_network_bound(meraki, nets, net_id, template_id) is True:
        path = meraki.construct_path('unbind', function='config_template', net_id=net_id)
        meraki.result['changed'] = True
        r = meraki.request(path, method='POST')
        if meraki.status != 200:
            meraki.fail_json(msg='Unable to unbind configuration template from network')
        return r


def main():

    # define the available arguments/parameters that a user can pass to
    # the module
    argument_spec = meraki_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'query', 'present'], default='query'),
                         org_name=dict(type='str', aliases=['organization']),
                         org_id=dict(type='int'),
                         config_template=dict(type='str', aliases=['name']),
                         net_name=dict(type='str'),
                         net_id=dict(type='str'),
                         # config_template_id=dict(type='str', aliases=['id']),
                         auto_bind=dict(type='bool'),
                         )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )
    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           )
    meraki = MerakiModule(module, function='config_template')
    meraki.params['follow_redirects'] = 'all'

    query_urls = {'config_template': '/organizations/{org_id}/configTemplates',
                  }

    delete_urls = {'config_template': '/organizations/{org_id}/configTemplates',
                   }

    bind_urls = {'config_template': '/networks/{net_id}/bind',
                 }

    unbind_urls = {'config_template': '/networks/{net_id}/unbind',
                   }

    meraki.url_catalog['get_all']['config_template'] = '/organizations/{org_id}/configTemplates'
    meraki.url_catalog['delete'] = delete_urls
    meraki.url_catalog['bind'] = bind_urls
    meraki.url_catalog['unbind'] = unbind_urls

    payload = None

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    # FIXME: Work with Meraki so they can implement a check mode
    if module.check_mode:
        meraki.exit_json(**meraki.result)

    # execute checks for argument completeness

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    org_id = meraki.params['org_id']
    if meraki.params['org_name']:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    net_id = meraki.params['net_id']
    nets = meraki.get_nets(org_id=org_id)
    if meraki.params['net_name']:
        net_id = meraki.get_net_id(net_name=meraki.params['net_name'], data=nets)

    if meraki.params['state'] == 'query':
        meraki.result['data'] = get_config_templates(meraki, org_id)
    elif meraki.params['state'] == 'present':
        if meraki.params['net_name']:
            template_bind = bind(meraki,
                                 meraki.params['org_name'],
                                 net_id,
                                 nets,
                                 meraki.params['config_template'],
                                 get_config_templates(meraki, org_id))
    elif meraki.params['state'] == 'absent':
        if not meraki.params['net_name']:
            meraki.result['data'] = delete_template(meraki,
                                                    org_id,
                                                    meraki.params['config_template'],
                                                    get_config_templates(meraki, org_id))
        else:
            config_unbind = unbind(meraki,
                                   meraki.params['org_name'],
                                   net_id,
                                   nets,
                                   meraki.params['config_template'],
                                   get_config_templates(meraki, org_id))

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
