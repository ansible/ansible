#!/usr/bin/python
# Copyright 2017 Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gcp_target_proxy
version_added: "2.4"
short_description: Create, Update or Destroy a Target_Proxy.
description:
    - Create, Update or Destroy a Target_Proxy. See
      U(https://cloud.google.com/compute/docs/load-balancing/http/target-proxies) for an overview.
      More details on the Target_Proxy API can be found at
      U(https://cloud.google.com/compute/docs/reference/latest/targetHttpProxies#resource-representations).
requirements:
  - "python >= 2.6"
  - "google-api-python-client >= 1.6.2"
  - "google-auth >= 0.9.0"
  - "google-auth-httplib2 >= 0.0.2"
deprecated:
    removed_in: "2.12"
    why: Updated modules released with increased functionality
    alternative: Use M(gcp_compute_target_http_proxy) instead.
notes:
  - Currently only supports global HTTP proxy.
author:
  - "Tom Melendez (@supertom) <tom@supertom.com>"
options:
  target_proxy_name:
    description:
       - Name of the Target_Proxy.
    required: true
  target_proxy_type:
    description:
       - Type of Target_Proxy. HTTP, HTTPS or SSL. Only HTTP is currently supported.
    required: true
  url_map_name:
    description:
       - Name of the Url Map.  Required if type is HTTP or HTTPS proxy.
    required: false
'''

EXAMPLES = '''
- name: Create Minimum HTTP Target_Proxy
  gcp_target_proxy:
    service_account_email: "{{ service_account_email }}"
    credentials_file: "{{ credentials_file }}"
    project_id: "{{ project_id }}"
    target_proxy_name: my-target_proxy
    target_proxy_type: HTTP
    url_map_name: my-url-map
    state: present
'''

RETURN = '''
state:
    description: state of the Target_Proxy
    returned: Always.
    type: str
    sample: present
updated_target_proxy:
    description: True if the target_proxy has been updated. Will not appear on
                 initial target_proxy creation.
    returned: if the target_proxy has been updated.
    type: bool
    sample: true
target_proxy_name:
    description: Name of the Target_Proxy
    returned: Always
    type: str
    sample: my-target-proxy
target_proxy_type:
    description: Type of Target_Proxy. One of HTTP, HTTPS or SSL.
    returned: Always
    type: str
    sample: HTTP
target_proxy:
    description: GCP Target_Proxy dictionary
    returned: Always. Refer to GCP documentation for detailed field descriptions.
    type: dict
    sample: { "name": "my-target-proxy", "urlMap": "..." }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gcp import get_google_api_client, GCPUtils


USER_AGENT_PRODUCT = 'ansible-target_proxy'
USER_AGENT_VERSION = '0.0.1'


def _build_target_proxy_dict(params, project_id=None):
    """
    Reformat services in Ansible Params.

    :param params: Params from AnsibleModule object
    :type params: ``dict``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: dictionary suitable for submission to GCP UrlMap API.
    :rtype ``dict``
    """
    url = ''
    if project_id:
        url = GCPUtils.build_googleapi_url(project_id)
    gcp_dict = GCPUtils.params_to_gcp_dict(params, 'target_proxy_name')
    if 'urlMap' in gcp_dict:
        gcp_dict['urlMap'] = '%s/global/urlMaps/%s' % (url,
                                                       gcp_dict['urlMap'])
    return gcp_dict


def get_target_http_proxy(client, name, project_id=None):
    """
    Get a Target HTTP Proxy from GCP.

    :param client: An initialized GCE Compute Discovery resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param name: Name of the Target Proxy.
    :type name:  ``str``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: A dict resp from the respective GCP 'get' request.
    :rtype: ``dict``
    """
    req = client.targetHttpProxies().get(project=project_id,
                                         targetHttpProxy=name)
    return GCPUtils.execute_api_client_req(req, raise_404=False)


def create_target_http_proxy(client, params, project_id):
    """
    Create a new Target_Proxy.

    :param client: An initialized GCE Compute Discovery resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param params: Dictionary of arguments from AnsibleModule.
    :type params:  ``dict``

    :return: Tuple with changed status and response dict
    :rtype: ``tuple`` in the format of (bool, dict)
    """
    gcp_dict = _build_target_proxy_dict(params, project_id)
    try:
        req = client.targetHttpProxies().insert(project=project_id,
                                                body=gcp_dict)
        return_data = GCPUtils.execute_api_client_req(req, client, raw=False)
        if not return_data:
            return_data = get_target_http_proxy(client,
                                                name=params['target_proxy_name'],
                                                project_id=project_id)
        return (True, return_data)
    except Exception:
        raise


def delete_target_http_proxy(client, name, project_id):
    """
    Delete a Target_Proxy.

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
        req = client.targetHttpProxies().delete(
            project=project_id, targetHttpProxy=name)
        return_data = GCPUtils.execute_api_client_req(req, client)
        return (True, return_data)
    except Exception:
        raise


def update_target_http_proxy(client, target_proxy, params, name, project_id):
    """
    Update a HTTP Target_Proxy. Currently only the Url Map can be updated.

    If the target_proxy has not changed, the update will not occur.

    :param client: An initialized GCE Compute Discovery resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param target_proxy: Name of the Target Proxy.
    :type target_proxy:  ``dict``

    :param params: Dictionary of arguments from AnsibleModule.
    :type params:  ``dict``

    :param name: Name of the Target Proxy.
    :type name:  ``str``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: Tuple with changed status and response dict
    :rtype: ``tuple`` in the format of (bool, dict)
    """
    gcp_dict = _build_target_proxy_dict(params, project_id)

    GCPUtils.are_params_equal(target_proxy, gcp_dict)
    if target_proxy['urlMap'] == gcp_dict['urlMap']:
        return (False, 'no update necessary')

    try:
        req = client.targetHttpProxies().setUrlMap(project=project_id,
                                                   targetHttpProxy=name,
                                                   body={"urlMap": gcp_dict['urlMap']})
        return_data = GCPUtils.execute_api_client_req(
            req, client=client, raw=False)
        return (True, return_data)
    except Exception:
        raise


def main():
    module = AnsibleModule(argument_spec=dict(
        target_proxy_name=dict(required=True),
        target_proxy_type=dict(required=True, choices=['HTTP']),
        url_map_name=dict(required=False),
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
    params['target_proxy_name'] = module.params.get('target_proxy_name')
    params['target_proxy_type'] = module.params.get('target_proxy_type')
    params['url_map'] = module.params.get('url_map_name', None)

    changed = False
    json_output = {'state': params['state']}
    target_proxy = get_target_http_proxy(client,
                                         name=params['target_proxy_name'],
                                         project_id=conn_params['project_id'])

    if not target_proxy:
        if params['state'] == 'absent':
            # Doesn't exist in GCE, and state==absent.
            changed = False
            module.fail_json(
                msg="Cannot delete unknown target_proxy: %s" %
                (params['target_proxy_name']))
        else:
            # Create
            changed, json_output['target_proxy'] = create_target_http_proxy(client,
                                                                            params=params,
                                                                            project_id=conn_params['project_id'])
    elif params['state'] == 'absent':
        # Delete
        changed, json_output['target_proxy'] = delete_target_http_proxy(client,
                                                                        name=params['target_proxy_name'],
                                                                        project_id=conn_params['project_id'])
    else:
        changed, json_output['target_proxy'] = update_target_http_proxy(client,
                                                                        target_proxy=target_proxy,
                                                                        params=params,
                                                                        name=params['target_proxy_name'],
                                                                        project_id=conn_params['project_id'])
        json_output['updated_target_proxy'] = changed

    json_output['changed'] = changed
    json_output.update(params)
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
