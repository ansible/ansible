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
module: linode
short_description: Manage instances on the Linode Public Cloud
description:
     - Manage Linode Public Cloud instances and optionally wait for it to be 'running'.
version_added: "1.3"
options:
  state:
    description:
     - Indicate desired state of the resource
    choices: [ absent, active, deleted, present, restarted, started, stopped ]
    default: present
  api_key:
    description:
     - Linode API key
  name:
    description:
     - Name to give the instance (alphanumeric, dashes, underscore).
     - To keep sanity on the Linode Web Console, name is prepended with C(LinodeID_).
  displaygroup:
    description:
     - Add the instance to a Display Group in Linode Manager.
    version_added: "2.3"
  linode_id:
    description:
     - Unique ID of a linode server
    aliases: [ lid ]
  additional_disks:
    description:
      - List of dictionaries for creating additional disks that are added to the Linode configuration settings.
      - Dictionary takes Size, Label, Type. Size is in MB.
    version_added: "2.3"
  alert_bwin_enabled:
    description:
    - Set status of bandwidth in alerts.
    type: bool
    version_added: "2.3"
  alert_bwin_threshold:
    description:
    - Set threshold in MB of bandwidth in alerts.
    version_added: "2.3"
  alert_bwout_enabled:
    description:
    - Set status of bandwidth out alerts.
    type: bool
    version_added: "2.3"
  alert_bwout_threshold:
    description:
    - Set threshold in MB of bandwidth out alerts.
    version_added: "2.3"
  alert_bwquota_enabled:
    description:
    - Set status of bandwidth quota alerts as percentage of network transfer quota.
    type: bool
    version_added: "2.3"
  alert_bwquota_threshold:
    description:
    - Set threshold in MB of bandwidth quota alerts.
    version_added: "2.3"
  alert_cpu_enabled:
    description:
    - Set status of receiving CPU usage alerts.
    type: bool
    version_added: "2.3"
  alert_cpu_threshold:
    description:
    - Set percentage threshold for receiving CPU usage alerts. Each CPU core adds 100% to total.
    version_added: "2.3"
  alert_diskio_enabled:
    description:
    - Set status of receiving disk IO alerts.
    type: bool
    version_added: "2.3"
  alert_diskio_threshold:
    description:
    - Set threshold for average IO ops/sec over 2 hour period.
    version_added: "2.3"
  backupweeklyday:
    description:
    - Integer value for what day of the week to store weekly backups.
    version_added: "2.3"
  plan:
    description:
     - plan to use for the instance (Linode plan)
  payment_term:
    description:
     - payment term to use for the instance (payment term in months)
    default: 1
    choices: [ 1, 12, 24 ]
  password:
    description:
     - root password to apply to a new server (auto generated if missing)
  private_ip:
    description:
    - Add private IPv4 address when Linode is created.
    type: bool
    default: "no"
    version_added: "2.3"
  ssh_pub_key:
    description:
     - SSH public key applied to root user
  swap:
    description:
     - swap size in MB
    default: 512
  distribution:
    description:
     - distribution to use for the instance (Linode Distribution)
  datacenter:
    description:
     - datacenter to create an instance in (Linode Datacenter)
  kernel_id:
    description:
     - kernel to use for the instance (Linode Kernel)
    version_added: "2.4"
  wait:
    description:
     - wait for the instance to be in state C(running) before returning
    type: bool
    default: "no"
  wait_timeout:
    description:
     - how long before wait gives up, in seconds
    default: 300
  watchdog:
    description:
    - Set status of Lassie watchdog.
    type: bool
    default: "True"
    version_added: "2.2"
requirements:
    - python >= 2.6
    - linode-python
author:
- Vincent Viallet (@zbal)
notes:
  - C(LINODE_API_KEY) env variable can be used instead.
'''

EXAMPLES = '''
- name: Create a server with a private IP Address
  linode:
     module: linode
     api_key: 'longStringFromLinodeApi'
     name: linode-test1
     plan: 1
     datacenter: 2
     distribution: 99
     password: 'superSecureRootPassword'
     private_ip: yes
     ssh_pub_key: 'ssh-rsa qwerty'
     swap: 768
     wait: yes
     wait_timeout: 600
     state: present
  delegate_to: localhost

- name: Fully configure new server
  linode:
     api_key: 'longStringFromLinodeApi'
     name: linode-test1
     plan: 4
     datacenter: 2
     distribution: 99
     kernel_id: 138
     password: 'superSecureRootPassword'
     private_ip: yes
     ssh_pub_key: 'ssh-rsa qwerty'
     swap: 768
     wait: yes
     wait_timeout: 600
     state: present
     alert_bwquota_enabled: True
     alert_bwquota_threshold: 80
     alert_bwin_enabled: True
     alert_bwin_threshold: 10
     alert_cpu_enabled: True
     alert_cpu_threshold: 210
     alert_diskio_enabled: True
     alert_bwout_enabled: True
     alert_bwout_threshold: 10
     alert_diskio_enabled: True
     alert_diskio_threshold: 10000
     backupweeklyday: 1
     backupwindow: 2
     displaygroup: 'test'
     additional_disks:
      - {Label: 'disk1', Size: 2500, Type: 'raw'}
      - {Label: 'newdisk', Size: 2000}
     watchdog: True
  delegate_to: localhost

- name: Ensure a running server (create if missing)
  linode:
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
  delegate_to: localhost

- name: Delete a server
  linode:
     api_key: 'longStringFromLinodeApi'
     name: linode-test1
     linode_id: 12345678
     state: absent
  delegate_to: localhost

- name: Stop a server
  linode:
     api_key: 'longStringFromLinodeApi'
     name: linode-test1
     linode_id: 12345678
     state: stopped
  delegate_to: localhost

- name: Reboot a server
  linode:
     api_key: 'longStringFromLinodeApi'
     name: linode-test1
     linode_id: 12345678
     state: restarted
  delegate_to: localhost
'''

import os
import time

try:
    from linode import api as linode_api
    HAS_LINODE = True
except ImportError:
    HAS_LINODE = False

from ansible.module_utils.basic import AnsibleModule


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


def linodeServers(module, api, state, name,
                  displaygroup, plan, additional_disks, distribution,
                  datacenter, kernel_id, linode_id, payment_term, password,
                  private_ip, ssh_pub_key, swap, wait, wait_timeout, watchdog, **kwargs):
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
            for arg in (name, plan, distribution, datacenter):
                if not arg:
                    module.fail_json(msg='%s is required for %s state' % (arg, state))
            # Create linode entity
            new_server = True

            # Get size of all individually listed disks to subtract from Distribution disk
            used_disk_space = 0 if additional_disks is None else sum(disk['Size'] for disk in additional_disks)

            try:
                res = api.linode_create(DatacenterID=datacenter, PlanID=plan,
                                        PaymentTerm=payment_term)
                linode_id = res['LinodeID']
                # Update linode Label to match name
                api.linode_update(LinodeId=linode_id, Label='%s_%s' % (linode_id, name))
                # Update Linode with Ansible configuration options
                api.linode_update(LinodeId=linode_id, LPM_DISPLAYGROUP=displaygroup, WATCHDOG=watchdog, **kwargs)
                # Save server
                servers = api.linode_list(LinodeId=linode_id)
            except Exception as e:
                module.fail_json(msg='%s' % e.value[0]['ERRORMESSAGE'])

        # Add private IP to Linode
        if private_ip:
            try:
                res = api.linode_ip_addprivate(LinodeID=linode_id)
            except Exception as e:
                module.fail_json(msg='%s' % e.value[0]['ERRORMESSAGE'])

        if not disks:
            for arg in (name, linode_id, distribution):
                if not arg:
                    module.fail_json(msg='%s is required for %s state' % (arg, state))
            # Create disks (1 from distrib, 1 for SWAP)
            new_server = True
            try:
                if not password:
                    # Password is required on creation, if not provided generate one
                    password = randompass()
                if not swap:
                    swap = 512
                # Create data disk
                size = servers[0]['TOTALHD'] - used_disk_space - swap

                if ssh_pub_key:
                    res = api.linode_disk_createfromdistribution(
                        LinodeId=linode_id, DistributionID=distribution,
                        rootPass=password, rootSSHKey=ssh_pub_key,
                        Label='%s data disk (lid: %s)' % (name, linode_id),
                        Size=size)
                else:
                    res = api.linode_disk_createfromdistribution(
                        LinodeId=linode_id, DistributionID=distribution,
                        rootPass=password,
                        Label='%s data disk (lid: %s)' % (name, linode_id),
                        Size=size)
                jobs.append(res['JobID'])
                # Create SWAP disk
                res = api.linode_disk_create(LinodeId=linode_id, Type='swap',
                                             Label='%s swap disk (lid: %s)' % (name, linode_id),
                                             Size=swap)
                # Create individually listed disks at specified size
                if additional_disks:
                    for disk in additional_disks:
                        # If a disk Type is not passed in, default to ext4
                        if disk.get('Type') is None:
                            disk['Type'] = 'ext4'
                        res = api.linode_disk_create(LinodeID=linode_id, Label=disk['Label'], Size=disk['Size'], Type=disk['Type'])

                jobs.append(res['JobID'])
            except Exception as e:
                # TODO: destroy linode ?
                module.fail_json(msg='%s' % e.value[0]['ERRORMESSAGE'])

        if not configs:
            for arg in (name, linode_id, distribution):
                if not arg:
                    module.fail_json(msg='%s is required for %s state' % (arg, state))

            # Check architecture
            for distrib in api.avail_distributions():
                if distrib['DISTRIBUTIONID'] != distribution:
                    continue
                arch = '32'
                if distrib['IS64BIT']:
                    arch = '64'
                break

            # Get latest kernel matching arch if kernel_id is not specified
            if not kernel_id:
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
            except Exception as e:
                module.fail_json(msg='%s' % e.value[0]['ERRORMESSAGE'])

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
                module.fail_json(msg='Timeout waiting on %s (lid: %s)' % (server['LABEL'], server['LINODEID']))
            # Get a fresh copy of the server details
            server = api.linode_list(LinodeId=server['LINODEID'])[0]
            if server['STATUS'] == -2:
                module.fail_json(msg='%s (lid: %s) failed to boot' %
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
        if not linode_id:
            module.fail_json(msg='linode_id is required for stopped state')

        if not servers:
            module.fail_json(msg='Server (lid: %s) not found' % (linode_id))

        for server in servers:
            instance = getInstanceDetails(api, server)
            if server['STATUS'] != 2:
                try:
                    res = api.linode_shutdown(LinodeId=linode_id)
                except Exception as e:
                    module.fail_json(msg='%s' % e.value[0]['ERRORMESSAGE'])
                instance['status'] = 'Stopping'
                changed = True
            else:
                instance['status'] = 'Stopped'
            instances.append(instance)

    elif state in ('restarted'):
        if not linode_id:
            module.fail_json(msg='linode_id is required for restarted state')

        if not servers:
            module.fail_json(msg='Server (lid: %s) not found' % (linode_id))

        for server in servers:
            instance = getInstanceDetails(api, server)
            try:
                res = api.linode_reboot(LinodeId=server['LINODEID'])
            except Exception as e:
                module.fail_json(msg='%s' % e.value[0]['ERRORMESSAGE'])
            instance['status'] = 'Restarting'
            changed = True
            instances.append(instance)

    elif state in ('absent', 'deleted'):
        for server in servers:
            instance = getInstanceDetails(api, server)
            try:
                api.linode_delete(LinodeId=server['LINODEID'], skipChecks=True)
            except Exception as e:
                module.fail_json(msg='%s' % e.value[0]['ERRORMESSAGE'])
            instance['status'] = 'Deleting'
            changed = True
            instances.append(instance)

    # Ease parsing if only 1 instance
    if len(instances) == 1:
        module.exit_json(changed=changed, instance=instances[0])

    module.exit_json(changed=changed, instances=instances)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present',
                       choices=['absent', 'active', 'deleted', 'present', 'restarted', 'started', 'stopped']),
            api_key=dict(type='str', no_log=True),
            name=dict(type='str'),
            alert_bwin_enabled=dict(type='bool'),
            alert_bwin_threshold=dict(type='int'),
            alert_bwout_enabled=dict(type='bool'),
            alert_bwout_threshold=dict(type='int'),
            alert_bwquota_enabled=dict(type='bool'),
            alert_bwquota_threshold=dict(type='int'),
            alert_cpu_enabled=dict(type='bool'),
            alert_cpu_threshold=dict(type='int'),
            alert_diskio_enabled=dict(type='bool'),
            alert_diskio_threshold=dict(type='int'),
            backupsenabled=dict(type='int'),
            backupweeklyday=dict(type='int'),
            backupwindow=dict(type='int'),
            displaygroup=dict(type='str', default=''),
            plan=dict(type='int'),
            additional_disks=dict(type='list'),
            distribution=dict(type='int'),
            datacenter=dict(type='int'),
            kernel_id=dict(type='int'),
            linode_id=dict(type='int', aliases=['lid']),
            payment_term=dict(type='int', default=1, choices=[1, 12, 24]),
            password=dict(type='str', no_log=True),
            private_ip=dict(type='bool'),
            ssh_pub_key=dict(type='str'),
            swap=dict(type='int', default=512),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(default=300),
            watchdog=dict(type='bool', default=True),
        ),
    )

    if not HAS_LINODE:
        module.fail_json(msg='linode-python required for this module')

    state = module.params.get('state')
    api_key = module.params.get('api_key')
    name = module.params.get('name')
    alert_bwin_enabled = module.params.get('alert_bwin_enabled')
    alert_bwin_threshold = module.params.get('alert_bwin_threshold')
    alert_bwout_enabled = module.params.get('alert_bwout_enabled')
    alert_bwout_threshold = module.params.get('alert_bwout_threshold')
    alert_bwquota_enabled = module.params.get('alert_bwquota_enabled')
    alert_bwquota_threshold = module.params.get('alert_bwquota_threshold')
    alert_cpu_enabled = module.params.get('alert_cpu_enabled')
    alert_cpu_threshold = module.params.get('alert_cpu_threshold')
    alert_diskio_enabled = module.params.get('alert_diskio_enabled')
    alert_diskio_threshold = module.params.get('alert_diskio_threshold')
    backupsenabled = module.params.get('backupsenabled')
    backupweeklyday = module.params.get('backupweeklyday')
    backupwindow = module.params.get('backupwindow')
    displaygroup = module.params.get('displaygroup')
    plan = module.params.get('plan')
    additional_disks = module.params.get('additional_disks')
    distribution = module.params.get('distribution')
    datacenter = module.params.get('datacenter')
    kernel_id = module.params.get('kernel_id')
    linode_id = module.params.get('linode_id')
    payment_term = module.params.get('payment_term')
    password = module.params.get('password')
    private_ip = module.params.get('private_ip')
    ssh_pub_key = module.params.get('ssh_pub_key')
    swap = module.params.get('swap')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))
    watchdog = int(module.params.get('watchdog'))

    kwargs = dict()
    check_items = dict(
        alert_bwin_enabled=alert_bwin_enabled,
        alert_bwin_threshold=alert_bwin_threshold,
        alert_bwout_enabled=alert_bwout_enabled,
        alert_bwout_threshold=alert_bwout_threshold,
        alert_bwquota_enabled=alert_bwquota_enabled,
        alert_bwquota_threshold=alert_bwquota_threshold,
        alert_cpu_enabled=alert_cpu_enabled,
        alert_cpu_threshold=alert_cpu_threshold,
        alert_diskio_enabled=alert_diskio_enabled,
        alert_diskio_threshold=alert_diskio_threshold,
        backupweeklyday=backupweeklyday,
        backupwindow=backupwindow,
    )

    for key, value in check_items.items():
        if value is not None:
            kwargs[key] = value

    # Setup the api_key
    if not api_key:
        try:
            api_key = os.environ['LINODE_API_KEY']
        except KeyError as e:
            module.fail_json(msg='Unable to load %s' % e.message)

    # setup the auth
    try:
        api = linode_api.Api(api_key)
        api.test_echo()
    except Exception as e:
        module.fail_json(msg='%s' % e.value[0]['ERRORMESSAGE'])

    linodeServers(module, api, state, name,
                  displaygroup, plan,
                  additional_disks, distribution, datacenter, kernel_id, linode_id,
                  payment_term, password, private_ip, ssh_pub_key, swap, wait,
                  wait_timeout, watchdog, **kwargs)


if __name__ == '__main__':
    main()
