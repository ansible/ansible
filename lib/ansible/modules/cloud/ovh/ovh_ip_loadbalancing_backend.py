#!/usr/bin/python

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovh_ip_loadbalancing_backend
short_description: Manage OVH IP LoadBalancing backends
description:
    - Manage OVH (French European hosting provider) LoadBalancing IP backends
version_added: "2.2"
author: Pascal HERAUD @pascalheraud
notes:
    - Uses the python OVH Api U(https://github.com/ovh/python-ovh).
      You have to create an application (a key and secret) with a consummer
      key as described into U(https://eu.api.ovh.com/g934.first_step_with_api)
requirements:
    - ovh >  0.3.5
options:
    name:
        required: true
        description:
            - Name of the LoadBalancing internal name (ip-X.X.X.X)
    backend:
        required: true
        description:
            - The IP address of the backend to update / modify / delete
    state:
        required: false
        default: present
        choices: ['present', 'absent']
        description:
            - Determines whether the backend is to be created/modified
              or deleted
    probe:
        required: false
        default: none
        choices: ['none', 'http', 'icmp' , 'oco']
        description:
            - Determines the type of probe to use for this backend
    weight:
        required: false
        default: 8
        description:
            - Determines the weight for this backend
    endpoint:
        required: true
        description:
            - The endpoint to use ( for instance ovh-eu)
    application_key:
        required: true
        description:
            - The applicationKey to use
    application_secret:
        required: true
        description:
            - The application secret to use
    consumer_key:
        required: true
        description:
            - The consumer key to use
    timeout:
        required: false
        default: 120
        description:
            - The timeout in seconds used to wait for a task to be
              completed.

'''

EXAMPLES = '''
# Adds or modify the backend '212.1.1.1' to a
# loadbalancing 'ip-1.1.1.1'
- ovh_ip_loadbalancing:
    name: ip-1.1.1.1
    backend: 212.1.1.1
    state: present
    probe: none
    weight: 8
    endpoint: ovh-eu
    application_key: yourkey
    application_secret: yoursecret
    consumer_key: yourconsumerkey

# Removes a backend '212.1.1.1' from a loadbalancing 'ip-1.1.1.1'
- ovh_ip_loadbalancing:
    name: ip-1.1.1.1
    backend: 212.1.1.1
    state: absent
    endpoint: ovh-eu
    application_key: yourkey
    application_secret: yoursecret
    consumer_key: yourconsumerkey
'''

RETURN = '''
'''

import time

try:
    import ovh
    import ovh.exceptions
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False

from ansible.module_utils.basic import AnsibleModule


def getOvhClient(ansibleModule):
    endpoint = ansibleModule.params.get('endpoint')
    application_key = ansibleModule.params.get('application_key')
    application_secret = ansibleModule.params.get('application_secret')
    consumer_key = ansibleModule.params.get('consumer_key')

    return ovh.Client(
        endpoint=endpoint,
        application_key=application_key,
        application_secret=application_secret,
        consumer_key=consumer_key
    )


def waitForNoTask(client, name, timeout):
    currentTimeout = timeout
    while len(client.get('/ip/loadBalancing/{0}/task'.format(name))) > 0:
        time.sleep(1)  # Delay for 1 sec
        currentTimeout -= 1
        if currentTimeout < 0:
            return False
    return True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            backend=dict(required=True),
            weight=dict(default=8, type='int'),
            probe=dict(default='none',
                       choices=['none', 'http', 'icmp', 'oco']),
            state=dict(default='present', choices=['present', 'absent']),
            endpoint=dict(required=True),
            application_key=dict(required=True, no_log=True),
            application_secret=dict(required=True, no_log=True),
            consumer_key=dict(required=True, no_log=True),
            timeout=dict(default=120, type='int')
        )
    )

    if not HAS_OVH:
        module.fail_json(msg='ovh-api python module'
           'is required to run this module ')

    # Get parameters
    name = module.params.get('name')
    state = module.params.get('state')
    backend = module.params.get('backend')
    weight = module.params.get('weight')
    probe = module.params.get('probe')
    timeout = module.params.get('timeout')

    # Connect to OVH API
    client = getOvhClient(module)

    # Check that the load balancing exists
    try:
        loadBalancings = client.get('/ip/loadBalancing')
    except APIError as apiError:
        module.fail_json(
            msg='Unable to call OVH api for getting the list of loadBalancing, '
                'check application key, secret, consumerkey and parameters. '
                'Error returned by OVH api was : {0}'.format(apiError))

    if name not in loadBalancings:
        module.fail_json(msg='IP LoadBalancing {0} does not exist'.format(name))

    # Check that no task is pending before going on
    try:
        if not waitForNoTask(client, name, timeout):
            module.fail_json(
                msg='Timeout of {0} seconds while waiting for no pending '
                    'tasks before executing the module '.format(timeout))
    except APIError as apiError:
        module.fail_json(
            msg='Unable to call OVH api for getting the list of pending tasks '
                'of the loadBalancing, check application key, secret, consumerkey '
                'and parameters. Error returned by OVH api was : {0}'
                .format(apiError))

    try:
        backends = client.get('/ip/loadBalancing/{0}/backend'.format(name))
    except APIError as apiError:
        module.fail_json(
            msg='Unable to call OVH api for getting the list of backends '
                'of the loadBalancing, check application key, secret, consumerkey '
                'and parameters. Error returned by OVH api was : {0}'
            .format(apiError))

    backendExists = backend in backends
    moduleChanged = False
    if state == "absent":
        if backendExists:
            # Remove backend
            try:
                client.delete(
                    '/ip/loadBalancing/{0}/backend/{1}'.format(name, backend))
                if not waitForNoTask(client, name, timeout):
                    module.fail_json(
                        msg='Timeout of {0} seconds while waiting for completion '
                            'of removing backend task'.format(timeout))
            except APIError as apiError:
                module.fail_json(
                    msg='Unable to call OVH api for deleting the backend, '
                        'check application key, secret, consumerkey and '
                        'parameters. Error returned by OVH api was : {0}'
                        .format(apiError))
            moduleChanged = True
    else:
        if backendExists:
            # Get properties
            try:
                backendProperties = client.get(
                    '/ip/loadBalancing/{0}/backend/{1}'.format(name, backend))
            except APIError as apiError:
                module.fail_json(
                    msg='Unable to call OVH api for getting the backend properties, '
                        'check application key, secret, consumerkey and '
                        'parameters. Error returned by OVH api was : {0}'
                        .format(apiError))

            if (backendProperties['weight'] != weight):
                # Change weight
                try:
                    client.post(
                        '/ip/loadBalancing/{0}/backend/{1}/setWeight'
                        .format(name, backend), weight=weight)
                    if not waitForNoTask(client, name, timeout):
                        module.fail_json(
                            msg='Timeout of {0} seconds while waiting for completion '
                                'of setWeight to backend task'
                                .format(timeout))
                except APIError as apiError:
                    module.fail_json(
                        msg='Unable to call OVH api for updating the weight of the '
                            'backend, check application key, secret, consumerkey '
                            'and parameters. Error returned by OVH api was : {0}'
                            .format(apiError))
                moduleChanged = True

            if (backendProperties['probe'] != probe):
                # Change probe
                backendProperties['probe'] = probe
                try:
                    client.put(
                        '/ip/loadBalancing/{0}/backend/{1}'
                        .format(name, backend), probe=probe)
                    if not waitForNoTask(client, name, timeout):
                        module.fail_json(
                            msg='Timeout of {0} seconds while waiting for completion of '
                                'setProbe to backend task'
                                .format(timeout))
                except APIError as apiError:
                    module.fail_json(
                        msg='Unable to call OVH api for updating the propbe of '
                            'the backend, check application key, secret, '
                            'consumerkey and parameters. Error returned by OVH api '
                            'was : {0}'
                            .format(apiError))
                moduleChanged = True

        else:
            # Creates backend
            try:
                try:
                    client.post('/ip/loadBalancing/{0}/backend'.format(name),
                                ipBackend=backend, probe=probe, weight=weight)
                except APIError as apiError:
                    module.fail_json(
                        msg='Unable to call OVH api for creating the backend, check '
                            'application key, secret, consumerkey and parameters. '
                            'Error returned by OVH api was : {0}'
                            .format(apiError))

                if not waitForNoTask(client, name, timeout):
                    module.fail_json(
                        msg='Timeout of {0} seconds while waiting for completion of '
                            'backend creation task'.format(timeout))
            except APIError as apiError:
                module.fail_json(
                    msg='Unable to call OVH api for creating the backend, check '
                        'application key, secret, consumerkey and parameters. '
                        'Error returned by OVH api was : {0}'.format(apiError))
            moduleChanged = True

    module.exit_json(changed=moduleChanged)


if __name__ == '__main__':
    main()
