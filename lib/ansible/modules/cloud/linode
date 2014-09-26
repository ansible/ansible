#!/usr/bin/python
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

DOCUMENTATION = '''
---
module: linode
short_description: create / delete / stop / restart an instance in Linode Public Cloud
description:
     - creates / deletes a Linode Public Cloud instance and optionally waits for it to be 'running'.
version_added: "1.3"
options:
  state:
    description:
     - Indicate desired state of the resource
    choices: ['present', 'active', 'started', 'absent', 'deleted', 'stopped', 'restarted']
    default: present
  api_key:
    description:
     - Linode API key
    default: null
  name:
    description:
     - Name to give the instance (alphanumeric, dashes, underscore)
     - To keep sanity on the Linode Web Console, name is prepended with LinodeID_
    default: null
    type: string
  linode_id:
    description:
     - Unique ID of a linode server
    aliases: lid
    default: null
    type: integer
  plan:
    description:
     - plan to use for the instance (Linode plan)
    default: null
    type: integer
  payment_term:
    description:
     - payment term to use for the instance (payment term in months)
    default: 1
    type: integer
    choices: [1, 12, 24]
  password:
    description:
     - root password to apply to a new server (auto generated if missing)
    default: null
    type: string
  ssh_pub_key:
    description:
     - SSH public key applied to root user
    default: null
    type: string
  swap:
    description:
     - swap size in MB
    default: 512
    type: integer
  distribution:
    description:
     - distribution to use for the instance (Linode Distribution)
    default: null
    type: integer
  datacenter:
    description:
     - datacenter to create an instance in (Linode Datacenter)
    default: null
    type: integer
  wait:
    description:
     - wait for the instance to be in state 'running' before returning
    default: "no"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
     - how long before wait gives up, in seconds
    default: 300
requirements: [ "linode-python", "pycurl" ]
author: Vincent Viallet
notes:
  - LINODE_API_KEY env variable can be used instead
'''

EXAMPLES = '''
# Create a server
- local_action:
     module: linode
     api_key: 'longStringFromLinodeApi'
     name: linode-test1
     plan: 1
     datacenter: 2
     distribution: 99
     password: 'superSecureRootPassword'
     ssh_pub_key: 'ssh-rsa qwerty'
     swap: 768
     wait: yes
     wait_timeout: 600
     state: present

# Ensure a running server (create if missing)
- local_action:
     module: linode
     api_key: 'longStringFromLinodeApi'
     name: linode-test1
     linode_id: 12345678
     plan: 1
     datacenter: 2
     distribution: 99
     password: 'superSecureRootPassword'
     ssh_pub_key: 'ssh-rsa qwerty'
     swap: 768
     wait: yes
     wait_timeout: 600
     state: present

# Delete a server
- local_action:
     module: linode
     api_key: 'longStringFromLinodeApi'
     name: linode-test1
     linode_id: 12345678
     state: absent

# Stop a server
- local_action:
     module: linode
     api_key: 'longStringFromLinodeApi'
     name: linode-test1
     linode_id: 12345678
     state: stopped

# Reboot a server
- local_action:
     module: linode
     api_key: 'longStringFromLinodeApi'
     name: linode-test1
     linode_id: 12345678
     state: restarted
'''

import sys
import time
import os

try:
    import pycurl
except ImportError:
    print("failed=True msg='pycurl required for this module'")
    sys.exit(1)


try:
    from linode import api as linode_api
except ImportError:
    print("failed=True msg='linode-python required for this module'")
    sys.exit(1)


def randompass():
    '''
    Generate a long random password that comply to Linode requirements
    '''
    # Linode API currently requires the following: 
    # It must contain at least two of these four character classes: 
    # lower case letters - upper case letters - numbers - punctuation
    # we play it safe :)
    import random
    import string
    # as of python 2.4, this reseeds the PRNG from urandom
    random.seed() 
    lower = ''.join(random.choice(string.ascii_lowercase) for x in range(6))
    upper = ''.join(random.choice(string.ascii_uppercase) for x in range(6))
    number = ''.join(random.choice(string.digits) for x in range(6))
    punct = ''.join(random.choice(string.punctuation) for x in range(6))
    p = lower + upper + number + punct
    return ''.join(random.sample(p, len(p)))

def getInstanceDetails(api, server):
    '''
    Return the details of an instance, populating IPs, etc.
    '''
    instance = {'id': server['LINODEID'],
                'name': server['LABEL'],
                'public': [],
                'private': []}

    # Populate with ips
    for ip in api.linode_ip_list(LinodeId=server['LINODEID']):
        if ip['ISPUBLIC'] and 'ipv4' not in instance:
            instance['ipv4'] = ip['IPADDRESS']
            instance['fqdn'] = ip['RDNS_NAME']
        if ip['ISPUBLIC']:
            instance['public'].append({'ipv4': ip['IPADDRESS'],
                                       'fqdn': ip['RDNS_NAME'],
                                       'ip_id': ip['IPADDRESSID']})
        else:
            instance['private'].append({'ipv4': ip['IPADDRESS'],
                                        'fqdn': ip['RDNS_NAME'],
                                        'ip_id': ip['IPADDRESSID']})
    return instance

def linodeServers(module, api, state, name, plan, distribution, datacenter, linode_id, 
                  payment_term, password, ssh_pub_key, swap, wait, wait_timeout):
    instances = []
    changed = False
    new_server = False   
    servers = []
    disks = []
    configs = []
    jobs = []

    # See if we can match an existing server details with the provided linode_id
    if linode_id:
        # For the moment we only consider linode_id as criteria for match
        # Later we can use more (size, name, etc.) and update existing
        servers = api.linode_list(LinodeId=linode_id)
        # Attempt to fetch details about disks and configs only if servers are 
        # found with linode_id
        if servers:
            disks = api.linode_disk_list(LinodeId=linode_id)
            configs = api.linode_config_list(LinodeId=linode_id)

    # Act on the state
    if state in ('active', 'present', 'started'):
        # TODO: validate all the plan / distribution / datacenter are valid

        # Multi step process/validation:
        #  - need linode_id (entity)
        #  - need disk_id for linode_id - create disk from distrib
        #  - need config_id for linode_id - create config (need kernel)
        
        # Any create step triggers a job that need to be waited for.
        if not servers:
            for arg in ('name', 'plan', 'distribution', 'datacenter'):
                if not eval(arg):
                    module.fail_json(msg='%s is required for active state' % arg)
            # Create linode entity
            new_server = True
            try:
                res = api.linode_create(DatacenterID=datacenter, PlanID=plan, 
                                        PaymentTerm=payment_term)
                linode_id = res['LinodeID']
                # Update linode Label to match name
                api.linode_update(LinodeId=linode_id, Label='%s_%s' % (linode_id, name))
                # Save server
                servers = api.linode_list(LinodeId=linode_id)
            except Exception, e:
                module.fail_json(msg = '%s' % e.value[0]['ERRORMESSAGE'])

        if not disks:
            for arg in ('name', 'linode_id', 'distribution'):
                if not eval(arg):
                    module.fail_json(msg='%s is required for active state' % arg)
            # Create disks (1 from distrib, 1 for SWAP)
            new_server = True
            try:
                if not password:
                    # Password is required on creation, if not provided generate one
                    password = randompass()
                if not swap:
                    swap = 512
                # Create data disk
                size = servers[0]['TOTALHD'] - swap
                if ssh_pub_key:
                    res = api.linode_disk_createfromdistribution(
                              LinodeId=linode_id, DistributionID=distribution, 
                              rootPass=password, rootSSHKey=ssh_pub_key,
                              Label='%s data disk (lid: %s)' % (name, linode_id), Size=size)
                else:
                    res = api.linode_disk_createfromdistribution(
                              LinodeId=linode_id, DistributionID=distribution, rootPass=password, 
                              Label='%s data disk (lid: %s)' % (name, linode_id), Size=size)
                jobs.append(res['JobID'])
                # Create SWAP disk
                res = api.linode_disk_create(LinodeId=linode_id, Type='swap', 
                                             Label='%s swap disk (lid: %s)' % (name, linode_id), 
                                             Size=swap)
                jobs.append(res['JobID'])
            except Exception, e:
                # TODO: destroy linode ?
                module.fail_json(msg = '%s' % e.value[0]['ERRORMESSAGE'])

        if not configs:
            for arg in ('name', 'linode_id', 'distribution'):
                if not eval(arg):
                    module.fail_json(msg='%s is required for active state' % arg)

            # Check architecture
            for distrib in api.avail_distributions():
                if distrib['DISTRIBUTIONID'] != distribution:
                    continue
                arch = '32'
                if distrib['IS64BIT']:
                    arch = '64'
                break

            # Get latest kernel matching arch
            for kernel in api.avail_kernels():
                if not kernel['LABEL'].startswith('Latest %s' % arch):
                    continue
                kernel_id = kernel['KERNELID']
                break

            # Get disk list
            disks_id = []
            for disk in api.linode_disk_list(LinodeId=linode_id):
                if disk['TYPE'] == 'ext3':
                    disks_id.insert(0, str(disk['DISKID']))
                    continue
                disks_id.append(str(disk['DISKID']))
            # Trick to get the 9 items in the list
            while len(disks_id) < 9:
                disks_id.append('')
            disks_list = ','.join(disks_id)

            # Create config
            new_server = True
            try:
                api.linode_config_create(LinodeId=linode_id, KernelId=kernel_id,
                                         Disklist=disks_list, Label='%s config' % name)
                configs = api.linode_config_list(LinodeId=linode_id)
            except Exception, e:
                module.fail_json(msg = '%s' % e.value[0]['ERRORMESSAGE'])

        # Start / Ensure servers are running
        for server in servers:
            # Refresh server state
            server = api.linode_list(LinodeId=server['LINODEID'])[0]
            # Ensure existing servers are up and running, boot if necessary
            if server['STATUS'] != 1:
                res = api.linode_boot(LinodeId=linode_id)
                jobs.append(res['JobID'])
                changed = True

            # wait here until the instances are up
            wait_timeout = time.time() + wait_timeout
            while wait and wait_timeout > time.time():
                # refresh the server details
                server = api.linode_list(LinodeId=server['LINODEID'])[0]
                # status:
                #  -2: Boot failed
                #  1: Running
                if server['STATUS'] in (-2, 1):
                    break
                time.sleep(5)
            if wait and wait_timeout <= time.time():
                # waiting took too long
                module.fail_json(msg = 'Timeout waiting on %s (lid: %s)' % 
                                 (server['LABEL'], server['LINODEID']))
            # Get a fresh copy of the server details
            server = api.linode_list(LinodeId=server['LINODEID'])[0]
            if server['STATUS'] == -2:
                module.fail_json(msg = '%s (lid: %s) failed to boot' % 
                                 (server['LABEL'], server['LINODEID']))
            # From now on we know the task is a success
            # Build instance report
            instance = getInstanceDetails(api, server)
            # depending on wait flag select the status
            if wait:
                instance['status'] = 'Running'
            else:
                instance['status'] = 'Starting'

            # Return the root password if this is a new box and no SSH key 
            # has been provided
            if new_server and not ssh_pub_key:
                instance['password'] = password
            instances.append(instance)

    elif state in ('stopped'):
        for arg in ('name', 'linode_id'):
            if not eval(arg):
                module.fail_json(msg='%s is required for active state' % arg)

        if not servers:
            module.fail_json(msg = 'Server %s (lid: %s) not found' % (name, linode_id))

        for server in servers:
            instance = getInstanceDetails(api, server)
            if server['STATUS'] != 2:
                try:
                    res = api.linode_shutdown(LinodeId=linode_id)
                except Exception, e:
                    module.fail_json(msg = '%s' % e.value[0]['ERRORMESSAGE'])
                instance['status'] = 'Stopping'
                changed = True
            else:
                instance['status'] = 'Stopped'
            instances.append(instance)

    elif state in ('restarted'):
        for arg in ('name', 'linode_id'):
            if not eval(arg):
                module.fail_json(msg='%s is required for active state' % arg)

        if not servers:
            module.fail_json(msg = 'Server %s (lid: %s) not found' % (name, linode_id))

        for server in servers:
            instance = getInstanceDetails(api, server)
            try:
                res = api.linode_reboot(LinodeId=server['LINODEID'])
            except Exception, e:
                module.fail_json(msg = '%s' % e.value[0]['ERRORMESSAGE'])
            instance['status'] = 'Restarting'
            changed = True
            instances.append(instance)
            
    elif state in ('absent', 'deleted'):
        for server in servers:
            instance = getInstanceDetails(api, server)
            try:
                api.linode_delete(LinodeId=server['LINODEID'], skipChecks=True)
            except Exception, e:
                module.fail_json(msg = '%s' % e.value[0]['ERRORMESSAGE'])
            instance['status'] = 'Deleting'
            changed = True
            instances.append(instance)

    # Ease parsing if only 1 instance
    if len(instances) == 1:
        module.exit_json(changed=changed, instance=instances[0])
    module.exit_json(changed=changed, instances=instances)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            state = dict(default='present', choices=['active', 'present', 'started',
                                                     'deleted', 'absent', 'stopped',
                                                     'restarted']),
            api_key = dict(),
            name = dict(type='str'),
            plan = dict(type='int'),
            distribution = dict(type='int'),
            datacenter = dict(type='int'),
            linode_id = dict(type='int', aliases=['lid']),
            payment_term = dict(type='int', default=1, choices=[1, 12, 24]),
            password = dict(type='str'),
            ssh_pub_key = dict(type='str'),
            swap = dict(type='int', default=512),
            wait = dict(type='bool', default=True),
            wait_timeout = dict(default=300),
        )
    )

    state = module.params.get('state')
    api_key = module.params.get('api_key')
    name = module.params.get('name')
    plan = module.params.get('plan')
    distribution = module.params.get('distribution')
    datacenter = module.params.get('datacenter')
    linode_id = module.params.get('linode_id')
    payment_term = module.params.get('payment_term')
    password = module.params.get('password')
    ssh_pub_key = module.params.get('ssh_pub_key')
    swap = module.params.get('swap')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))

    # Setup the api_key
    if not api_key:
        try:
            api_key = os.environ['LINODE_API_KEY']
        except KeyError, e:
            module.fail_json(msg = 'Unable to load %s' % e.message)

    # setup the auth
    try:
        api = linode_api.Api(api_key)
        api.test_echo()
    except Exception, e:
        module.fail_json(msg = '%s' % e.value[0]['ERRORMESSAGE'])

    linodeServers(module, api, state, name, plan, distribution, datacenter, linode_id, 
                 payment_term, password, ssh_pub_key, swap, wait, wait_timeout)

# import module snippets
from ansible.module_utils.basic import *

main()
