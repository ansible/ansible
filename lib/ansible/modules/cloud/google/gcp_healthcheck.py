#!/usr/bin/python
# Copyright 2017 Google Inc.
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gcp_healthcheck
version_added: "2.4"
short_description: Create, Update or Destory a Healthcheck.
description:
    - Create, Update or Destory a Healthcheck. Currently only HTTP and
      HTTPS Healthchecs are supported. Healthchecks are used to monitor
      individual instances, managed instance groups and/or backend
      services. Healtchecks are reusable.
    - Visit
      U(https://cloud.google.com/compute/docs/load-balancing/health-checks)
      for an overview of Healthchecks on GCP.
    - See
      U(https://cloud.google.com/compute/docs/reference/latest/httpHealthChecks) for
      API details on HTTP Healthchecks.
    - See
      U(https://cloud.google.com/compute/docs/reference/latest/httpsHealthChecks)
      for more details on the HTTPS Healtcheck API.
requirements:
  - "python >= 2.6"
  - "google-api-python-client >= 1.6.2"
  - "google-auth >= 0.9.0"
  - "google-auth-httplib2 >= 0.0.2"
notes:
  - Only supports HTTP and HTTPS Healthchecks currently.
author:
  - "Tom Melendez (@supertom) <tom@supertom.com>"
options:
  check_interval:
    description:
       - How often (in seconds) to send a health check. The default
         value is 5 seconds.
    required: false
  healthcheck_name:
    description:
       - Name of the Healthcheck.
    required: true
  healthcheck_type:
    description:
       - Type of Healthcheck. HTTP or HTTPS.
    required: true
  host_header:
    description:
       - The value of the host header in the health check request. If left
         empty (default value), the public IP on behalf of which this health
         check is performed will be used.
    required: true
  port:
    description:
       - The TCP port number for health check request.The default value is 443
         for HTTPS and 80 for HTTP.
    required: false
  request_path:
    description:
       - The request path of the HTTPS health check request.
         The default value is "/".
    required: false
  timeout:
    description:
       - How long (in seconds) to wait before claiming failure. The default
         value is 5 seconds. It is invalid for timeout to have a greater
         value than check_interval.
    required: false
  unhealthy_threshold:
    description:
       - A so-far healthy instance will be marked unhealthy after this
         many consecutive failures. The default value is 2.
    required: false
  healthy_threshold:
    description:
       - A so-far unhealthy instance will be marked healthy after this
         many consecutive successes. The default value is 2.
    required: false
'''

EXAMPLES = '''
- name: Create Minimum HealthCheck
  gcp_healthcheck:
    service_account_email: "{{ service_account_email }}"
    credentials_file: "{{ credentials_file }}"
    project_id: "{{ project_id }}"
    healthcheck_name: my-healthcheck
    healthcheck_type: HTTP
    state: present
- name: Create HTTP HealthCheck
  gcp_healthcheck:
    service_account_email: "{{ service_account_email }}"
    credentials_file: "{{ credentials_file }}"
    project_id: "{{ project_id }}"
    healthcheck_name: my-healthcheck
    healthcheck_type: HTTP
    host: my-host
    request_path: /hc
    check_interval: 10
    timeout: 30
    unhealthy_threshhold: 2
    healthy_threshhold: 1
    state: present
- name: Create HTTPS HealthCheck
  gcp_healthcheck:
    service_account_email: "{{ service_account_email }}"
    credentials_file: "{{ credentials_file }}"
    project_id: "{{ project_id }}"
    healthcheck_name: "{{ https_healthcheck }}"
    healthcheck_type: HTTPS
    host_header: my-host
    request_path: /hc
    check_interval: 5
    timeout: 5
    unhealthy_threshold: 2
    healthy_threshold: 1
    state: present
'''

RETURN = '''
state:
    description: state of the Healthcheck
    returned: Always.
    type: str
    sample: present
updated_healthcheck:
    description: True if the healthcheck has been updated. Will not appear on
                 initial healthcheck creation.
    returned: if the healthcheck has been updated.
    type: bool
    sample: true
healthcheck_name:
    description: Name of the Healthcheck
    returned: Always
    type: str
    sample: my-url-map
healthcheck_type:
    description: Type of the Healthcheck
    returned: Always
    type: str
    sample: HTTP
healthcheck:
    description: GCP Healthcheck dictionary
    returned: Always. Refer to GCP documentation for detailed field descriptions.
    type: dict
    sample: { "name": "my-hc", "port": 443, "requestPath": "/foo" ... }
'''


try:
    from ast import literal_eval
    HAS_PYTHON26 = True
except ImportError:
    HAS_PYTHON26 = False

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gcp import check_params, get_google_api_client, GCPUtils

USER_AGENT_PRODUCT = 'ansible-healthcheck'
USER_AGENT_VERSION = '0.0.1'


def _validate_healthcheck_params(params):
    """
    Validate healthcheck params.

    Simple validation has already assumed by AnsibleModule.

    :param params: Ansible dictionary containing configuration.
    :type  params: ``dict``

    :return: True or raises ValueError
    :rtype: ``bool`` or `class:ValueError`
    """
    if params['timeout'] > params['check_interval']:
        raise ValueError("timeout (%s) is greater than check_interval (%s)" % (
            params['timeout'], params['check_interval']))

    return (True, '')


def _build_healthcheck_dict(params):
    """
    Reformat services in Ansible Params for GCP.

    :param params: Params from AnsibleModule object
    :type params: ``dict``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: dictionary suitable for submission to GCP
             HealthCheck (HTTP/HTTPS) API.
    :rtype ``dict``
    """
    gcp_dict = GCPUtils.params_to_gcp_dict(params, 'healthcheck_name')
    if 'timeout' in gcp_dict:
        gcp_dict['timeoutSec'] = gcp_dict['timeout']
        del gcp_dict['timeout']

    if 'check_interval' in gcp_dict:
        gcp_dict['checkIntervalSec'] = gcp_dict['check_interval']
        del gcp_dict['check_interval']

    if 'host_header' in gcp_dict:
        gcp_dict['host'] = gcp_dict['host_header']
        del gcp_dict['host_header']

    if 'healthcheck_type' in gcp_dict:
        del gcp_dict['healthcheck_type']
    return gcp_dict


def _get_req_resource(client, resource_type):
    if resource_type == 'HTTPS':
        return (client.httpsHealthChecks(), 'httpsHealthCheck')
    else:
        return (client.httpHealthChecks(), 'httpHealthCheck')


def get_healthcheck(client, name, project_id=None, resource_type='HTTP'):
    """
    Get a Healthcheck from GCP.

    :param client: An initialized GCE Compute Disovery resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param name: Name of the Url Map.
    :type name:  ``str``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: A dict resp from the respective GCP 'get' request.
    :rtype: ``dict``
    """
    try:
        resource, entity_name = _get_req_resource(client, resource_type)
        args = {'project': project_id, entity_name: name}
        req = resource.get(**args)
        return GCPUtils.execute_api_client_req(req, raise_404=False)
    except:
        raise


def create_healthcheck(client, params, project_id, resource_type='HTTP'):
    """
    Create a new Healthcheck.

    :param client: An initialized GCE Compute Disovery resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param params: Dictionary of arguments from AnsibleModule.
    :type params:  ``dict``

    :return: Tuple with changed status and response dict
    :rtype: ``tuple`` in the format of (bool, dict)
    """
    gcp_dict = _build_healthcheck_dict(params)
    try:
        resource, _ = _get_req_resource(client, resource_type)
        args = {'project': project_id, 'body': gcp_dict}
        req = resource.insert(**args)
        return_data = GCPUtils.execute_api_client_req(req, client, raw=False)
        if not return_data:
            return_data = get_healthcheck(client,
                                          name=params['healthcheck_name'],
                                          project_id=project_id)
        return (True, return_data)
    except:
        raise


def delete_healthcheck(client, name, project_id, resource_type='HTTP'):
    """
    Delete a Healthcheck.

    :param client: An initialized GCE Compute Disover resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param name: Name of the Url Map.
    :type name:  ``str``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: Tuple with changed status and response dict
    :rtype: ``tuple`` in the format of (bool, dict)
    """
    try:
        resource, entity_name = _get_req_resource(client, resource_type)
        args = {'project': project_id, entity_name: name}
        req = resource.delete(**args)
        return_data = GCPUtils.execute_api_client_req(req, client)
        return (True, return_data)
    except:
        raise


def update_healthcheck(client, healthcheck, params, name, project_id,
                       resource_type='HTTP'):
    """
    Update a Healthcheck.

    If the healthcheck has not changed, the update will not occur.

    :param client: An initialized GCE Compute Disovery resource.
    :type client:  :class: `googleapiclient.discovery.Resource`

    :param healthcheck: Name of the Url Map.
    :type healthcheck:  ``dict``

    :param params: Dictionary of arguments from AnsibleModule.
    :type params:  ``dict``

    :param name: Name of the Url Map.
    :type name:  ``str``

    :param project_id: The GCP project ID.
    :type project_id:  ``str``

    :return: Tuple with changed status and response dict
    :rtype: ``tuple`` in the format of (bool, dict)
    """
    gcp_dict = _build_healthcheck_dict(params)

    ans = GCPUtils.are_params_equal(healthcheck, gcp_dict)
    if ans:
        return (False, 'no update necessary')

    try:
        resource, entity_name = _get_req_resource(client, resource_type)
        args = {'project': project_id, entity_name: name, 'body': gcp_dict}
        req = resource.update(**args)
        return_data = GCPUtils.execute_api_client_req(
            req, client=client, raw=False)
        return (True, return_data)
    except:
        raise


def main():
    module = AnsibleModule(argument_spec=dict(
        healthcheck_name=dict(required=True),
        healthcheck_type=dict(required=True,
                              choices=['HTTP', 'HTTPS']),
        request_path=dict(required=False, default='/'),
        check_interval=dict(required=False, type='int', default=5),
        healthy_threshold=dict(required=False, type='int', default=2),
        unhealthy_threshold=dict(required=False, type='int', default=2),
        host_header=dict(required=False, type='str'),
        timeout=dict(required=False, type='int', default=5),
        port=dict(required=False, type='int'),
        state=dict(choices=['absent', 'present'], default='present'),
        service_account_email=dict(),
        service_account_permissions=dict(type='list'),
        pem_file=dict(),
        credentials_file=dict(),
        project_id=dict(), ), )

    if not HAS_PYTHON26:
        module.fail_json(
            msg="GCE module requires python's 'ast' module, python v2.6+")

    client, conn_params = get_google_api_client(module, 'compute', user_agent_product=USER_AGENT_PRODUCT,
                                                user_agent_version=USER_AGENT_VERSION)

    params = {}

    params['healthcheck_name'] = module.params.get('healthcheck_name')
    params['healthcheck_type'] = module.params.get('healthcheck_type')
    params['request_path'] = module.params.get('request_path')
    params['check_interval'] = module.params.get('check_interval')
    params['healthy_threshold'] = module.params.get('healthy_threshold')
    params['unhealthy_threshold'] = module.params.get('unhealthy_threshold')
    params['host_header'] = module.params.get('host_header')
    params['timeout'] = module.params.get('timeout')
    params['port'] = module.params.get('port')
    params['state'] = module.params.get('state')

    try:
        _validate_healthcheck_params(params)
    except Exception as e:
        module.fail_json(msg=e.message, changed=False)

    changed = False
    json_output = {'state': params['state']}
    healthcheck = get_healthcheck(client,
                                  name=params['healthcheck_name'],
                                  project_id=conn_params['project_id'],
                                  resource_type=params['healthcheck_type'])

    if not healthcheck:
        if params['state'] == 'absent':
            # Doesn't exist in GCE, and state==absent.
            changed = False
            module.fail_json(
                msg="Cannot delete unknown healthcheck: %s" %
                (params['healthcheck_name']))
        else:
            # Create
            changed, json_output['healthcheck'] = create_healthcheck(client,
                                                                     params=params,
                                                                     project_id=conn_params['project_id'],
                                                                     resource_type=params['healthcheck_type'])
    elif params['state'] == 'absent':
        # Delete
        changed, json_output['healthcheck'] = delete_healthcheck(client,
                                                                 name=params['healthcheck_name'],
                                                                 project_id=conn_params['project_id'],
                                                                 resource_type=params['healthcheck_type'])
    else:
        changed, json_output['healthcheck'] = update_healthcheck(client,
                                                                 healthcheck=healthcheck,
                                                                 params=params,
                                                                 name=params['healthcheck_name'],
                                                                 project_id=conn_params['project_id'],
                                                                 resource_type=params['healthcheck_type'])
        json_output['updated_healthcheck'] = changed

    json_output['changed'] = changed
    json_output.update(params)
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
