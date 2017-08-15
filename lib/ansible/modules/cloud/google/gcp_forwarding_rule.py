#!/usr/bin/python
# Copyright 2017 Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gcp_forwarding_rule
version_added: "2.4"
short_description: Create, Update or Destroy a Forwarding_Rule.
description:
    - Create, Update or Destroy a Forwarding_Rule. See
      U(https://cloud.google.com/compute/docs/load-balancing/http/target-proxies) for an overview.
      More details on the Global Forwarding_Rule API can be found at
      U(https://cloud.google.com/compute/docs/reference/latest/globalForwardingRules)
      More details on the Forwarding Rules API can be found at
      U(https://cloud.google.com/compute/docs/reference/latest/forwardingRules)
requirements:
  - "python >= 2.6"
  - "google-api-python-client >= 1.6.2"
  - "google-auth >= 0.9.0"
  - "google-auth-httplib2 >= 0.0.2"
notes:
  - Currently only supports global forwarding rules.
    As such, Load Balancing Scheme is always EXTERNAL.
author:
  - "Tom Melendez (@supertom) <tom@supertom.com>"
options:
  address:
    description:
       - IPv4 or named IP address. Must be of the same scope (regional, global).
         Reserved addresses can (and probably should) be used for global
         forwarding rules. You may reserve IPs from the console or
         via the gce_eip module.
    required: false
  forwarding_rule_name:
    description:
       - Name of the Forwarding_Rule.
    required: true
  port_range:
    description:
       - For global forwarding rules, must be set to 80 or 8080 for TargetHttpProxy, and
         443 for TargetHttpsProxy or TargetSslProxy.
    required: false
  protocol:
    description:
       - For global forwarding rules, TCP, UDP, ESP, AH, SCTP or ICMP. Default is TCP.
    required: false
  region:
    description:
       - The region for this forwarding rule. Currently, only 'global' is supported.
    required: false
  state:
    description:
       - The state of the Forwarding Rule. 'present' or 'absent'
    required: true
    choices: ["present", "absent"]
  target:
    description:
       - Target resource for forwarding rule. For global proxy, this is a Global
         TargetProxy resource. Required for external load balancing (including Global load balancing)
    required: false
'''

EXAMPLES = '''
- name: Create Minimum GLOBAL Forwarding_Rule
  gcp_forwarding_rule:
    service_account_email: "{{ service_account_email }}"
    credentials_file: "{{ credentials_file }}"
    project_id: "{{ project_id }}"
    forwarding_rule_name: my-forwarding_rule
    protocol: TCP
    port_range: 80
    region: global
    target: my-target-proxy
    state: present

- name: Create Forwarding_Rule w/reserved static address
  gcp_forwarding_rule:
    service_account_email: "{{ service_account_email }}"
    credentials_file: "{{ credentials_file }}"
    project_id: "{{ project_id }}"
    forwarding_rule_name: my-forwarding_rule
    protocol: TCP
    port_range: 80
    address: my-reserved-static-address-name
    region: global
    target: my-target-proxy
    state: present
'''

RETURN = '''
forwarding_rule_name:
    description: Name of the Forwarding_Rule
    returned: Always
    type: str
    sample: my-target-proxy
forwarding_rule:
    description: GCP Forwarding_Rule dictionary
    returned: Always. Refer to GCP documentation for detailed field descriptions.
    type: dict
    sample: { "name": "my-forwarding_rule", "target": "..." }
region:
    description: Region for Forwarding Rule.
    returned: Always
    type: bool
    sample: true
state:
    description: state of the Forwarding_Rule
    returned: Always.
    type: str
    sample: present
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gcp import get_google_api_client, GCPUtils


USER_AGENT_PRODUCT = 'ansible-forwarding_rule'
USER_AGENT_VERSION = '0.0.1'


def _build_global_forwarding_rule_dict(params, project_id=None):
    """
    Reformat services in Ansible Params.

    :param params: Params from AnsibleModule object
    :type params: ``dict``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: dictionary suitable for submission to GCP API.
    :rtype ``dict``
    """
    url = ''
    if project_id:
        url = GCPUtils.build_googleapi_url(project_id)
    gcp_dict = GCPUtils.params_to_gcp_dict(params, 'forwarding_rule_name')
    if 'target' in gcp_dict:
        gcp_dict['target'] = '%s/global/targetHttpProxies/%s' % (url,
                                                                 gcp_dict['target'])
    if 'address' in gcp_dict:
        gcp_dict['IPAddress'] = '%s/global/addresses/%s' % (url,
                                                            gcp_dict['address'])
        del gcp_dict['address']
    if 'protocol' in gcp_dict:
        gcp_dict['IPProtocol'] = gcp_dict['protocol']
        del gcp_dict['protocol']
    return gcp_dict


def get_global_forwarding_rule(client, name, project_id=None):
    """
    Get a Global Forwarding Rule from GCP.

    :param client: An initialized GCE Compute Disovery resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param name: Name of the Global Forwarding Rule.
    :type name:  ``str``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: A dict resp from the respective GCP 'get' request.
    :rtype: ``dict``
    """
    try:
        req = client.globalForwardingRules().get(
            project=project_id, forwardingRule=name)
        return GCPUtils.execute_api_client_req(req, raise_404=False)
    except:
        raise


def create_global_forwarding_rule(client, params, project_id):
    """
    Create a new Global Forwarding Rule.

    :param client: An initialized GCE Compute Disovery resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param params: Dictionary of arguments from AnsibleModule.
    :type params:  ``dict``

    :return: Tuple with changed status and response dict
    :rtype: ``tuple`` in the format of (bool, dict)
    """
    gcp_dict = _build_global_forwarding_rule_dict(params, project_id)
    try:
        req = client.globalForwardingRules().insert(project=project_id, body=gcp_dict)
        return_data = GCPUtils.execute_api_client_req(req, client, raw=False)
        if not return_data:
            return_data = get_global_forwarding_rule(client,
                                                     name=params['forwarding_rule_name'],
                                                     project_id=project_id)
        return (True, return_data)
    except:
        raise


def delete_global_forwarding_rule(client, name, project_id):
    """
    Delete a Global Forwarding Rule.

    :param client: An initialized GCE Compute Discovery resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param name: Name of the Target Proxy.
    :type name:  ``str``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: Tuple with changed status and response dict
    :rtype: ``tuple`` in the format of (bool, dict)
    """
    try:
        req = client.globalForwardingRules().delete(
            project=project_id, forwardingRule=name)
        return_data = GCPUtils.execute_api_client_req(req, client)
        return (True, return_data)
    except:
        raise


def update_global_forwarding_rule(client, forwarding_rule, params, name, project_id):
    """
    Update a Global Forwarding_Rule. Currently, only a target can be updated.

    If the forwarding_rule has not changed, the update will not occur.

    :param client: An initialized GCE Compute Disovery resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param forwarding_rule: Name of the Target Proxy.
    :type forwarding_rule:  ``dict``

    :param params: Dictionary of arguments from AnsibleModule.
    :type params:  ``dict``

    :param name: Name of the Global Forwarding Rule.
    :type name:  ``str``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: Tuple with changed status and response dict
    :rtype: ``tuple`` in the format of (bool, dict)
    """
    gcp_dict = _build_global_forwarding_rule_dict(params, project_id)

    GCPUtils.are_params_equal(forwarding_rule, gcp_dict)
    if forwarding_rule['target'] == gcp_dict['target']:
        return (False, 'no update necessary')

    try:
        req = client.globalForwardingRules().setTarget(project=project_id,
                                                       forwardingRule=name,
                                                       body={'target': gcp_dict['target']})
        return_data = GCPUtils.execute_api_client_req(
            req, client=client, raw=False)
        return (True, return_data)
    except:
        raise


def main():
    module = AnsibleModule(argument_spec=dict(
        forwarding_rule_name=dict(required=True),
        region=dict(required=True),
        target=dict(required=False),
        address=dict(type='str', required=False),
        protocol=dict(required=False, default='TCP', choices=['TCP']),
        port_range=dict(required=False),
        load_balancing_scheme=dict(
            required=False, default='EXTERNAL', choices=['EXTERNAL']),
        state=dict(required=True, choices=['absent', 'present']),
        service_account_email=dict(),
        service_account_permissions=dict(type='list'),
        pem_file=dict(),
        credentials_file=dict(),
        project_id=dict(), ), )

    client, conn_params = get_google_api_client(module, 'compute', user_agent_product=USER_AGENT_PRODUCT,
                                                user_agent_version=USER_AGENT_VERSION)

    params = {}
    params['state'] = module.params.get('state')
    params['forwarding_rule_name'] = module.params.get('forwarding_rule_name')
    params['region'] = module.params.get('region')
    params['target'] = module.params.get('target', None)
    params['protocol'] = module.params.get('protocol', None)
    params['port_range'] = module.params.get('port_range')
    if module.params.get('address', None):
        params['address'] = module.params.get('address', None)

    if params['region'] != 'global':
        # This module currently doesn't support regional rules.
        module.fail_json(
            msg=("%s - Only global forwarding rules currently supported. "
                 "Be sure to specify 'global' for the region option.") %
            (params['forwarding_rule_name']))

    changed = False
    json_output = {'state': params['state']}
    forwarding_rule = None
    if params['region'] == 'global':
        forwarding_rule = get_global_forwarding_rule(client,
                                                     name=params['forwarding_rule_name'],
                                                     project_id=conn_params['project_id'])
    if not forwarding_rule:
        if params['state'] == 'absent':
            # Doesn't exist in GCE, and state==absent.
            changed = False
            module.fail_json(
                msg="Cannot delete unknown forwarding_rule: %s" %
                (params['forwarding_rule_name']))
        else:
            # Create
            changed, json_output['forwarding_rule'] = create_global_forwarding_rule(client,
                                                                                    params=params,
                                                                                    project_id=conn_params['project_id'])
    elif params['state'] == 'absent':
        # Delete
        changed, json_output['forwarding_rule'] = delete_global_forwarding_rule(client,
                                                                                name=params['forwarding_rule_name'],
                                                                                project_id=conn_params['project_id'])
    else:
        changed, json_output['forwarding_rule'] = update_global_forwarding_rule(client,
                                                                                forwarding_rule=forwarding_rule,
                                                                                params=params,
                                                                                name=params['forwarding_rule_name'],
                                                                                project_id=conn_params['project_id'])

    json_output['changed'] = changed
    json_output.update(params)
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
