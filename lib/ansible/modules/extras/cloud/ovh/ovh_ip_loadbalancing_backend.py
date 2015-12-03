#!/usr/bin/env python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: ovh_ip_loadbalancing_backend
short_description: Manage OVH IP LoadBalancing backends
description:
    - Manage OVH (French European hosting provider) LoadBalancing IP backends
version_added: "1.9"
author: Pascal HERAUD @pascalheraud
notes:
    - Uses the python OVH Api U(https://github.com/ovh/python-ovh). You have to create an application (a key and secret) with a consummer key as described into U(https://eu.api.ovh.com/g934.first_step_with_api)
requirements: 
    - ovh >  0.35
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
            - Determines wether the backend is to be created/modified or deleted
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
    
'''

EXAMPLES = '''
# Adds or modify a backend to a loadbalancing
- ovh_ip_loadbalancing name=ip-1.1.1.1 ip=212.1.1.1 state=present probe=none weight=8 endpoint=ovh-eu application_key=yourkey application_secret=yoursecret consumer_key=yourconsumerkey

# Removes a backend from a loadbalancing
- ovh_ip_loadbalancing name=ip-1.1.1.1 ip=212.1.1.1 state=absent endpoint=ovh-eu application_key=yourkey application_secret=yoursecret consumer_key=yourconsumerkey
'''

import sys
import ovh

def getOvhClient(ansibleModule):
    endpoint  = ansibleModule.params.get('endpoint')
    application_key  = ansibleModule.params.get('application_key')
    application_secret  = ansibleModule.params.get('application_secret')
    consumer_key  = ansibleModule.params.get('consumer_key')

    return ovh.Client(
        endpoint=endpoint,
        application_key=application_key,
        application_secret=application_secret,
        consumer_key=consumer_key
    )

def waitForNoTask(client, name):
    while len(client.get('/ip/loadBalancing/{}/task'.format(name)))>0:
        time.sleep(1)  # Delay for 1 sec
    
def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            backend = dict(required=True),
            weight = dict(default='8'),
            probe = dict(default='none', choices =['none', 'http', 'icmp' , 'oco']),
            state = dict(default='present', choices=['present', 'absent']),
            endpoint = dict(required=True),
            application_key = dict(required=True),
            application_secret = dict(required=True),
            consumer_key = dict(required=True),
        )
    )

    # Get parameters
    name   = module.params.get('name')
    state  = module.params.get('state')
    backend  = module.params.get('backend')
    weight  = long(module.params.get('weight'))
    probe  = module.params.get('probe')

    # Connect to OVH API
    client = getOvhClient(module)

    # Check that the load balancing exists
    loadBalancings = client.get('/ip/loadBalancing')
    if not name in loadBalancings:
        module.fail_json(msg='IP LoadBalancing {} does not exist'.format(name))

    # Check that no task is pending before going on
    waitForNoTask(client, name)

    backends = client.get('/ip/loadBalancing/{}/backend'.format(name))
    
    backendExists = backend in backends
    moduleChanged = False
    if (state=="absent") :
        if (backendExists) :
            # Remove backend
            client.delete('/ip/loadBalancing/{}/backend/{}'.format(name, backend))
            waitForNoTask(client, name)
            moduleChanged = True
        else :
            moduleChanged = False
    if (state=="present") :
        if (backendExists) :
            moduleChanged = False
            # Get properties
            backendProperties = client.get('/ip/loadBalancing/{}/backend/{}'.format(name, backend))
            if (backendProperties['weight'] != weight):
                # Change weight
                client.post('/ip/loadBalancing/{}/backend/{}/setWeight'.format(name, backend), weight=weight)
                waitForNoTask(client, name)
                moduleChanged = True
            if (backendProperties['probe'] != probe):
                # Change probe
                backendProperties['probe'] = probe
                client.put('/ip/loadBalancing/{}/backend/{}'.format(name, backend), probe=probe )
                waitForNoTask(client, name)
                moduleChanged = True
                
        else :
            # Creates backend
            client.post('/ip/loadBalancing/{}/backend'.format(name), ipBackend=backend, probe=probe, weight=weight)
            waitForNoTask(client, name)
            moduleChanged = True
                                             
    module.exit_json(changed=moduleChanged)

    # We should never reach here
    module.fail_json(msg='Internal ovh_ip_loadbalancing_backend module error')


# import module snippets
from ansible.module_utils.basic import *

main()
