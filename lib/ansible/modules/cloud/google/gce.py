#!/usr/bin/python
# Copyright 2013 Google Inc.
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

DOCUMENTATION = '''
---
module: gce
version_added: "1.4"
short_description: create or terminate GCE instances
description:
     - Creates or terminates Google Compute Engine (GCE) instances.  See
       U(https://cloud.google.com/products/compute-engine) for an overview.
       Full install/configuration instructions for the gce* modules can
       be found in the comments of ansible/test/gce_tests.py.
options:
  image:
    description:
       - image string to use for the instance
    required: false
    default: "debian-7"
    aliases: []
  instance_names:
    description:
      - a comma-separated list of instance names to create or destroy
    required: false
    default: null
    aliases: []
  machine_type:
    description:
      - machine type to use for the instance, use 'n1-standard-1' by default
    required: false
    default: "n1-standard-1"
    aliases: []
  metadata:
    description:
      - a hash/dictionary of custom data for the instance; '{"key":"value",...}'
    required: false
    default: null
    aliases: []
  service_account_email:
    version_added: 1.5.1
    description:
      - service account email
    required: false
    default: null
    aliases: []
  pem_file:
    version_added: 1.5.1
    description:
      - path to the pem file associated with the service account email
    required: false
    default: null
    aliases: []
  project_id:
    version_added: 1.5.1
    description:
      - your GCE project ID
    required: false
    default: null
    aliases: []
  name:
    description:
      - identifier when working with a single instance
    required: false
    aliases: []
  network:
    description:
      - name of the network, 'default' will be used if not specified
    required: false
    default: "default"
    aliases: []
  persistent_boot_disk:
    description:
      - if set, create the instance with a persistent boot disk
    required: false
    default: "false"
    aliases: []
  disks:
    description:
      - a list of persistent disks to attach to the instance; a string value gives the name of the disk; alternatively, a dictionary value can define 'name' and 'mode' ('READ_ONLY' or 'READ_WRITE'). The first entry will be the boot disk (which must be READ_WRITE).
    required: false
    default: null
    aliases: []
    version_added: "1.7"
  state:
    description:
      - desired state of the resource
    required: false
    default: "present"
    choices: ["active", "present", "absent", "deleted"]
    aliases: []
  tags:
    description:
      - a comma-separated list of tags to associate with the instance
    required: false
    default: null
    aliases: []
  zone:
    description:
      - the GCE zone to use
    required: true
    default: "us-central1-a"
    aliases: []
  ip_forward:
    version_added: "1.9"
    description:
      - set to true if the instance can forward ip packets (useful for gateways)
    required: false
    default: "false"
    aliases: []
  external_ip:
    version_added: "1.9"
    description:
      - type of external ip, ephemeral by default
    required: false
    default: "ephemeral"
    aliases: []
  disk_auto_delete:
    version_added: "1.9"
    description:
      - if set boot disk will be removed after instance destruction
    required: false
    default: "true"
    aliases: []

requirements: [ "libcloud" ]
notes:
  - Either I(name) or I(instance_names) is required.
author: Eric Johnson <erjohnso@google.com>
'''

EXAMPLES = '''
# Basic provisioning example.  Create a single Debian 7 instance in the
# us-central1-a Zone of n1-standard-1 machine type.
- local_action:
    module: gce
    name: test-instance
    zone: us-central1-a
    machine_type: n1-standard-1
    image: debian-7

# Example using defaults and with metadata to create a single 'foo' instance
- local_action:
    module: gce
    name: foo
    metadata: '{"db":"postgres", "group":"qa", "id":500}'


# Launch instances from a control node, runs some tasks on the new instances,
# and then terminate them
- name: Create a sandbox instance
  hosts: localhost
  vars:
    names: foo,bar
    machine_type: n1-standard-1
    image: debian-6
    zone: us-central1-a
    service_account_email: unique-email@developer.gserviceaccount.com
    pem_file: /path/to/pem_file
    project_id: project-id
  tasks:
    - name: Launch instances
      local_action: gce instance_names={{names}} machine_type={{machine_type}}
                    image={{image}} zone={{zone}} service_account_email={{ service_account_email }}
                    pem_file={{ pem_file }} project_id={{ project_id }}
      register: gce
    - name: Wait for SSH to come up
      local_action: wait_for host={{item.public_ip}} port=22 delay=10
                    timeout=60 state=started
      with_items: {{gce.instance_data}}

- name: Configure instance(s)
  hosts: launched
  sudo: True
  roles:
    - my_awesome_role
    - my_awesome_tasks

- name: Terminate instances
  hosts: localhost
  connection: local
  tasks:
    - name: Terminate instances that were previously launched
      local_action:
        module: gce
        state: 'absent'
        instance_names: {{gce.instance_names}}

'''

import sys

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, \
            ResourceExistsError, ResourceInUseError, ResourceNotFoundError
    _ = Provider.GCE
except ImportError:
    print("failed=True " + \
        "msg='libcloud with GCE support (0.13.3+) required for this module'")
    sys.exit(1)

try:
    from ast import literal_eval
except ImportError:
    print("failed=True " + \
        "msg='GCE module requires python's 'ast' module, python v2.6+'")
    sys.exit(1)


def get_instance_info(inst):
    """Retrieves instance information from an instance object and returns it
    as a dictionary.

    """
    metadata = {}
    if 'metadata' in inst.extra and 'items' in inst.extra['metadata']:
        for md in inst.extra['metadata']['items']:
            metadata[md['key']] = md['value']

    try:
        netname = inst.extra['networkInterfaces'][0]['network'].split('/')[-1]
    except:
        netname = None
    if 'disks' in inst.extra:
        disk_names = [disk_info['source'].split('/')[-1]
                      for disk_info
                      in sorted(inst.extra['disks'],
                                key=lambda disk_info: disk_info['index'])]
    else:
        disk_names = []

    if len(inst.public_ips) == 0:
        public_ip = None
    else:
        public_ip = inst.public_ips[0]

    return({
        'image': not inst.image is None and inst.image.split('/')[-1] or None,
        'disks': disk_names,
        'machine_type': inst.size,
        'metadata': metadata,
        'name': inst.name,
        'network': netname,
        'private_ip': inst.private_ips[0],
        'public_ip': public_ip,
        'status': ('status' in inst.extra) and inst.extra['status'] or None,
        'tags': ('tags' in inst.extra) and inst.extra['tags'] or [],
        'zone': ('zone' in inst.extra) and inst.extra['zone'].name or None,
   })

def create_instances(module, gce, instance_names):
    """Creates new instances. Attributes other than instance_names are picked
    up from 'module'

    module : AnsibleModule object
    gce: authenticated GCE libcloud driver
    instance_names: python list of instance names to create

    Returns:
        A list of dictionaries with instance information
        about the instances that were launched.

    """
    image = module.params.get('image')
    machine_type = module.params.get('machine_type')
    metadata = module.params.get('metadata')
    network = module.params.get('network')
    persistent_boot_disk = module.params.get('persistent_boot_disk')
    disks = module.params.get('disks')
    state = module.params.get('state')
    tags = module.params.get('tags')
    zone = module.params.get('zone')
    ip_forward = module.params.get('ip_forward')
    external_ip = module.params.get('external_ip')
    disk_auto_delete = module.params.get('disk_auto_delete')

    if external_ip == "none":
        external_ip = None

    new_instances = []
    changed = False

    lc_image = gce.ex_get_image(image)
    lc_disks = []
    disk_modes = []
    for i, disk in enumerate(disks or []):
        if isinstance(disk, dict):
            lc_disks.append(gce.ex_get_volume(disk['name']))
            disk_modes.append(disk['mode'])
        else:
            lc_disks.append(gce.ex_get_volume(disk))
            # boot disk is implicitly READ_WRITE
            disk_modes.append('READ_ONLY' if i > 0 else 'READ_WRITE')
    lc_network = gce.ex_get_network(network)
    lc_machine_type = gce.ex_get_size(machine_type)
    lc_zone = gce.ex_get_zone(zone)

    # Try to convert the user's metadata value into the format expected
    # by GCE.  First try to ensure user has proper quoting of a
    # dictionary-like syntax using 'literal_eval', then convert the python
    # dict into a python list of 'key' / 'value' dicts.  Should end up
    # with:
    # [ {'key': key1, 'value': value1}, {'key': key2, 'value': value2}, ...]
    if metadata:
        try:
            md = literal_eval(metadata)
            if not isinstance(md, dict):
                raise ValueError('metadata must be a dict')
        except ValueError, e:
            print("failed=True msg='bad metadata: %s'" % str(e))
            sys.exit(1)
        except SyntaxError, e:
            print("failed=True msg='bad metadata syntax'")
            sys.exit(1)

        items = []
        for k,v in md.items():
            items.append({"key": k,"value": v})
        metadata = {'items': items}

    # These variables all have default values but check just in case
    if not lc_image or not lc_network or not lc_machine_type or not lc_zone:
        module.fail_json(msg='Missing required create instance variable',
                changed=False)

    for name in instance_names:
        pd = None
        if lc_disks:
            pd = lc_disks[0]
        elif persistent_boot_disk:
            try:
                pd = gce.create_volume(None, "%s" % name, image=lc_image)
            except ResourceExistsError:
                pd = gce.ex_get_volume("%s" % name, lc_zone)
        inst = None
        try:
            inst = gce.create_node(name, lc_machine_type, lc_image,
                    location=lc_zone, ex_network=network, ex_tags=tags,
                    ex_metadata=metadata, ex_boot_disk=pd, ex_can_ip_forward=ip_forward,
                    external_ip=external_ip, ex_disk_auto_delete=disk_auto_delete)
            changed = True
        except ResourceExistsError:
            inst = gce.ex_get_node(name, lc_zone)
        except GoogleBaseError, e:
            module.fail_json(msg='Unexpected error attempting to create ' + \
                    'instance %s, error: %s' % (name, e.value))

        for i, lc_disk in enumerate(lc_disks):
            # Check whether the disk is already attached
            if (len(inst.extra['disks']) > i):
                attached_disk = inst.extra['disks'][i]
                if attached_disk['source'] != lc_disk.extra['selfLink']:
                    module.fail_json(
                        msg=("Disk at index %d does not match: requested=%s found=%s" % (
                            i, lc_disk.extra['selfLink'], attached_disk['source'])))
                elif attached_disk['mode'] != disk_modes[i]:
                    module.fail_json(
                        msg=("Disk at index %d is in the wrong mode: requested=%s found=%s" % (
                            i, disk_modes[i], attached_disk['mode'])))
                else:
                    continue
            gce.attach_volume(inst, lc_disk, ex_mode=disk_modes[i])
            # Work around libcloud bug: attached volumes don't get added
            # to the instance metadata. get_instance_info() only cares about
            # source and index.
            if len(inst.extra['disks']) != i+1:
                inst.extra['disks'].append(
                    {'source': lc_disk.extra['selfLink'], 'index': i})

        if inst:
            new_instances.append(inst)

    instance_names = []
    instance_json_data = []
    for inst in new_instances:
        d = get_instance_info(inst)
        instance_names.append(d['name'])
        instance_json_data.append(d)

    return (changed, instance_json_data, instance_names)


def terminate_instances(module, gce, instance_names, zone_name):
    """Terminates a list of instances.

    module: Ansible module object
    gce: authenticated GCE connection object
    instance_names: a list of instance names to terminate
    zone_name: the zone where the instances reside prior to termination

    Returns a dictionary of instance names that were terminated.

    """
    changed = False
    terminated_instance_names = []
    for name in instance_names:
        inst = None
        try:
            inst = gce.ex_get_node(name, zone_name)
        except ResourceNotFoundError:
            pass
        except Exception, e:
            module.fail_json(msg=unexpected_error_msg(e), changed=False)
        if inst:
            gce.destroy_node(inst)
            terminated_instance_names.append(inst.name)
            changed = True

    return (changed, terminated_instance_names)


def main():
    module = AnsibleModule(
        argument_spec = dict(
            image = dict(default='debian-7'),
            instance_names = dict(),
            machine_type = dict(default='n1-standard-1'),
            metadata = dict(),
            name = dict(),
            network = dict(default='default'),
            persistent_boot_disk = dict(type='bool', default=False),
            disks = dict(type='list'),
            state = dict(choices=['active', 'present', 'absent', 'deleted'],
                    default='present'),
            tags = dict(type='list'),
            zone = dict(default='us-central1-a'),
            service_account_email = dict(),
            pem_file = dict(),
            project_id = dict(),
            ip_forward = dict(type='bool', default=False),
            external_ip = dict(choices=['ephemeral', 'none'],
                    default='ephemeral'),
            disk_auto_delete = dict(type='bool', default=True),
        )
    )

    gce = gce_connect(module)

    image = module.params.get('image')
    instance_names = module.params.get('instance_names')
    machine_type = module.params.get('machine_type')
    metadata = module.params.get('metadata')
    name = module.params.get('name')
    network = module.params.get('network')
    persistent_boot_disk = module.params.get('persistent_boot_disk')
    state = module.params.get('state')
    tags = module.params.get('tags')
    zone = module.params.get('zone')
    ip_forward = module.params.get('ip_forward')
    changed = False

    inames = []
    if isinstance(instance_names, list):
        inames = instance_names
    elif isinstance(instance_names, str):
        inames = instance_names.split(',')
    if name:
        inames.append(name)
    if not inames:
        module.fail_json(msg='Must specify a "name" or "instance_names"',
                changed=False)
    if not zone:
        module.fail_json(msg='Must specify a "zone"', changed=False)

    json_output = {'zone': zone}
    if state in ['absent', 'deleted']:
        json_output['state'] = 'absent'
        (changed, terminated_instance_names) = terminate_instances(module,
                gce, inames, zone)

        # based on what user specified, return the same variable, although
        # value could be different if an instance could not be destroyed
        if instance_names:
            json_output['instance_names'] = terminated_instance_names
        elif name:
            json_output['name'] = name

    elif state in ['active', 'present']:
        json_output['state'] = 'present'
        (changed, instance_data,instance_name_list) = create_instances(
                module, gce, inames)
        json_output['instance_data'] = instance_data
        if instance_names:
            json_output['instance_names'] = instance_name_list
        elif name:
            json_output['name'] = name


    json_output['changed'] = changed
    print json.dumps(json_output)
    sys.exit(0)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.gce import *

main()
