#!/usr/bin/python
# encoding: utf-8
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import json
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
  name_add_id:
    description:
    - prepend the linode ID to the name
    default: True
    type: bool
    version_added: "2.4"
  name_id_separator:
    description:
    - The separator to use when automatically adding an ID.
    default: '_'
    type: string
    version_added: "2.4"
  displaygroup:
    description:
     - Add the instance to a Display Group in Linode Manager
    default: null
    version_added: "2.3"
  linode_id:
    description:
     - Unique ID of a linode server
    aliases: [ 'lid' ]
    default: null
  additional_disks:
    description: >
      List of dictionaries for creating additional disks that are added to the Linode configuration settings.
      Dictionary takes Size, Label, Type. Size is in MB.
    default: null
    version_added: "2.3"
  alert_bwin_enabled:
    description:
    - Set status of bandwidth in alerts.
    default: null
    choices: [ "True", "False" ]
    version_added: "2.3"
  alert_bwin_threshold:
    description:
    - Set threshold in MB of bandwidth in alerts.
    default: null
    version_added: "2.3"
  alert_bwout_enabled:
    description:
    - Set status of bandwidth out alerts.
    default: null
    choices: [ "True", "False" ]
    version_added: "2.3"
  alert_bwout_threshold:
    description:
    - Set threshold in MB of bandwidth out alerts.
    default: null
    version_added: "2.3"
  alert_bwquota_enabled:
    description:
    - Set status of bandwidth quota alerts as percentage of network transfer quota.
    default: null
    choices: [ "True", "False" ]
    version_added: "2.3"
  alert_bwquota_threshold:
    description:
    - Set threshold in MB of bandwidth quota alerts.
    default: null
    version_added: "2.3"
  alert_cpu_enabled:
    description:
    - Set status of receiving CPU usage alerts.
    default: null
    choices: [ "True", "False" ]
    version_added: "2.3"
  alert_cpu_threshold:
    description:
    - Set percentage threshold for receiving CPU usage alerts. Each CPU core adds 100% to total.
    default: null
    version_added: "2.3"
  alert_diskio_enabled:
    description:
    - Set status of receiving disk IO alerts.
    default: null
    choices: [ "True", "False" ]
    version_added: "2.3"
  alert_diskio_threshold:
    description:
    - Set threshold for average IO ops/sec over 2 hour period.
    default: null
    version_added: "2.3"
  backupweeklyday:
    description:
    - Integer value for what day of the week to store weekly backups.
    default: null
    version_added: "2.3"
  plan:
    description:
     - plan to use for the instance (Linode plan)
    default: null
  payment_term:
    description:
     - payment term to use for the instance (payment term in months)
    default: 1
    choices: [1, 12, 24]
  password:
    description:
     - root password to apply to a new server (auto generated if missing)
    default: null
  private_ip:
    description:
    - Add private IPv4 address when Linode is created.
    default: "no"
    choices: [ "yes", "no" ]
    version_added: "2.3"
  ssh_pub_key:
    description:
     - SSH public key applied to root user
    default: null
  swap:
    description:
     - swap size in MB
    default: 512
  distribution:
    description:
     - distribution to use for the instance (Linode Distribution)
    default: null
  stackscript:
     - stackscript to run during first boot (customize distribution)
     default: null
     type: integer
  stackscript_responses:
     - user defined fields answering questions posed by the stackscript
     default: null
     type: dict
  private_dns_zone:
     - Linode DNS namespace where resource records should be created for new instances' private IP
     default: null
     type: string
  datacenter:
    description:
     - datacenter to create an instance in (Linode Datacenter)
    default: null
  kernel_id:
    description:
     - kernel to use for the instance (Linode Kernel)
    default: null
    version_added: "2.4"
  wait:
    description:
     - wait for the instance to be in state 'running' before returning
    default: "no"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
     - how long before wait gives up, in seconds
    default: 300
  watchdog:
    description:
    - Set status of Lassie watchdog.
    default: "True"
    choices: [ "True", "False" ]
    version_added: "2.2"
requirements:
    - "python >= 2.6"
    - "linode-python"
    - "pycurl"
author: "Vincent Viallet (@zbal)"
notes:
  - LINODE_API_KEY env variable can be used instead
'''

EXAMPLES = '''
# Create a server with a private IP Address
- local_action:
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

# Fully configure new server
- local_action:
     module: linode
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

# run a script during first boot and add DNS records for the new instances
- local_action:
     module: linode
     api_key: 'longStringFromLinodeApi'
     name: linode-test1
     plan: 1
     datacenter: 2
     distribution: 99
     ssh_pub_key: 'ssh-rsa qwerty'
     wait: yes
     state: present
     stackscript: 36655         # https://www.linode.com/stackscripts/view/36655
     stackscript_responses:
        ssuser: 'admin'
        sspassword: 'superSecureRootPassword'
        sspubkey: 'ssh-rsa qwerty'
     private_dns_zone: dc1.example.com.

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

import os
import time

try:
    import pycurl
    HAS_PYCURL = True
except ImportError:
    HAS_PYCURL = False

try:
    from linode import api as linode_api
    HAS_LINODE = True
except ImportError:
    HAS_LINODE = False

from ansible.module_utils.basic import AnsibleModule

def getDomainID(api, private_dns_zone):
    try:
        dns_zones
    except:
        dns_zones = api.domain_list()
        pass
    for zone in dns_zones:
        if zone['DOMAIN'] == private_dns_zone:
            domain_id = zone['DOMAINID']
            break
    return(domain_id)

def getAResourceRecords(api, domain_id):
    try:
        resource_records = api.domain_resource_list(DomainID=domain_id)
    except Exception as e:
        raise(e)
    private_resource_records = []
    for rr in resource_records:
        if rr['TYPE'] == "A":
            private_resource_records.append(rr)
    return(private_resource_records)

# delete any stale records, optionally preserving exactly one record matching rdata
def delAResourceRecords(api, domain_id, private_resource_records, rname, rdata=None):
    stale_resource_records = []
    preserved = False
    for rr in private_resource_records:
        if rr['NAME'] == rname:
            # ignore the current matching record if we didn't already select a
            # record for preservation
            if rdata and not preserved and rr['TARGET'] == rdata:
                preserved = True
                continue
            stale_resource_records.append({
                'TYPE': rr['TYPE'],
                'TARGET': rr['TARGET'],
                'RESOURCEID': rr['RESOURCEID'],
                'NAME': rr['NAME']
            })
    changed = False
    if stale_resource_records:
        for rr in stale_resource_records:
            try:
                delete_result = api.domain_resource_delete(
                                DomainID=domain_id,
                                ResourceID=rr['RESOURCEID']
                                )
                changed = True
            except Exception as e:
                raise(e)
    return { 'changed': changed }

def putAResourceRecords(api, domain_id, rname, rdata):
    try:
        create_result = api.domain_resource_create(
                        DomainID=domain_id,
                        Type="A",
                        Name=rname,
                        Target=rdata)
    except:
        pass
    try:
        update_result = api.domain_resource_update(
                        DomainID=domain_id,
                        ResourceID=create_result['ResourceID'],
                        Name=rname,
                        Target=rdata)
    except Exception as e:
        raise(e)

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
                'private': [],
                'disks': [],
                'configs': []}

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

    # populate disks and configs
    instance['disks'] = api.linode_disk_list(LinodeId=server['LINODEID'])
    instance['configs'] = api.linode_config_list(LinodeId=server['LINODEID'])

    return instance

def linodeServers(module, api, state, name, name_add_id, name_id_separator,
                  displaygroup, plan, additional_disks, distribution, stackscript,
                  stackscript_responses, datacenter, kernel_id, linode_id,
                  payment_term, password, private_ip, ssh_pub_key, swap, wait,
                  wait_timeout, watchdog, private_dns_zone, **kwargs):
    server = None
    instance = {}
    changed = False
    new_server = False
    servers = []
    private_interfaces = []
    public_interfaces = []
    jobs = []
    disk_size = 0
    dns_zones = []

    # See if we can match an existing server details with the provided linode_id
    if linode_id:
        # For the moment we only consider linode_id as criteria for match
        # Later we can use more (size, name, etc.) and update existing
        server = api.linode_list(LinodeId=linode_id)[0]
    else:
        servers = api.linode_list()
        for srv in servers:
            if srv['LABEL'] == name:
                server = srv
                linode_id = server['LINODEID']
                break

    private_resource_records = []
    if private_dns_zone:
        try:
            domain_id = getDomainID(api, private_dns_zone)
            private_resource_records = getAResourceRecords(api, domain_id)
        except Exception as e:
            raise(e)

    # Attempt to fetch details about an existing instance
    if server:
        instance = getInstanceDetails(api, server)

    # Act on the state
    if state in ('active', 'present', 'started'):
        # TODO: validate all the plan / distribution / datacenter are valid

        # Multi step process/validation:
        #  - need linode_id (entity)
        #  - need disk_id for linode_id - create disk from distrib
        #  - need config_id for linode_id - create config (need kernel)

        # Any create step triggers a job that need to be waited for.
        if not server:
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
                if name_add_id:
                    api.linode_update(LinodeId=linode_id, Label='%s%s%s' % (linode_id, name_id_separator, name))
                else:
                    api.linode_update(LinodeId=linode_id, Label=name)
                # Update Linode with Ansible configuration options
                api.linode_update(LinodeId=linode_id,
                        LPM_DISPLAYGROUP=displaygroup, WATCHDOG=watchdog, **kwargs)
                # Save server
                server = api.linode_list(LinodeId=linode_id)[0]
                instance = getInstanceDetails(api, server)
            except Exception as e:
                module.fail_json(msg = '%s' % e)

        if not instance['disks']:
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

                if stackscript:
                    # assign a random password if not user-defined
                    try:
                        stackscript_responses['sspassword']
                    except:
                        stackscript_responses['sspassword'] = randompass()
                        pass

                # Create data disk
                size = server['TOTALHD'] - used_disk_space - swap

                if ssh_pub_key and not stackscript:
                    res = api.linode_disk_createfromdistribution(
                        LinodeId=linode_id, DistributionID=distribution,
                        rootPass=password, rootSSHKey=ssh_pub_key,
                        Label='%s data disk (lid: %s)' % (name, linode_id),
                        Size=size)
                elif ssh_pub_key and stackscript:
                    res = api.linode_disk_createfromstackscript(
                        LinodeId=linode_id, StackScriptID=stackscript,
                        StackScriptUDFResponses=json.dumps(stackscript_responses),
                        DistributionID=distribution, rootPass=password,
                        rootSSHKey=ssh_pub_key, Label='%s data disk (lid: %s)' % (name, linode_id),
                        Size=size)
                elif stackscript:
                    res = api.linode_disk_createfromstackscript(
                        LinodeId=linode_id, StackScriptID=stackscript,
                        StackScriptUDFResponses=json.dumps(stackscript_responses),
                        DistributionID=distribution, rootPass=password,
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

                # freshen
                server = api.linode_list(LinodeId=linode_id)[0]
                instance = getInstanceDetails(api, server)

            except Exception as e:
                # TODO: destroy linode ?
                module.fail_json(msg = '%s' % e)

        if not instance['configs']:
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

            # exctract a list of disk IDs from the list of dicts describing existing disks
            disk_ids = []
            for disk in instance['disks']:
                # ¿Why are ext3 disks always unshifted on the stack (i.e., inserted)?
                if disk['TYPE'] == 'ext3':
                    disk_ids.insert(0, str(disk['DISKID']))
                    continue
                disk_ids.append(str(disk['DISKID']))
            # Trick to get the 9 items in the list
            # ¿Why only the first nine items?
            while len(disk_ids) < 9:
                disk_ids.append('')
            disks = ','.join(disk_ids)

            # Create config
            new_server = True
            try:
                api.linode_config_create(LinodeId=linode_id, KernelId=kernel_id,
                                         Disklist=disks, Label='%s config' % name)
            except Exception as e:
                module.fail_json(msg = '%s' % e)

        # add private IP if requested and the instance exists and a private IP is not already added
        if private_ip and instance and not instance['private']:
            try:
                res = api.linode_ip_addprivate(LinodeID=linode_id)
                # freshen
                instance = getInstanceDetails(api, server)
            except Exception as e:
                module.fail_json(msg = '%s' % e)

        if private_dns_zone:
            try: # delete stale records and create a new one for the private IP
                delAResourceRecords(api, domain_id, private_resource_records,
                                    rname=name, rdata=instance['private'][0]['ipv4'])
                putAResourceRecords(api, domain_id,
                                    rname=name, rdata=instance['private'][0]['ipv4'])
            except Exception as e:
                raise(e)

        # Start / Ensure servers are running
        # Ensure existing servers are up and running, boot if necessary
        #  1: Running
        if server['STATUS'] != 1:
            # Get a fresh copy of the server details
            server = api.linode_list(LinodeId=linode_id)[0]
            res = api.linode_boot(LinodeId=linode_id)
            jobs.append(res['JobID'])
            changed = True

        # wait here until the instances are up
        wait_timeout = time.time() + wait_timeout
        while wait and wait_timeout > time.time():
            # refresh the server details
            server = api.linode_list(LinodeId=linode_id)[0]
            # status:
            #  -2: Boot failed
            #  1: Running
            if server['STATUS'] in (-2, 1):
                break
            time.sleep(5)
        if wait and wait_timeout <= time.time():
            # waiting took too long
            module.fail_json(msg = 'Timeout waiting on %s (lid: %s)' %
                             (server['LABEL'], linode_id))
        # Get a fresh copy of the server details
        server = api.linode_list(LinodeId=linode_id)[0]
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

    elif state in ('stopped'):
        if not linode_id:
            module.fail_json(msg='linode_id is required for stopped state')

        if not server:
            module.fail_json(msg = 'Server (linode_id: %s) does not exist' % (linode_id))

        # unless stopped
        if server['STATUS'] != 2:
            try:
                res = api.linode_shutdown(LinodeId=linode_id)
            except Exception as e:
                module.fail_json(msg = '%s' % e)

            instance['status'] = 'Stopping'
            changed = True

        else:
            instance['status'] = 'Stopped'

    elif state in ('restarted'):
        if not linode_id:
            module.fail_json(msg='linode_id is required for restarted state')

        if not server:
            module.fail_json(msg = 'Server (linode_id: %s) does not exist' % (linode_id))

        try:
            res = api.linode_reboot(LinodeId=linode_id)
        except Exception as e:
            module.fail_json(msg = '%s' % e)

        instance['status'] = 'Restarting'
        changed = True

    elif state in ('absent', 'deleted'):
        if server:
            try:
                api.linode_delete(LinodeId=server['LINODEID'], skipChecks=True)
                instance['status'] = 'Deleting'
                changed = True
            except Exception as e:
                module.fail_json(msg = '%s' % e)
        else:
            instance['status'] = 'Deleted'
            changed = False

        if private_dns_zone:
            try:
                result = delAResourceRecords(api, domain_id, private_resource_records, rname=name)
            except Exception as e:
                raise(e)

        if result['changed']:
            changed = True

    module.exit_json(changed=changed, instance=instance)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            state = dict(default='present', choices=['active', 'present', 'started',
                                                     'deleted', 'absent', 'stopped',
                                                     'restarted']),
            api_key = dict(no_log=True),
            name = dict(type='str'),
            name_add_id = dict(type='bool', default=True),
            name_id_separator = dict(type='str', default='_'),
            alert_bwin_enabled = dict(type='bool', default=None),
            alert_bwin_threshold = dict(type='int', default=None),
            alert_bwout_enabled = dict(type='bool', default=None),
            alert_bwout_threshold = dict(type='int', default=None),
            alert_bwquota_enabled = dict(type='bool', default=None),
            alert_bwquota_threshold = dict(type='int', default=None),
            alert_cpu_enabled = dict(type='bool', default=None),
            alert_cpu_threshold = dict(type='int', default=None),
            alert_diskio_enabled = dict(type='bool', default=None),
            alert_diskio_threshold = dict(type='int', default=None),
            backupsenabled = dict(type='int', default=None),
            backupweeklyday = dict(type='int', default=None),
            backupwindow = dict(type='int', default=None),
            displaygroup = dict(type='str', default=''),
            plan = dict(type='int'),
            additional_disks= dict(type='list'),
            distribution = dict(type='int'),
            stackscript = dict(type='int'),
            stackscript_responses = dict(type='dict', no_log=True),
            datacenter = dict(type='int'),
            kernel_id = dict(type='int'),
            linode_id = dict(type='int', aliases=['lid']),
            payment_term = dict(type='int', default=1, choices=[1, 12, 24]),
            password = dict(type='str', no_log=True),
            private_ip = dict(type='bool'),
            ssh_pub_key = dict(type='str'),
            swap = dict(type='int', default=512),
            wait = dict(type='bool', default=True),
            wait_timeout = dict(default=300),
            watchdog = dict(type='bool', default=True),
            private_dns_zone = dict(type='str', default=None),
        )
    )

    if not HAS_PYCURL:
        module.fail_json(msg='pycurl required for this module')
    if not HAS_LINODE:
        module.fail_json(msg='linode-python required for this module')

    state = module.params.get('state')
    api_key = module.params.get('api_key')
    name = module.params.get('name')
    name_add_id = module.params.get('name_add_id')
    name_id_separator = module.params.get('name_id_separator')
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
    stackscript = module.params.get('stackscript')
    stackscript_responses = module.params.get('stackscript_responses')
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
    private_dns_zone = str(module.params.get('private_dns_zone'))

    kwargs = {}
    check_items = {'alert_bwin_enabled': alert_bwin_enabled, 'alert_bwin_threshold': alert_bwin_threshold,
                    'alert_bwout_enabled': alert_bwout_enabled, 'alert_bwout_threshold': alert_bwout_threshold,
                    'alert_bwquota_enabled': alert_bwquota_enabled, 'alert_bwquota_threshold': alert_bwquota_threshold,
                    'alert_cpu_enabled': alert_cpu_enabled, 'alert_cpu_threshold': alert_cpu_threshold,
                    'alert_diskio_enabled': alert_diskio_enabled, 'alert_diskio_threshold': alert_diskio_threshold,
                    'backupweeklyday': backupweeklyday, 'backupwindow': backupwindow}

    for key, value in check_items.items():
        if value is not None:
            kwargs[key] = value

    # Setup the api_key
    if not api_key:
        try:
            api_key = os.environ['LINODE_API_KEY']
        except KeyError as e:
            module.fail_json(msg = 'Unable to load %s' % e.message)

    # setup the auth
    try:
        api = linode_api.Api(api_key)
        api.test_echo()
    except Exception as e:
        module.fail_json(msg = '%s' % e)

    linodeServers(module, api, state, name, name_add_id, name_id_separator,
            displaygroup, plan, additional_disks, distribution, stackscript,
            stackscript_responses, datacenter, kernel_id, linode_id,
            payment_term, password, private_ip, ssh_pub_key, swap, wait,
            wait_timeout, watchdog, private_dns_zone, **kwargs)


if __name__ == '__main__':
    main()
