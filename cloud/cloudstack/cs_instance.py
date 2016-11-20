#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cs_instance
short_description: Manages instances and virtual machines on Apache CloudStack based clouds.
description:
    - Deploy, start, update, scale, restart, restore, stop and destroy instances.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Host name of the instance. C(name) can only contain ASCII letters.
      - Name will be generated (UUID) by CloudStack if not specified and can not be changed afterwards.
      - Either C(name) or C(display_name) is required.
    required: false
    default: null
  display_name:
    description:
      - Custom display name of the instances.
      - Display name will be set to C(name) if not specified.
      - Either C(name) or C(display_name) is required.
    required: false
    default: null
  group:
    description:
      - Group in where the new instance should be in.
    required: false
    default: null
  state:
    description:
      - State of the instance.
    required: false
    default: 'present'
    choices: [ 'deployed', 'started', 'stopped', 'restarted', 'restored', 'destroyed', 'expunged', 'present', 'absent' ]
  service_offering:
    description:
      - Name or id of the service offering of the new instance.
      - If not set, first found service offering is used.
    required: false
    default: null
  cpu:
    description:
      - The number of CPUs to allocate to the instance, used with custom service offerings
    required: false
    default: null
  cpu_speed:
    description:
      - The clock speed/shares allocated to the instance, used with custom service offerings
    required: false
    default: null
  memory:
    description:
      - The memory allocated to the instance, used with custom service offerings
    required: false
    default: null
  template:
    description:
      - Name or id of the template to be used for creating the new instance.
      - Required when using C(state=present).
      - Mutually exclusive with C(ISO) option.
    required: false
    default: null
  iso:
    description:
      - Name or id of the ISO to be used for creating the new instance.
      - Required when using C(state=present).
      - Mutually exclusive with C(template) option.
    required: false
    default: null
  template_filter:
    description:
      - Name of the filter used to search for the template or iso.
      - Used for params C(iso) or C(template) on C(state=present).
    required: false
    default: 'executable'
    choices: [ 'featured', 'self', 'selfexecutable', 'sharedexecutable', 'executable', 'community' ]
    aliases: [ 'iso_filter' ]
    version_added: '2.1'
  hypervisor:
    description:
      - Name the hypervisor to be used for creating the new instance.
      - Relevant when using C(state=present), but only considered if not set on ISO/template.
      - If not set or found on ISO/template, first found hypervisor will be used.
    required: false
    default: null
    choices: [ 'KVM', 'VMware', 'BareMetal', 'XenServer', 'LXC', 'HyperV', 'UCS', 'OVM' ]
  keyboard:
    description:
      - Keyboard device type for the instance.
    required: false
    default: null
    choices: [ 'de', 'de-ch', 'es', 'fi', 'fr', 'fr-be', 'fr-ch', 'is', 'it', 'jp', 'nl-be', 'no', 'pt', 'uk', 'us' ]
  networks:
    description:
      - List of networks to use for the new instance.
    required: false
    default: []
    aliases: [ 'network' ]
  ip_address:
    description:
      - IPv4 address for default instance's network during creation.
    required: false
    default: null
  ip6_address:
    description:
      - IPv6 address for default instance's network.
    required: false
    default: null
  ip_to_networks:
    description:
      - "List of mappings in the form {'network': NetworkName, 'ip': 1.2.3.4}"
      - Mutually exclusive with C(networks) option.
    required: false
    default: null
    aliases: [ 'ip_to_network' ]
  disk_offering:
    description:
      - Name of the disk offering to be used.
    required: false
    default: null
  disk_size:
    description:
      - Disk size in GByte required if deploying instance from ISO.
    required: false
    default: null
  root_disk_size:
    description:
      - Root disk size in GByte required if deploying instance with KVM hypervisor and want resize the root disk size at startup (need CloudStack >= 4.4, cloud-initramfs-growroot installed and enabled in the template)
    required: false
    default: null
  security_groups:
    description:
      - List of security groups the instance to be applied to.
    required: false
    default: null
    aliases: [ 'security_group' ]
  domain:
    description:
      - Domain the instance is related to.
    required: false
    default: null
  account:
    description:
      - Account the instance is related to.
    required: false
    default: null
  project:
    description:
      - Name of the project the instance to be deployed in.
    required: false
    default: null
  zone:
    description:
      - Name of the zone in which the instance shoud be deployed.
      - If not set, default zone is used.
    required: false
    default: null
  ssh_key:
    description:
      - Name of the SSH key to be deployed on the new instance.
    required: false
    default: null
  affinity_groups:
    description:
      - Affinity groups names to be applied to the new instance.
    required: false
    default: []
    aliases: [ 'affinity_group' ]
  user_data:
    description:
      - Optional data (ASCII) that can be sent to the instance upon a successful deployment.
      - The data will be automatically base64 encoded.
      - Consider switching to HTTP_POST by using C(CLOUDSTACK_METHOD=post) to increase the HTTP_GET size limit of 2KB to 32 KB.
    required: false
    default: null
  vpc:
    description:
      - Name of the VPC.
    required: false
    default: null
    version_added: "2.3"
  force:
    description:
      - Force stop/start the instance if required to apply changes, otherwise a running instance will not be changed.
    required: false
    default: false
  tags:
    description:
      - List of tags. Tags are a list of dictionaries having keys C(key) and C(value).
      - "If you want to delete all tags, set a empty list e.g. C(tags: [])."
    required: false
    default: null
    aliases: [ 'tag' ]
  poll_async:
    description:
      - Poll async jobs until job has finished.
    required: false
    default: true
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Create a instance from an ISO
# NOTE: Names of offerings and ISOs depending on the CloudStack configuration.
- local_action:
    module: cs_instance
    name: web-vm-1
    iso: Linux Debian 7 64-bit
    hypervisor: VMware
    project: Integration
    zone: ch-zrh-ix-01
    service_offering: 1cpu_1gb
    disk_offering: PerfPlus Storage
    disk_size: 20
    networks:
      - Server Integration
      - Sync Integration
      - Storage Integration

# For changing a running instance, use the 'force' parameter
- local_action:
    module: cs_instance
    name: web-vm-1
    display_name: web-vm-01.example.com
    iso: Linux Debian 7 64-bit
    service_offering: 2cpu_2gb
    force: yes

# Create or update a instance on Exoscale's public cloud using display_name.
# Note: user_data can be used to kickstart the instance using cloud-init yaml config.
- local_action:
    module: cs_instance
    display_name: web-vm-1
    template: Linux Debian 7 64-bit
    service_offering: Tiny
    ssh_key: john@example.com
    tags:
      - { key: admin, value: john }
      - { key: foo,   value: bar }
    user_data: |
        #cloud-config
        packages:
          - nginx

# Create an instance with multiple interfaces specifying the IP addresses
- local_action:
    module: cs_instance
    name: web-vm-1
    template: Linux Debian 7 64-bit
    service_offering: Tiny
    ip_to_networks:
      - {'network': NetworkA, 'ip': '10.1.1.1'}
      - {'network': NetworkB, 'ip': '192.0.2.1'}

# Ensure an instance is stopped
- local_action: cs_instance name=web-vm-1 state=stopped

# Ensure an instance is running
- local_action: cs_instance name=web-vm-1 state=started

# Remove an instance
- local_action: cs_instance name=web-vm-1 state=absent
'''

RETURN = '''
---
id:
  description: UUID of the instance.
  returned: success
  type: string
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: Name of the instance.
  returned: success
  type: string
  sample: web-01
display_name:
  description: Display name of the instance.
  returned: success
  type: string
  sample: web-01
group:
  description: Group name of the instance is related.
  returned: success
  type: string
  sample: web
created:
  description: Date of the instance was created.
  returned: success
  type: string
  sample: 2014-12-01T14:57:57+0100
password_enabled:
  description: True if password setting is enabled.
  returned: success
  type: boolean
  sample: true
password:
  description: The password of the instance if exists.
  returned: success
  type: string
  sample: Ge2oe7Do
ssh_key:
  description: Name of SSH key deployed to instance.
  returned: success
  type: string
  sample: key@work
domain:
  description: Domain the instance is related to.
  returned: success
  type: string
  sample: example domain
account:
  description: Account the instance is related to.
  returned: success
  type: string
  sample: example account
project:
  description: Name of project the instance is related to.
  returned: success
  type: string
  sample: Production
default_ip:
  description: Default IP address of the instance.
  returned: success
  type: string
  sample: 10.23.37.42
public_ip:
  description: Public IP address with instance via static NAT rule.
  returned: success
  type: string
  sample: 1.2.3.4
iso:
  description: Name of ISO the instance was deployed with.
  returned: success
  type: string
  sample: Debian-8-64bit
template:
  description: Name of template the instance was deployed with.
  returned: success
  type: string
  sample: Debian-8-64bit
service_offering:
  description: Name of the service offering the instance has.
  returned: success
  type: string
  sample: 2cpu_2gb
zone:
  description: Name of zone the instance is in.
  returned: success
  type: string
  sample: ch-gva-2
state:
  description: State of the instance.
  returned: success
  type: string
  sample: Running
security_groups:
  description: Security groups the instance is in.
  returned: success
  type: list
  sample: '[ "default" ]'
affinity_groups:
  description: Affinity groups the instance is in.
  returned: success
  type: list
  sample: '[ "webservers" ]'
tags:
  description: List of resource tags associated with the instance.
  returned: success
  type: dict
  sample: '[ { "key": "foo", "value": "bar" } ]'
hypervisor:
  description: Hypervisor related to this instance.
  returned: success
  type: string
  sample: KVM
instance_name:
  description: Internal name of the instance (ROOT admin only).
  returned: success
  type: string
  sample: i-44-3992-VM
'''

import base64

# import cloudstack common
from ansible.module_utils.cloudstack import *


class AnsibleCloudStackInstance(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackInstance, self).__init__(module)
        self.returns = {
            'group':                'group',
            'hypervisor':           'hypervisor',
            'instancename':         'instance_name',
            'publicip':             'public_ip',
            'passwordenabled':      'password_enabled',
            'password':             'password',
            'serviceofferingname':  'service_offering',
            'isoname':              'iso',
            'templatename':         'template',
            'keypair':              'ssh_key',
        }
        self.instance = None
        self.template = None
        self.iso = None


    def get_service_offering_id(self):
        service_offering = self.module.params.get('service_offering')

        service_offerings = self.cs.listServiceOfferings()
        if service_offerings:
            if not service_offering:
                return service_offerings['serviceoffering'][0]['id']

            for s in service_offerings['serviceoffering']:
                if service_offering in [ s['name'], s['id'] ]:
                    return s['id']
        self.module.fail_json(msg="Service offering '%s' not found" % service_offering)


    def get_template_or_iso(self, key=None):
        template = self.module.params.get('template')
        iso = self.module.params.get('iso')

        if not template and not iso:
            return None

        args                = {}
        args['account']     = self.get_account(key='name')
        args['domainid']    = self.get_domain(key='id')
        args['projectid']   = self.get_project(key='id')
        args['zoneid']      = self.get_zone(key='id')
        args['isrecursive'] = True

        if template:
            if self.template:
                return self._get_by_key(key, self.template)

            args['templatefilter'] = self.module.params.get('template_filter')
            templates = self.cs.listTemplates(**args)
            if templates:
                for t in templates['template']:
                    if template in [ t['displaytext'], t['name'], t['id'] ]:
                        self.template = t
                        return self._get_by_key(key, self.template)
            self.module.fail_json(msg="Template '%s' not found" % template)

        elif iso:
            if self.iso:
                return self._get_by_key(key, self.iso)
            args['isofilter'] = self.module.params.get('template_filter')
            isos = self.cs.listIsos(**args)
            if isos:
                for i in isos['iso']:
                    if iso in [ i['displaytext'], i['name'], i['id'] ]:
                        self.iso = i
                        return self._get_by_key(key, self.iso)
            self.module.fail_json(msg="ISO '%s' not found" % iso)


    def get_disk_offering_id(self):
        disk_offering = self.module.params.get('disk_offering')

        if not disk_offering:
            return None

        disk_offerings = self.cs.listDiskOfferings()
        if disk_offerings:
            for d in disk_offerings['diskoffering']:
                if disk_offering in [ d['displaytext'], d['name'], d['id'] ]:
                    return d['id']
        self.module.fail_json(msg="Disk offering '%s' not found" % disk_offering)


    def get_instance(self):
        instance = self.instance
        if not instance:
            instance_name = self.get_or_fallback('name', 'display_name')
            vpc_id = self.get_vpc(key='id')
            args = {
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'projectid': self.get_project(key='id'),
                'vpcid': vpc_id,
            }
            # Do not pass zoneid, as the instance name must be unique across zones.
            instances = self.cs.listVirtualMachines(**args)
            if instances:
                for v in instances['virtualmachine']:
                    # Due the limitation of the API, there is no easy way (yet) to get only those VMs
                    # not belonging to a VPC.
                    if not vpc_id and self.is_vm_in_vpc(vm=v):
                        continue
                    if instance_name.lower() in [ v['name'].lower(), v['displayname'].lower(), v['id'] ]:
                        self.instance = v
                        break
        return self.instance


    def get_iptonetwork_mappings(self):
        network_mappings = self.module.params.get('ip_to_networks')
        if network_mappings is None:
            return

        if network_mappings and self.module.params.get('networks'):
            self.module.fail_json(msg="networks and ip_to_networks are mutually exclusive.")

        network_names = [n['network'] for n in network_mappings]
        ids = self.get_network_ids(network_names)
        res = []
        for i, data in enumerate(network_mappings):
            res.append({'networkid': ids[i], 'ip': data['ip']})
        return res


    def security_groups_has_changed(self):
        security_groups = self.module.params.get('security_groups')
        if security_groups is None:
            return False

        security_groups = [s.lower() for s in security_groups]
        instance_security_groups = self.instance.get('securitygroup',[])

        instance_security_group_names = []
        for instance_security_group in instance_security_groups:
            if instance_security_group['name'].lower() not in security_groups:
                return True
            else:
                instance_security_group_names.append(instance_security_group['name'].lower())

        for security_group in security_groups:
            if security_group not in instance_security_group_names:
                return True
        return False


    def get_network_ids(self, network_names=None):
        if network_names is None:
            network_names = self.module.params.get('networks')

        if not network_names:
            return None

        args = {
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            'zoneid': self.get_zone(key='id'),
            'vpcid': self.get_vpc(key='id'),
        }
        networks = self.cs.listNetworks(**args)
        if not networks:
            self.module.fail_json(msg="No networks available")

        network_ids = []
        network_displaytexts = []
        for network_name in network_names:
            for n in networks['network']:
                if network_name in [ n['displaytext'], n['name'], n['id'] ]:
                    network_ids.append(n['id'])
                    network_displaytexts.append(n['name'])
                    break

        if len(network_ids) != len(network_names):
            self.module.fail_json(msg="Could not find all networks, networks list found: %s" % network_displaytexts)

        return network_ids


    def present_instance(self, start_vm=True):
        instance = self.get_instance()

        if not instance:
            instance = self.deploy_instance(start_vm=start_vm)
        else:
            instance = self.recover_instance(instance=instance)
            instance = self.update_instance(instance=instance, start_vm=start_vm)

        # In check mode, we do not necessarely have an instance
        if instance:
            instance = self.ensure_tags(resource=instance, resource_type='UserVm')
            # refresh instance data
            self.instance = instance

        return instance


    def get_user_data(self):
        user_data = self.module.params.get('user_data')
        if user_data is not None:
            user_data = base64.b64encode(str(user_data))
        return user_data


    def get_details(self):
        res = None
        cpu = self.module.params.get('cpu')
        cpu_speed = self.module.params.get('cpu_speed')
        memory = self.module.params.get('memory')
        if all([cpu, cpu_speed, memory]):
            res = [{
                'cpuNumber': cpu,
                'cpuSpeed': cpu_speed,
                'memory': memory,
            }]
        return res


    def deploy_instance(self, start_vm=True):
        self.result['changed'] = True
        networkids = self.get_network_ids()
        if networkids is not None:
            networkids = ','.join(networkids)

        args                        = {}
        args['templateid']          = self.get_template_or_iso(key='id')
        if not args['templateid']:
            self.module.fail_json(msg="Template or ISO is required.")

        args['zoneid']              = self.get_zone(key='id')
        args['serviceofferingid']   = self.get_service_offering_id()
        args['account']             = self.get_account(key='name')
        args['domainid']            = self.get_domain(key='id')
        args['projectid']           = self.get_project(key='id')
        args['diskofferingid']      = self.get_disk_offering_id()
        args['networkids']          = networkids
        args['iptonetworklist']     = self.get_iptonetwork_mappings()
        args['userdata']            = self.get_user_data()
        args['keyboard']            = self.module.params.get('keyboard')
        args['ipaddress']           = self.module.params.get('ip_address')
        args['ip6address']          = self.module.params.get('ip6_address')
        args['name']                = self.module.params.get('name')
        args['displayname']         = self.get_or_fallback('display_name', 'name')
        args['group']               = self.module.params.get('group')
        args['keypair']             = self.module.params.get('ssh_key')
        args['size']                = self.module.params.get('disk_size')
        args['startvm']             = start_vm
        args['rootdisksize']        = self.module.params.get('root_disk_size')
        args['affinitygroupnames']  = ','.join(self.module.params.get('affinity_groups'))
        args['details']             = self.get_details()

        security_groups = self.module.params.get('security_groups')
        if security_groups is not None:
            args['securitygroupnames']  = ','.join(security_groups)

        template_iso = self.get_template_or_iso()
        if 'hypervisor' not in template_iso:
            args['hypervisor'] = self.get_hypervisor()

        instance = None
        if not self.module.check_mode:
            instance = self.cs.deployVirtualMachine(**args)

            if 'errortext' in instance:
                self.module.fail_json(msg="Failed: '%s'" % instance['errortext'])

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                instance = self.poll_job(instance, 'virtualmachine')
        return instance


    def update_instance(self, instance, start_vm=True):
        # Service offering data
        args_service_offering = {}
        args_service_offering['id'] = instance['id']
        if self.module.params.get('service_offering'):
            args_service_offering['serviceofferingid'] = self.get_service_offering_id()
        service_offering_changed = self.has_changed(args_service_offering, instance)

        # Instance data
        args_instance_update = {}
        args_instance_update['id'] = instance['id']
        args_instance_update['userdata'] = self.get_user_data()
        args_instance_update['ostypeid'] = self.get_os_type(key='id')
        if self.module.params.get('group'):
            args_instance_update['group'] = self.module.params.get('group')
        if self.module.params.get('display_name'):
            args_instance_update['displayname'] = self.module.params.get('display_name')
        instance_changed = self.has_changed(args_instance_update, instance)

        # SSH key data
        args_ssh_key = {}
        args_ssh_key['id'] = instance['id']
        args_ssh_key['projectid'] = self.get_project(key='id')
        if self.module.params.get('ssh_key'):
            args_ssh_key['keypair'] = self.module.params.get('ssh_key')
        ssh_key_changed = self.has_changed(args_ssh_key, instance)

        security_groups_changed = self.security_groups_has_changed()

        changed = [
            service_offering_changed,
            instance_changed,
            security_groups_changed,
            ssh_key_changed,
        ]

        if True in changed:
            force = self.module.params.get('force')
            instance_state = instance['state'].lower()
            if instance_state == 'stopped' or force:
                self.result['changed'] = True
                if not self.module.check_mode:

                    # Ensure VM has stopped
                    instance = self.stop_instance()
                    instance = self.poll_job(instance, 'virtualmachine')
                    self.instance = instance

                    # Change service offering
                    if service_offering_changed:
                        res = self.cs.changeServiceForVirtualMachine(**args_service_offering)
                        if 'errortext' in res:
                            self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                        instance = res['virtualmachine']
                        self.instance = instance

                    # Update VM
                    if instance_changed or security_groups_changed:
                        if security_groups_changed:
                            args_instance_update['securitygroupnames'] = ','.join(self.module.params.get('security_groups'))
                        res = self.cs.updateVirtualMachine(**args_instance_update)
                        if 'errortext' in res:
                            self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                        instance = res['virtualmachine']
                        self.instance = instance

                    # Reset SSH key
                    if ssh_key_changed:
                        instance = self.cs.resetSSHKeyForVirtualMachine(**args_ssh_key)
                        if 'errortext' in instance:
                            self.module.fail_json(msg="Failed: '%s'" % instance['errortext'])

                        instance = self.poll_job(instance, 'virtualmachine')
                        self.instance = instance

                    # Start VM again if it was running before
                    if instance_state == 'running' and start_vm:
                        instance = self.start_instance()
        return instance


    def recover_instance(self, instance):
        if instance['state'].lower() in [ 'destroying', 'destroyed' ]:
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.cs.recoverVirtualMachine(id=instance['id'])
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                instance = res['virtualmachine']
        return instance


    def absent_instance(self):
        instance = self.get_instance()
        if instance:
            if instance['state'].lower() not in ['expunging', 'destroying', 'destroyed']:
                self.result['changed'] = True
                if not self.module.check_mode:
                    res = self.cs.destroyVirtualMachine(id=instance['id'])

                    if 'errortext' in res:
                        self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

                    poll_async = self.module.params.get('poll_async')
                    if poll_async:
                        instance = self.poll_job(res, 'virtualmachine')
        return instance


    def expunge_instance(self):
        instance = self.get_instance()
        if instance:
            res = {}
            if instance['state'].lower() in [ 'destroying', 'destroyed' ]:
                self.result['changed'] = True
                if not self.module.check_mode:
                    res = self.cs.destroyVirtualMachine(id=instance['id'], expunge=True)

            elif instance['state'].lower() not in [ 'expunging' ]:
                self.result['changed'] = True
                if not self.module.check_mode:
                    res = self.cs.destroyVirtualMachine(id=instance['id'], expunge=True)

            if res and 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                res = self.poll_job(res, 'virtualmachine')
        return instance


    def stop_instance(self):
        instance = self.get_instance()
        # in check mode intance may not be instanciated
        if instance:
            if instance['state'].lower() in ['stopping', 'stopped']:
                return instance

            if instance['state'].lower() in ['starting', 'running']:
                self.result['changed'] = True
                if not self.module.check_mode:
                    instance = self.cs.stopVirtualMachine(id=instance['id'])

                    if 'errortext' in instance:
                        self.module.fail_json(msg="Failed: '%s'" % instance['errortext'])

                    poll_async = self.module.params.get('poll_async')
                    if poll_async:
                        instance = self.poll_job(instance, 'virtualmachine')
        return instance


    def start_instance(self):
        instance = self.get_instance()
        # in check mode intance may not be instanciated
        if instance:
            if instance['state'].lower() in ['starting', 'running']:
                return instance

            if instance['state'].lower() in ['stopped', 'stopping']:
                self.result['changed'] = True
                if not self.module.check_mode:
                    instance = self.cs.startVirtualMachine(id=instance['id'])

                    if 'errortext' in instance:
                        self.module.fail_json(msg="Failed: '%s'" % instance['errortext'])

                    poll_async = self.module.params.get('poll_async')
                    if poll_async:
                        instance = self.poll_job(instance, 'virtualmachine')
        return instance


    def restart_instance(self):
        instance = self.get_instance()
        # in check mode intance may not be instanciated
        if instance:
            if instance['state'].lower() in [ 'running', 'starting' ]:
                self.result['changed'] = True
                if not self.module.check_mode:
                    instance = self.cs.rebootVirtualMachine(id=instance['id'])

                    if 'errortext' in instance:
                        self.module.fail_json(msg="Failed: '%s'" % instance['errortext'])

                    poll_async = self.module.params.get('poll_async')
                    if poll_async:
                        instance = self.poll_job(instance, 'virtualmachine')

            elif instance['state'].lower() in [ 'stopping', 'stopped' ]:
                instance = self.start_instance()
        return instance


    def restore_instance(self):
        instance = self.get_instance()
        self.result['changed'] = True
        # in check mode intance may not be instanciated
        if instance:
            args = {}
            args['templateid'] = self.get_template_or_iso(key='id')
            args['virtualmachineid'] = instance['id']
            res = self.cs.restoreVirtualMachine(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                instance = self.poll_job(res, 'virtualmachine')
        return instance


    def get_result(self, instance):
        super(AnsibleCloudStackInstance, self).get_result(instance)
        if instance:
            if 'securitygroup' in instance:
                security_groups = []
                for securitygroup in instance['securitygroup']:
                    security_groups.append(securitygroup['name'])
                self.result['security_groups'] = security_groups
            if 'affinitygroup' in instance:
                affinity_groups = []
                for affinitygroup in instance['affinitygroup']:
                    affinity_groups.append(affinitygroup['name'])
                self.result['affinity_groups'] = affinity_groups
            if 'nic' in instance:
                for nic in instance['nic']:
                    if nic['isdefault'] and 'ipaddress' in nic:
                        self.result['default_ip'] = nic['ipaddress']
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name = dict(default=None),
        display_name = dict(default=None),
        group = dict(default=None),
        state = dict(choices=['present', 'deployed', 'started', 'stopped', 'restarted', 'restored', 'absent', 'destroyed', 'expunged'], default='present'),
        service_offering = dict(default=None),
        cpu = dict(default=None, type='int'),
        cpu_speed = dict(default=None, type='int'),
        memory = dict(default=None, type='int'),
        template = dict(default=None),
        iso = dict(default=None),
        template_filter = dict(default="executable", aliases=['iso_filter'], choices=['featured', 'self', 'selfexecutable', 'sharedexecutable', 'executable', 'community']),
        networks = dict(type='list', aliases=[ 'network' ], default=None),
        ip_to_networks = dict(type='list', aliases=['ip_to_network'], default=None),
        ip_address = dict(defaul=None),
        ip6_address = dict(defaul=None),
        disk_offering = dict(default=None),
        disk_size = dict(type='int', default=None),
        root_disk_size = dict(type='int', default=None),
        keyboard = dict(choices=['de', 'de-ch', 'es', 'fi', 'fr', 'fr-be', 'fr-ch', 'is', 'it', 'jp', 'nl-be', 'no', 'pt', 'uk', 'us'], default=None),
        hypervisor = dict(choices=CS_HYPERVISORS, default=None),
        security_groups = dict(type='list', aliases=[ 'security_group' ], default=None),
        affinity_groups = dict(type='list', aliases=[ 'affinity_group' ], default=[]),
        domain = dict(default=None),
        account = dict(default=None),
        project = dict(default=None),
        user_data = dict(default=None),
        zone = dict(default=None),
        ssh_key = dict(default=None),
        force = dict(type='bool', default=False),
        tags = dict(type='list', aliases=[ 'tag' ], default=None),
        vpc = dict(default=None),
        poll_async = dict(type='bool', default=True),
    ))

    required_together = cs_required_together()
    required_together.extend([
        ['cpu', 'cpu_speed', 'memory'],
    ])

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=required_together,
        required_one_of = (
            ['display_name', 'name'],
        ),
        mutually_exclusive = (
            ['template', 'iso'],
        ),
        supports_check_mode=True
    )

    try:
        acs_instance = AnsibleCloudStackInstance(module)

        state = module.params.get('state')

        if state in ['absent', 'destroyed']:
            instance = acs_instance.absent_instance()

        elif state in ['expunged']:
            instance = acs_instance.expunge_instance()

        elif state in ['restored']:
            acs_instance.present_instance()
            instance = acs_instance.restore_instance()

        elif state in ['present', 'deployed']:
            instance = acs_instance.present_instance()

        elif state in ['stopped']:
            acs_instance.present_instance(start_vm=False)
            instance = acs_instance.stop_instance()

        elif state in ['started']:
            acs_instance.present_instance()
            instance = acs_instance.start_instance()

        elif state in ['restarted']:
            acs_instance.present_instance()
            instance = acs_instance.restart_instance()

        if instance and 'state' in instance and instance['state'].lower() == 'error':
            module.fail_json(msg="Instance named '%s' in error state." % module.params.get('name'))

        result = acs_instance.get_result(instance)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
