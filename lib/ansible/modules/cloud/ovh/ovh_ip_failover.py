#!/usr/bin/python

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovh_ip_failover
short_description: Manage OVH IP failover address
description:
    - Manage OVH (French European hosting provider) IP Failover Address. For now, this module can only be used to move
      an ip failover (or failover block) between services
version_added: "2.8"
author: "Pascal HERAUD (@pascalheraud)"
notes:
    - Uses the python OVH Api U(https://github.com/ovh/python-ovh).
      You have to create an application (a key and secret) with a consummer
      key as described into U(https://eu.api.ovh.com/g934.first_step_with_api)
requirements:
    - ovh >=  0.4.8
options:
    name:
        required: true
        description:
            - The IP address to manage (can be a single IP like 1.1.1.1
              or a block like 1.1.1.1/28 )
    service:
        required: true
        description:
            - The name of the OVH service this IP address should be routed
    endpoint:
        required: true
        description:
            - The endpoint to use ( for instance ovh-eu)
    wait_completion:
        required: false
        default: true
        type: bool
        description:
            - If true, the module will wait for the IP address to be moved.
              If false, exit without waiting. The taskId will be returned
              in module output
    wait_task_completion:
        required: false
        default: 0
        description:
            - If not 0, the module will wait for this task id to be
              completed. Use wait_task_completion if you want to wait for
              completion of a previously executed task with
              wait_completion=false. You can execute this module repeatedly on
              a list of failover IPs using wait_completion=false (see examples)
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
              completed. Default is 120 seconds.

'''

EXAMPLES = '''
# Route an IP address 1.1.1.1 to the service ns666.ovh.net
- ovh_ip_failover:
    name: 1.1.1.1
    service: ns666.ovh.net
    endpoint: ovh-eu
    application_key: yourkey
    application_secret: yoursecret
    consumer_key: yourconsumerkey
- ovh_ip_failover:
    name: 1.1.1.1
    service: ns666.ovh.net
    endpoint: ovh-eu
    wait_completion: false
    application_key: yourkey
    application_secret: yoursecret
    consumer_key: yourconsumerkey
  register: moved
- ovh_ip_failover:
    name: 1.1.1.1
    service: ns666.ovh.net
    endpoint: ovh-eu
    wait_task_completion: "{{moved.taskId}}"
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
from ansible.module_utils.six.moves.urllib.parse import quote_plus


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
    while client.get('/ip/{0}/task'.format(quote_plus(name)),
                     function='genericMoveFloatingIp',
                     status='todo'):
        time.sleep(1)  # Delay for 1 sec
        currentTimeout -= 1
        if currentTimeout < 0:
            return False
    return True


def waitForTaskDone(client, name, taskId, timeout):
    currentTimeout = timeout
    while True:
        task = client.get('/ip/{0}/task/{1}'.format(quote_plus(name), taskId))
        if task['status'] == 'done':
            return True
        time.sleep(5)  # Delay for 5 sec because it's long to wait completion, do not harass the API
        currentTimeout -= 5
        if currentTimeout < 0:
            return False
    return True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            service=dict(required=True),
            endpoint=dict(required=True),
            wait_completion=dict(default=True, type='bool'),
            wait_task_completion=dict(default=0, type='int'),
            application_key=dict(required=True, no_log=True),
            application_secret=dict(required=True, no_log=True),
            consumer_key=dict(required=True, no_log=True),
            timeout=dict(default=120, type='int')
        ),
        supports_check_mode=True
    )

    result = dict(
        changed=False
    )

    if not HAS_OVH:
        module.fail_json(msg='ovh-api python module is required to run this module ')

    # Get parameters
    name = module.params.get('name')
    service = module.params.get('service')
    timeout = module.params.get('timeout')
    wait_completion = module.params.get('wait_completion')
    wait_task_completion = module.params.get('wait_task_completion')

    # Connect to OVH API
    client = getOvhClient(module)

    # Check that the load balancing exists
    try:
        ips = client.get('/ip', ip=name, type='failover')
    except APIError as apiError:
        module.fail_json(
            msg='Unable to call OVH api for getting the list of ips, '
                'check application key, secret, consumerkey and parameters. '
                'Error returned by OVH api was : {0}'.format(apiError))

    if name not in ips and '{0}/32'.format(name) not in ips:
        module.fail_json(msg='IP {0} does not exist'.format(name))

    # Check that no task is pending before going on
    try:
        if not waitForNoTask(client, name, timeout):
            module.fail_json(
                msg='Timeout of {0} seconds while waiting for no pending '
                    'tasks before executing the module '.format(timeout))
    except APIError as apiError:
        module.fail_json(
            msg='Unable to call OVH api for getting the list of pending tasks '
                'of the ip, check application key, secret, consumerkey '
                'and parameters. Error returned by OVH api was : {0}'
                .format(apiError))

    try:
        ipproperties = client.get('/ip/{0}'.format(quote_plus(name)))
    except APIError as apiError:
        module.fail_json(
            msg='Unable to call OVH api for getting the properties '
                'of the ip, check application key, secret, consumerkey '
                'and parameters. Error returned by OVH api was : {0}'
            .format(apiError))

    if ipproperties['routedTo']['serviceName'] != service:
        if not module.check_mode:
            if wait_task_completion == 0:
                # Move the IP and get the created taskId
                task = client.post('/ip/{0}/move'.format(quote_plus(name)), to=service)
                taskId = task['taskId']
                result['moved'] = True
            else:
                # Just wait for the given taskId to be completed
                taskId = wait_task_completion
                result['moved'] = False
            result['taskId'] = taskId
            if wait_completion or wait_task_completion != 0:
                if not waitForTaskDone(client, name, taskId, timeout):
                    module.fail_json(
                        msg='Timeout of {0} seconds while waiting for completion '
                            'of move ip to service'.format(timeout))
                result['waited'] = True
            else:
                result['waited'] = False
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
