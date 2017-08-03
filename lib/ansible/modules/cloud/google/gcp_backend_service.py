#!/usr/bin/python
# Copyright 2017 Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}
DOCUMENTATION = '''
module: gcp_backend_service
version_added: "2.4"
short_description: Create or Destroy a Backend Service.
description:
    - Create or Destroy a Backend Service.  See
      U(https://cloud.google.com/compute/docs/load-balancing/http/backend-service) for an overview.
      Full install/configuration instructions for the Google Cloud modules can
      be found in the comments of ansible/test/gce_tests.py.
requirements:
  - "python >= 2.6"
  - "apache-libcloud >= 1.3.0"
notes:
  - Update is not currently supported.
  - Only global backend services are currently supported. Regional backends not currently supported.
  - Internal load balancing not currently supported.
author:
  - "Tom Melendez (@supertom) <tom@supertom.com>"
options:
  backend_service_name:
    description:
       - Name of the Backend Service.
    required: true
  backends:
    description:
       - List of backends that make up the backend service. A backend is made up of
         an instance group and optionally several other parameters.  See
         U(https://cloud.google.com/compute/docs/reference/latest/backendServices)
         for details.
    required: true
  healthchecks:
    description:
       - List of healthchecks. Only one healthcheck is supported.
    required: true
  enable_cdn:
    description:
       - If true, enable Cloud CDN for this Backend Service.
    required: false
  port_name:
    description:
      - Name of the port on the managed instance group (MIG) that backend
        services can forward data to. Required for external load balancing.
    required: false
    default: null
  protocol:
    description:
       - The protocol this Backend Service uses to communicate with backends.
         Possible values are HTTP, HTTPS, TCP, and SSL. The default is HTTP.
    required: false
  timeout:
    description:
       - How many seconds to wait for the backend before considering it a failed
         request. Default is 30 seconds. Valid range is 1-86400.
    required: false
  service_account_email:
    description:
      - Service account email
    required: false
    default: null
  credentials_file:
    description:
      - Path to the JSON file associated with the service account email.
    default: null
    required: false
  project_id:
    description:
      - GCE project ID.
    required: false
    default: null
  state:
    description:
      - Desired state of the resource
    required: false
    default: "present"
    choices: ["absent", "present"]
'''

EXAMPLES = '''
- name: Create Minimum Backend Service
  gcp_backend_service:
    service_account_email: "{{ service_account_email }}"
    credentials_file: "{{ credentials_file }}"
    project_id: "{{ project_id }}"
    backend_service_name: "{{ bes }}"
    backends:
    - instance_group: managed_instance_group_1
    healthchecks:
    - name: healthcheck_name_for_backend_service
    port_name: myhttpport
    state: present

- name: Create BES with extended backend parameters
  gcp_backend_service:
    service_account_email: "{{ service_account_email }}"
    credentials_file: "{{ credentials_file }}"
    project_id: "{{ project_id }}"
    backend_service_name: "{{ bes }}"
    backends:
    - instance_group: managed_instance_group_1
      max_utilization: 0.6
      max_rate: 10
    - instance_group: managed_instance_group_2
      max_utilization: 0.5
      max_rate: 4
    healthchecks:
    - name: healthcheck_name_for_backend_service
    port_name: myhttpport
    state: present
    timeout: 60
'''

RETURN = '''
backend_service_created:
    description: Indicator Backend Service was created.
    returned: When a Backend Service is created.
    type: boolean
    sample: "True"
backend_service_deleted:
    description: Indicator Backend Service was deleted.
    returned: When a Backend Service is deleted.
    type: boolean
    sample: "True"
backend_service_name:
    description: Name of the Backend Service.
    returned: Always.
    type: string
    sample: "my-backend-service"
backends:
    description: List of backends (comprised of instance_group) that
                 make up a Backend Service.
    returned: When a Backend Service exists.
    type: list
    sample: "[ { 'instance_group': 'mig_one', 'zone': 'us-central1-b'} ]"
enable_cdn:
    description: If Cloud CDN is enabled. null if not set.
    returned: When a backend service exists.
    type: boolean
    sample: "True"
healthchecks:
    description: List of healthchecks applied to the Backend Service.
    returned: When a Backend Service exists.
    type: list
    sample: "[ 'my-healthcheck' ]"
protocol:
    description: Protocol used to communicate with the Backends.
    returned: When a Backend Service exists.
    type: string
    sample: "HTTP"
port_name:
    description: Name of Backend Port.
    returned: When a Backend Service exists.
    type: string
    sample: "myhttpport"
timeout:
    description: In seconds, how long before a request sent to a backend is
                 considered failed.
    returned: If specified.
    type: int
    sample: "myhttpport"
'''

try:
    from ast import literal_eval
    HAS_PYTHON26 = True
except ImportError:
    HAS_PYTHON26 = False

try:
    import libcloud
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, \
        ResourceExistsError, ResourceInUseError, ResourceNotFoundError
    from libcloud.compute.drivers.gce import GCEAddress
    _ = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gce import gce_connect
from ansible.module_utils.gcp import check_params


def _validate_params(params):
    """
    Validate backend_service params.

    This function calls _validate_backend_params to verify
    the backend-specific parameters.

    :param params: Ansible dictionary containing configuration.
    :type  params: ``dict``

    :return: True or raises ValueError
    :rtype: ``bool`` or `class:ValueError`
    """
    fields = [
        {'name': 'timeout', 'type': int, 'min': 1, 'max': 86400},
    ]
    try:
        check_params(params, fields)
        _validate_backend_params(params['backends'])
    except:
        raise

    return (True, '')


def _validate_backend_params(backends):
    """
    Validate configuration for backends.

    :param backends: Ansible dictionary containing backends configuration (only).
    :type  backends: ``dict``

    :return: True or raises ValueError
    :rtype: ``bool`` or `class:ValueError`
    """
    fields = [
        {'name': 'balancing_mode', 'type': str, 'values': ['UTILIZATION', 'RATE', 'CONNECTION']},
        {'name': 'max_utilization', 'type': float},
        {'name': 'max_connections', 'type': int},
        {'name': 'max_rate', 'type': int},
        {'name': 'max_rate_per_instance', 'type': float},
    ]

    if not backends:
        raise ValueError('backends should be a list.')

    for backend in backends:
        try:
            check_params(backend, fields)
        except:
            raise

        if 'max_rate' in backend and 'max_rate_per_instance' in backend:
            raise ValueError('Both maxRate or maxRatePerInstance cannot be set.')

    return (True, '')


def get_backend_service(gce, name):
    """
    Get a Backend Service from GCE.

    :param gce: An initialized GCE driver object.
    :type gce:  :class: `GCENodeDriver`

    :param name: Name of the Backend Service.
    :type name:  ``str``

    :return: A GCEBackendService object or None.
    :rtype: :class: `GCEBackendService` or None
    """
    try:
        # Does the Backend Service already exist?
        return gce.ex_get_backendservice(name=name)

    except ResourceNotFoundError:
        return None


def get_healthcheck(gce, name):
    return gce.ex_get_healthcheck(name)


def get_instancegroup(gce, name, zone=None):
    return gce.ex_get_instancegroup(name=name, zone=zone)


def create_backend_service(gce, params):
    """
    Create a new Backend Service.

    :param gce: An initialized GCE driver object.
    :type gce:  :class: `GCENodeDriver`

    :param params: Dictionary of parameters needed by the module.
    :type params:  ``dict``

    :return: Tuple with changed stats
    :rtype: tuple in the format of (bool, bool)
    """
    from copy import deepcopy

    changed = False
    return_data = False
    # only one healthcheck is currently supported
    hc_name = params['healthchecks'][0]
    hc = get_healthcheck(gce, hc_name)
    backends = []
    for backend in params['backends']:
        ig = get_instancegroup(gce, backend['instance_group'],
                               backend.get('zone', None))
        kwargs = deepcopy(backend)
        kwargs['instance_group'] = ig
        backends.append(gce.ex_create_backend(
            **kwargs))

    bes = gce.ex_create_backendservice(
        name=params['backend_service_name'], healthchecks=[hc], backends=backends,
        enable_cdn=params['enable_cdn'], port_name=params['port_name'],
        timeout_sec=params['timeout'], protocol=params['protocol'])

    if bes:
        changed = True
        return_data = True

    return (changed, return_data)


def delete_backend_service(bes):
    """
    Delete a Backend Service. The Instance Groups are NOT destroyed.
    """
    changed = False
    return_data = False
    if bes.destroy():
        changed = True
        return_data = True
    return (changed, return_data)


def main():
    module = AnsibleModule(argument_spec=dict(
        backends=dict(type='list', required=True),
        backend_service_name=dict(required=True),
        healthchecks=dict(type='list', required=True),
        service_account_email=dict(),
        service_account_permissions=dict(type='list'),
        enable_cdn=dict(type='bool'),
        port_name=dict(type='str'),
        protocol=dict(type='str', default='TCP',
                      choices=['HTTP', 'HTTPS', 'SSL', 'TCP']),
        timeout=dict(type='int'),
        state=dict(choices=['absent', 'present'], default='present'),
        pem_file=dict(),
        credentials_file=dict(),
        project_id=dict(), ), )

    if not HAS_PYTHON26:
        module.fail_json(
            msg="GCE module requires python's 'ast' module, python v2.6+")
    if not HAS_LIBCLOUD:
        module.fail_json(
            msg='libcloud with GCE Backend Service support (1.3+) required for this module.')

    gce = gce_connect(module)
    if not hasattr(gce, 'ex_create_instancegroupmanager'):
        module.fail_json(
            msg='libcloud with GCE Backend Service support (1.3+) required for this module.',
            changed=False)

    params = {}
    params['state'] = module.params.get('state')
    params['backend_service_name'] = module.params.get('backend_service_name')
    params['backends'] = module.params.get('backends')
    params['healthchecks'] = module.params.get('healthchecks')
    params['enable_cdn'] = module.params.get('enable_cdn', None)
    params['port_name'] = module.params.get('port_name', None)
    params['protocol'] = module.params.get('protocol', None)
    params['timeout'] = module.params.get('timeout', None)

    try:
        _validate_params(params)
    except Exception as e:
        module.fail_json(msg=e.message, changed=False)

    changed = False
    json_output = {'state': params['state']}
    bes = get_backend_service(gce, params['backend_service_name'])

    if not bes:
        if params['state'] == 'absent':
            # Doesn't exist and state==absent.
            changed = False
            module.fail_json(
                msg="Cannot delete unknown backend service: %s" %
                (params['backend_service_name']))
        else:
            # Create
            (changed, json_output['backend_service_created']) = create_backend_service(gce,
                                                                                       params)
    elif params['state'] == 'absent':
        # Delete
        (changed, json_output['backend_service_deleted']) = delete_backend_service(bes)
    else:
        # TODO(supertom): Add update support when it is available in libcloud.
        changed = False

    json_output['changed'] = changed
    json_output.update(params)
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
