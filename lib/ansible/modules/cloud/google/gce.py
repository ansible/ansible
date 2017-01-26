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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: gce
version_added: "1.4"
short_description: create or terminate GCE instances
description:
     - Creates or terminates Google Compute Engine (GCE) instances.  See
       U(https://cloud.google.com/compute) for an overview.
       Full install/configuration instructions for the gce* modules can
       be found in the comments of ansible/test/gce_tests.py.
options:
  image:
    description:
      - image string to use for the instance (default will follow latest
        stable debian image)
    required: false
    default: "debian-8"
  instance_names:
    description:
      - a comma-separated list of instance names to create or destroy
    required: false
    default: null
  machine_type:
    description:
      - machine type to use for the instance, use 'n1-standard-1' by default
    required: false
    default: "n1-standard-1"
  metadata:
    description:
      - a hash/dictionary of custom data for the instance;
        '{"key":"value", ...}'
    required: false
    default: null
  service_account_email:
    version_added: "1.5.1"
    description:
      - service account email
    required: false
    default: null
  service_account_permissions:
    version_added: "2.0"
    description:
      - service account permissions (see
        U(https://cloud.google.com/sdk/gcloud/reference/compute/instances/create),
        --scopes section for detailed information)
    required: false
    default: null
    choices: [
      "bigquery", "cloud-platform", "compute-ro", "compute-rw",
      "useraccounts-ro", "useraccounts-rw", "datastore", "logging-write",
      "monitoring", "sql", "sql-admin", "storage-full", "storage-ro",
      "storage-rw", "taskqueue", "userinfo-email"
    ]
  pem_file:
    version_added: "1.5.1"
    description:
      - path to the pem file associated with the service account email
        This option is deprecated. Use 'credentials_file'.
    required: false
    default: null
  credentials_file:
    version_added: "2.1.0"
    description:
      - path to the JSON file associated with the service account email
    default: null
    required: false
  project_id:
    version_added: "1.5.1"
    description:
      - your GCE project ID
    required: false
    default: null
  name:
    description:
      - either a name of a single instance or when used with 'num_instances',
        the base name of a cluster of nodes
    required: false
    aliases: ['base_name']
  num_instances:
    description:
      - can be used with 'name', specifies
        the number of nodes to provision using 'name'
        as a base name
    required: false
    version_added: "2.3"
  network:
    description:
      - name of the network, 'default' will be used if not specified
    required: false
    default: "default"
  subnetwork:
    description:
      - name of the subnetwork in which the instance should be created
    required: false
    default: null
    version_added: "2.2"
  persistent_boot_disk:
    description:
      - if set, create the instance with a persistent boot disk
    required: false
    default: "false"
  disks:
    description:
      - a list of persistent disks to attach to the instance; a string value
        gives the name of the disk; alternatively, a dictionary value can
        define 'name' and 'mode' ('READ_ONLY' or 'READ_WRITE'). The first entry
        will be the boot disk (which must be READ_WRITE).
    required: false
    default: null
    version_added: "1.7"
  state:
    description:
      - desired state of the resource
    required: false
    default: "present"
    choices: ["active", "present", "absent", "deleted", "started", "stopped", "terminated"]
  tags:
    description:
      - a comma-separated list of tags to associate with the instance
    required: false
    default: null
  zone:
    description:
      - the GCE zone to use
    required: true
    default: "us-central1-a"
  ip_forward:
    version_added: "1.9"
    description:
      - set to true if the instance can forward ip packets (useful for
        gateways)
    required: false
    default: "false"
  external_ip:
    version_added: "1.9"
    description:
      - type of external ip, ephemeral by default; alternatively, a fixed gce ip or ip name can be given. Specify 'none' if no external ip is desired.
    required: false
    default: "ephemeral"
  disk_auto_delete:
    version_added: "1.9"
    description:
      - if set boot disk will be removed after instance destruction
    required: false
    default: "true"
  preemptible:
    version_added: "2.1"
    description:
      - if set to true, instances will be preemptible and time-limited.
        (requires libcloud >= 0.20.0)
    required: false
    default: "false"
  disk_size:
    description:
      - The size of the boot disk created for this instance (in GB)
    required: false
    default: 10
    version_added: "2.3"

requirements:
    - "python >= 2.6"
    - "apache-libcloud >= 0.13.3, >= 0.17.0 if using JSON credentials,
      >= 0.20.0 if using preemptible option"
notes:
  - Either I(instance_names) or I(name) is required.
  - JSON credentials strongly preferred.
author: "Eric Johnson (@erjohnso) <erjohnso@google.com>, Tom Melendez (@supertom) <supertom@google.com>"
'''

EXAMPLES = '''
# Basic provisioning example.  Create a single Debian 8 instance in the
# us-central1-a Zone of the n1-standard-1 machine type.
# Create multiple instances by specifying multiple names, seperated by
# commas in the instance_names field
# (e.g. my-test-instance1,my-test-instance2)
    gce:
      instance_names: my-test-instance1
      zone: us-central1-a
      machine_type: n1-standard-1
      image: debian-8
      state: present
      service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"
      credentials_file: "/path/to/your-key.json"
      project_id: "your-project-name"
      disk_size: 32

# Create a single Debian 8 instance in the us-central1-a Zone
# Use existing disks, custom network/subnetwork, set service account permissions
# add tags and metadata.
    gce:
      instance_names: my-test-instance
      zone: us-central1-a
      machine_type: n1-standard-1
      state: present
      metadata: '{"db":"postgres", "group":"qa", "id":500}'
      tags:
        - http-server
        - my-other-tag
      disks:
        - name: disk-2
          mode: READ_WRITE
        - name: disk-3
          mode: READ_ONLY
      disk_auto_delete: false
      network: foobar-network
      subnetwork: foobar-subnetwork-1
      preemptible: true
      ip_forward: true
      service_account_permissions:
        - storage-full
        - taskqueue
        - bigquery
      service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"
      credentials_file: "/path/to/your-key.json"
      project_id: "your-project-name"

# Example Playbook
- name: Compute Engine Instance Examples
  hosts: localhost
  vars:
    service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"
    credentials_file: "/path/to/your-key.json"
    project_id: "your-project-name"
  tasks:
    - name: create multiple instances
      # Basic provisioning example.  Create multiple Debian 8 instances in the
      # us-central1-a Zone of n1-standard-1 machine type.
      gce:
        instance_names: test1,test2,test3
        zone: us-central1-a
        machine_type: n1-standard-1
        image: debian-8
        state: present
        service_account_email: "{{ service_account_email }}"
        credentials_file: "{{ credentials_file }}"
        project_id: "{{ project_id }}"
        metadata : '{ "startup-script" : "apt-get update" }'
      register: gce

    - name: Save host data
      add_host:
        hostname: "{{ item.public_ip }}"
        groupname: gce_instances_ips
      with_items: "{{ gce.instance_data }}"

    - name: Wait for SSH for instances
      wait_for:
        delay: 1
        host: "{{ item.public_ip }}"
        port: 22
        state: started
        timeout: 30
      with_items: "{{ gce.instance_data }}"

    - name: Configure Hosts
      hosts: gce_instances_ips
      become: yes
      become_method: sudo
      roles:
        - my-role-one
        - my-role-two
      tags:
        - config

    - name: delete test-instances
      # Basic termination of instance.
      gce:
        service_account_email: "{{ service_account_email }}"
        credentials_file: "{{ credentials_file }}"
        project_id: "{{ project_id }}"
        instance_names: "{{ gce.instance_names }}"
        zone: us-central1-a
        state: absent
      tags:
        - delete
'''

import socket

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

try:
    from ast import literal_eval
    HAS_PYTHON26 = True
except ImportError:
    HAS_PYTHON26 = False


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
    try:
        subnetname = inst.extra['networkInterfaces'][0]['subnetwork'].split('/')[-1]
    except:
        subnetname = None
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
        'image': inst.image is not None and inst.image.split('/')[-1] or None,
        'disks': disk_names,
        'machine_type': inst.size,
        'metadata': metadata,
        'name': inst.name,
        'network': netname,
        'subnetwork': subnetname,
        'private_ip': inst.private_ips[0],
        'public_ip': public_ip,
        'status': ('status' in inst.extra) and inst.extra['status'] or None,
        'tags': ('tags' in inst.extra) and inst.extra['tags'] or [],
        'zone': ('zone' in inst.extra) and inst.extra['zone'].name or None,
    })


def create_instances(module, gce, instance_names, number):
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
    subnetwork = module.params.get('subnetwork')
    persistent_boot_disk = module.params.get('persistent_boot_disk')
    disks = module.params.get('disks')
    state = module.params.get('state')
    tags = module.params.get('tags')
    zone = module.params.get('zone')
    ip_forward = module.params.get('ip_forward')
    external_ip = module.params.get('external_ip')
    disk_auto_delete = module.params.get('disk_auto_delete')
    preemptible = module.params.get('preemptible')
    disk_size = module.params.get('disk_size')
    service_account_permissions = module.params.get('service_account_permissions')
    service_account_email = module.params.get('service_account_email')

    if external_ip == "none":
        instance_external_ip = None
    elif external_ip != "ephemeral":
        instance_external_ip = external_ip
        try:
            # check if instance_external_ip is an ip or a name
            try:
                socket.inet_aton(instance_external_ip)
                instance_external_ip = GCEAddress(id='unknown', name='unknown', address=instance_external_ip, region='unknown', driver=gce)
            except socket.error:
                instance_external_ip = gce.ex_get_address(instance_external_ip)
        except GoogleBaseError as e:
            module.fail_json(msg='Unexpected error attempting to get a static ip %s, error: %s' % (external_ip, e.value))
    else:
        instance_external_ip = external_ip

    new_instances = []
    changed = False

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
        if isinstance(metadata, dict):
            md = metadata
        else:
            try:
                md = literal_eval(str(metadata))
                if not isinstance(md, dict):
                    raise ValueError('metadata must be a dict')
            except ValueError as e:
                module.fail_json(msg='bad metadata: %s' % str(e))
            except SyntaxError as e:
                module.fail_json(msg='bad metadata syntax')

        if hasattr(libcloud, '__version__') and libcloud.__version__ < '0.15':
            items = []
            for k, v in md.items():
                items.append({"key": k, "value": v})
            metadata = {'items': items}
        else:
            metadata = md

    lc_image = LazyDiskImage(module, gce, image, lc_disks)
    ex_sa_perms = []
    bad_perms = []
    if service_account_permissions:
        for perm in service_account_permissions:
            if perm not in gce.SA_SCOPES_MAP:
                bad_perms.append(perm)
        if len(bad_perms) > 0:
            module.fail_json(msg='bad permissions: %s' % str(bad_perms))
        ex_sa_perms.append({'email': "default"})
        ex_sa_perms[0]['scopes'] = service_account_permissions

    # These variables all have default values but check just in case
    if not lc_network or not lc_machine_type or not lc_zone:
        module.fail_json(msg='Missing required create instance variable',
                         changed=False)

    gce_args = dict(
        location=lc_zone,
        ex_network=network, ex_tags=tags, ex_metadata=metadata,
        ex_can_ip_forward=ip_forward,
        external_ip=instance_external_ip, ex_disk_auto_delete=disk_auto_delete,
        ex_service_accounts=ex_sa_perms
    )
    if preemptible is not None:
        gce_args['ex_preemptible'] = preemptible
    if subnetwork is not None:
        gce_args['ex_subnetwork'] = subnetwork

    if isinstance(instance_names, str) and not number:
        instance_names = [instance_names]

    if isinstance(instance_names, str) and number:
        instance_responses = gce.ex_create_multiple_nodes(instance_names, lc_machine_type,
                                                          lc_image(), number, **gce_args)
        for resp in instance_responses:
            n = resp
            if isinstance(resp, libcloud.compute.drivers.gce.GCEFailedNode):
                try:
                    n = gce.ex_get_node(n.name, lc_zone)
                except ResourceNotFoundError:
                    pass
            else:
                # Assure that at least one node has been created to set changed=True
                changed = True
            new_instances.append(n)
    else:
        for instance in instance_names:
            pd = None
            if lc_disks:
                pd = lc_disks[0]
            elif persistent_boot_disk:
                try:
                    pd = gce.ex_get_volume("%s" % instance, lc_zone)
                except ResourceNotFoundError:
                    pd = gce.create_volume(disk_size, "%s" % instance, image=lc_image())
            gce_args['ex_boot_disk'] = pd

            inst = None
            try:
                inst = gce.ex_get_node(instance, lc_zone)
            except ResourceNotFoundError:
                inst = gce.create_node(
                    instance, lc_machine_type, lc_image(), **gce_args
                )
                changed = True
            except GoogleBaseError as e:
                module.fail_json(msg='Unexpected error attempting to create ' +
                                 'instance %s, error: %s' % (instance, e.value))
            if inst:
                new_instances.append(inst)

    for inst in new_instances:
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

    instance_names = []
    instance_json_data = []
    for inst in new_instances:
        d = get_instance_info(inst)
        instance_names.append(d['name'])
        instance_json_data.append(d)

    return (changed, instance_json_data, instance_names)

def change_instance_state(module, gce, instance_names, number, zone_name, state):
    """Changes the state of a list of instances. For example,
    change from started to stopped, or started to absent.

    module: Ansible module object
    gce: authenticated GCE connection object
    instance_names: a list of instance names to terminate
    zone_name: the zone where the instances reside prior to termination
    state: 'state' parameter passed into module as argument

    Returns a dictionary of instance names that were changed.

    """
    changed = False
    nodes = []
    state_instance_names = []

    if isinstance(instance_names, str) and number:
        node_names = ['%s-%03d' % (instance_names, i) for i in range(number)]
    elif isinstance(instance_names, str) and not number:
        node_names = [instance_names]
    else:
        node_names = instance_names

    for name in node_names:
        inst = None
        try:
            inst = gce.ex_get_node(name, zone_name)
        except ResourceNotFoundError:
            state_instance_names.append(name)
        except Exception as e:
            module.fail_json(msg=unexpected_error_msg(e), changed=False)
        else:
            nodes.append(inst)
            state_instance_names.append(name)

    if state in ['absent', 'deleted'] and number:
        changed_nodes = gce.ex_destroy_multiple_nodes(nodes) or [False]
        changed = reduce(lambda x, y: x or y, changed_nodes)
    else:
        for node in nodes:
            if state in ['absent', 'deleted']:
                gce.destroy_node(node)
                changed = True
            elif state == 'started' and \
                      node.state == libcloud.compute.types.NodeState.STOPPED:
                gce.ex_start_node(node)
                changed = True
            elif state in ['stopped', 'terminated'] and \
                      node.state == libcloud.compute.types.NodeState.RUNNING:
                gce.ex_stop_node(node)
                changed = True

    return (changed, state_instance_names)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            image = dict(default='debian-8'),
            instance_names = dict(),
            machine_type = dict(default='n1-standard-1'),
            metadata = dict(),
            name = dict(aliases=['base_name']),
            num_instances = dict(type='int'),
            network = dict(default='default'),
            subnetwork = dict(),
            persistent_boot_disk = dict(type='bool', default=False),
            disks = dict(type='list'),
            state = dict(choices=['active', 'present', 'absent', 'deleted',
                                  'started', 'stopped', 'terminated'],
                         default='present'),
            tags = dict(type='list'),
            zone = dict(default='us-central1-a'),
            service_account_email = dict(),
            service_account_permissions = dict(type='list'),
            pem_file = dict(type='path'),
            credentials_file = dict(type='path'),
            project_id = dict(),
            ip_forward = dict(type='bool', default=False),
            external_ip=dict(default='ephemeral'),
            disk_auto_delete = dict(type='bool', default=True),
            disk_size = dict(type='int', default=10),
            preemptible = dict(type='bool', default=None),
        ),
        mutually_exclusive=[('instance_names', 'name')]
    )

    if not HAS_PYTHON26:
        module.fail_json(msg="GCE module requires python's 'ast' module, python v2.6+")
    if not HAS_LIBCLOUD:
        module.fail_json(msg='libcloud with GCE support (0.17.0+) required for this module')

    gce = gce_connect(module)

    image = module.params.get('image')
    instance_names = module.params.get('instance_names')
    machine_type = module.params.get('machine_type')
    metadata = module.params.get('metadata')
    name = module.params.get('name')
    number = module.params.get('num_instances')
    network = module.params.get('network')
    subnetwork = module.params.get('subnetwork')
    persistent_boot_disk = module.params.get('persistent_boot_disk')
    state = module.params.get('state')
    tags = module.params.get('tags')
    zone = module.params.get('zone')
    ip_forward = module.params.get('ip_forward')
    preemptible = module.params.get('preemptible')
    changed = False

    inames = None
    if isinstance(instance_names, list):
        inames = instance_names
    elif isinstance(instance_names, str):
        inames = instance_names.split(',')
    if name:
        inames = name
    if not inames:
        module.fail_json(msg='Must specify a "name" or "instance_names"',
                         changed=False)
    if not zone:
        module.fail_json(msg='Must specify a "zone"', changed=False)

    if preemptible is not None and hasattr(libcloud, '__version__') and libcloud.__version__ < '0.20':
        module.fail_json(msg="Apache Libcloud 0.20.0+ is required to use 'preemptible' option",
                         changed=False)

    if subnetwork is not None and not hasattr(gce, 'ex_get_subnetwork'):
        module.fail_json(msg="Apache Libcloud 1.0.0+ is required to use 'subnetwork' option",
                         changed=False)

    json_output = {'zone': zone}
    if state in ['absent', 'deleted', 'started', 'stopped', 'terminated']:
        json_output['state'] = state
        (changed, state_instance_names) = change_instance_state(
            module, gce, inames, number, zone, state)

        # based on what user specified, return the same variable, although
        # value could be different if an instance could not be destroyed
        if instance_names or name and number:
            json_output['instance_names'] = state_instance_names
        elif name:
            json_output['name'] = name

    elif state in ['active', 'present']:
        json_output['state'] = 'present'
        (changed, instance_data, instance_name_list) = create_instances(
            module, gce, inames, number)
        json_output['instance_data'] = instance_data
        if instance_names:
            json_output['instance_names'] = instance_name_list
        elif name:
            json_output['name'] = name

    json_output['changed'] = changed
    module.exit_json(**json_output)


class LazyDiskImage:
    """
    Object for lazy instantiation of disk image
    gce.ex_get_image is a very expensive call, so we want to avoid calling it as much as possible.
    """
    def __init__(self, module, gce, name, has_pd):
        self.image = None
        self.was_called = False
        self.gce = gce
        self.name = name
        self.has_pd = has_pd
        self.module = module

    def __call__(self):
        if not self.was_called:
            self.was_called = True
            if not self.has_pd:
                self.image = self.gce.ex_get_image(self.name)
                if not self.image:
                    self.module.fail_json(msg='image or disks missing for create instance', changed=False)
        return self.image


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.gce import *
if __name__ == '__main__':
    main()
