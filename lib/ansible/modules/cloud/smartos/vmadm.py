#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Jasper Lievisse Adriaanse <j@jasper.la>
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
#

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: vmadm
short_description: Manage SmartOS virtual machines and zones.
description:
  - Manage SmartOS virtual machines through vmadm(1M).
version_added: "2.3"
author: Jasper Lievisse Adriaanse (@jasperla)
options:
  autoboot:
    required: false
    description:
      - Whether or not a VM is booted when the system is rebooted.
  brand:
    required: true
    choices: [ joyent, joyent-minimal, kvm, lx ]
    default: joyent
    description:
      - Type for of virtual machine.
  cpu_cap:
    required: false
    description:
      - Sets a limit on the amount of CPU time that can be used by a VM.
        Use C(0) for no cap.
  cpu_shares:
    required: false
    description:
      - Sets a limit on the number of fair share scheduler (FSS) CPU shares for
        a VM. This limit is relative to all other VMs on the system.
  customer_metadata:
    required: false
    description:
      - Metadata to be set and associated with this VM, this contain customer
        modifiable keys.
  delegate_dataset:
    required: false
    description:
      - Whether to delegate a ZFS dataset to an OS VM.
  disk_driver:
    required: false
    description:
      - Default value for a virtual disk model for KVM guests.
  disks:
    required: false
    description:
      - A list of disks to add, valid properties are documented in vmadm(1M).
  dns_domain:
    required: false
    description:
      - Domain value for C(/etc/hosts).
  filesystems:
      required: false
      description:
        - Mount additional filesystems into an OS VM.
  firewall_enabled:
    required: false
    description:
      - Enables the firewall, allowing fwadm(1M) rules to be applied.
  force:
    required: false
    description:
      - Force a particular action (i.e. stop or delete a VM).
  fs_allowed:
    required: false
    description:
      - Comma separated list of filesystem types this zone is allowed to mount.
  hostname:
    required: false
    description:
      - Zone/VM hostname.
  image_uuid:
    required: false
    description:
      - Image UUID.
  indestructible_zoneroot:
    required: false
    description:
      - Adds an C(@indestructible) snapshot to zoneroot.
  internal_metadata:
    required: false
    description:
      - Metadata to be set and associated with this VM, this contains operator
        generated keys.
  kernel_version:
    required: false
    description:
      - Kernel version to emulate for LX VMs.
  maintain_resolvers:
    required: false
    description:
      - Resolvers in C(/etc/resolv.conf) will be updated when updating
        the I(resolvers) property.
  max_physical_memory:
    required: false
    description:
      - Maximum amount of memory (in MiBs) on the host that the VM is allowed to use.
  max_swap:
    required: false
    description:
      - Maximum amount of virtual memory (in MiBs) the VM is allowed to use.
  name:
    required: false
    aliases: [ alias ]
    description:
      - Name of the VM. vmadm(1M) uses this as an optional name.
  nic_driver:
    required: false
    description:
      - Default value for a virtual NIC model for KVM guests.
  nics:
    required: false
    description:
      - A list of nics to add, valid properties are documented in vmadm(1M).
  qemu_extra_opts:
    required: false
    description:
      - Additional qemu cmdline arguments for KVM guests.
  quota:
    required: false
    description:
      - Quota on zone filesystems (in MiBs).
  ram:
    required: false
    description:
      - Amount of virtual RAM for a KVM guest (in MiBs).
  resolvers:
    required: false
    description:
      - List of resolvers to be put into C(/etc/resolv.conf).
  state:
    required: true
    choices: [ present, absent, stopped, restarted ]
    description:
      - States for the VM to be in. Please note that C(present), C(stopped) and C(restarted)
        operate on a VM that is currently provisioned. C(present) means that the VM will be
        created if it was absent, and that it will be in a running state. C(absent) will
        shutdown the zone before removing it.
        C(stopped) means the zone will be created if it doesn't exist already, before shutting
        it down.
  uuid:
    required: false
    description:
      - UUID of the VM. Can either be a full UUID or C(*) for all VMs.
  vcpus:
    required: false
    description:
      - Number of virtual CPUs for a KVM guest.
  vnc_port:
    required: false
    description:
      - TCP port to listen of the VNC server. Or set C(0) for random,
        or C(-1) to disable.
  zfs_io_priority:
    required: false
    description:
      - IO throttle priority value relative to other VMs.
  zpool:
    required: false
    description:
      - ZFS pool the VM's zone dataset will be created in.
requirements:
    - python >= 2.6
'''

EXAMPLES = '''
- name: create SmartOS zone
  vmadm:
    brand: joyent
    state: present
    alias: fw_zone
    image_uuid: 95f265b8-96b2-11e6-9597-972f3af4b6d5
    firewall_enabled: yes
    indestructible_zoneroot: yes
    nics:
      - nic_tag: admin
        ip: dhcp
        primary: true
    internal_metadata:
      root_pw: 'secret'
    quota: 1

- name: Delete a zone
  vmadm:
    alias: test_zone
    state: deleted

- name: Stop all zones
  vmadm:
    uuid: '*'
    state: stopped
'''

RETURN = '''
uuid:
  description: UUID of the managed VM.
  returned: always
  type: string
  sample: 'b217ab0b-cf57-efd8-cd85-958d0b80be33'
alias:
  description: Alias of the managed VM.
  returned: When addressing a VM by alias.
  type: string
  sample: 'dns-zone'
state:
  description: State of the target, after execution.
  returned: success
  type: string
  sample: 'running'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils._text import to_native
import os
import re
import tempfile
import traceback
try:
    import json
except ImportError:
    import simplejson as json

# While vmadm(1M) supports a -E option to return any errors in JSON, the
# generated JSON does not play well with the JSON parsers of Python.
# The returned message contains '\n' as part of the stacktrace,
# which breaks the parsers.


def get_vm_prop(module, uuid, prop):
    # Lookup a property for the given VM.
    # Returns the property, or None if not found.
    cmd = '{0} lookup -j -o {1} uuid={2}'.format(module.vmadm, prop, uuid)

    (rc, stdout, stderr) = module.run_command(cmd)

    if rc != 0:
        module.fail_json(
            msg='Could not perform lookup of {0} on {1}'.format(prop, uuid), exception=stderr)

    try:
        stdout_json = json.loads(stdout)
    except:
        e = get_exception()
        module.fail_json(
            msg='Invalid JSON returned by vmadm for uuid lookup of {0}'.format(alias),
            details=to_native(e))

    if len(stdout_json) > 0 and prop in stdout_json[0]:
        return stdout_json[0][prop]
    else:
        return None


def get_vm_uuid(module, alias):
    # Lookup the uuid that goes with the given alias.
    # Returns the uuid or '' if not found.
    cmd = '{0} lookup -j -o uuid alias={1}'.format(module.vmadm, alias)

    (rc, stdout, stderr) = module.run_command(cmd)

    if rc != 0:
        module.fail_json(
            msg='Could not retrieve UUID of {0}'.format(alias), exception=stderr)

    # If no VM was found matching the given alias, we get back an empty array.
    # That is not an error condition as we might be explicitly checking it's
    # absence.
    if stdout.strip() == '[]':
        return None
    else:
        try:
            stdout_json = json.loads(stdout)
        except:
            e = get_exception()
            module.fail_json(
                msg='Invalid JSON returned by vmadm for uuid lookup of {0}'.format(alias),
                details=to_native(e))

        if len(stdout_json) > 0 and 'uuid' in stdout_json[0]:
            return stdout_json[0]['uuid']


def get_all_vm_uuids(module):
    # Retrieve the UUIDs for all VMs.
    cmd = '{0} lookup -j -o uuid'.format(module.vmadm)

    (rc, stdout, stderr) = module.run_command(cmd)

    if rc != 0:
        module.fail_json(msg='Failed to get VMs list', exception=stderr)

    try:
        stdout_json = json.loads(stdout)
        return [v['uuid'] for v in stdout_json]
    except:
        e = get_exception()
        module.fail_json(msg='Could not retrieve VM UUIDs', details=to_native(e))


def new_vm(module, uuid, vm_state):
    payload_file = create_payload(module, uuid)

    (rc, stdout, stderr) = vmadm_create_vm(module, payload_file)

    if rc != 0:
        changed = False
        module.fail_json(msg='Could not create VM', exception=stderr)
    else:
        changed = True
        # 'vmadm create' returns all output to stderr...
        match = re.match('Successfully created VM (.*)', stderr)
        if match:
            vm_uuid = match.groups()[0]
            if not is_valid_uuid(vm_uuid):
                module.fail_json(msg='Invalid UUID for VM {0}?'.format(vm_uuid))
        else:
            module.fail_json(msg='Could not retrieve UUID of newly created(?) VM')

        # Now that the VM is created, ensure it is in the desired state (if not 'running')
        if vm_state != 'running':
            ret = set_vm_state(module, vm_uuid, vm_state)
            if not ret:
                module.fail_json(msg='Could not set VM {0} to state {1}'.format(vm_uuid, vm_state))

    try:
        os.unlink(payload_file)
    except Exception as e:
        # Since the payload may contain sensitive information, fail hard
        # if we cannot remove the file so the operator knows about it.
        module.fail_json(
            msg='Could not remove temporary JSON payload file {0}'.format(payload_file),
            exception=traceback.format_exc(e))

    return changed, vm_uuid


def vmadm_create_vm(module, payload_file):
    # Create a new VM using the provided payload.
    cmd = '{0} create -f {1}'.format(module.vmadm, payload_file)

    return module.run_command(cmd)


def set_vm_state(module, vm_uuid, vm_state):
    p = module.params

    # Check if the VM is already in the desired state.
    state = get_vm_prop(module, vm_uuid, 'state')
    if state and (state == vm_state):
        return None

    # Lookup table for the state to be in, and which command to use for that.
    # vm_state: [vmadm commandm, forceable?]
    cmds = {
        'stopped': ['stop', True],
        'running': ['start', False],
        'deleted': ['delete', True],
        'rebooted': ['reboot', False]
    }

    if p['force'] and cmds[vm_state][1]:
        force = '-F'
    else:
        force = ''

    cmd = 'vmadm {0} {1} {2}'.format(cmds[vm_state][0], force, vm_uuid)

    (rc, stdout, stderr) = module.run_command(cmd)

    match = re.match('^Successfully.*', stderr)
    if match:
        return True
    else:
        return False


def create_payload(module, uuid):
    # Create the JSON payload (vmdef) and return the filename.

    p = module.params

    # Filter out the few options that are not valid VM properties.
    module_options = ['debug', 'force', 'state']
    vmattrs = filter(lambda prop: prop not in module_options, p)

    vmdef = {}

    for attr in vmattrs:
        if p[attr]:
            vmdef[attr] = p[attr]

    try:
        vmdef_json = json.dumps(vmdef)
    except Exception as e:
        module.fail_json(
            msg='Could not create valid JSON payload', exception=traceback.format_exc(e))

    # Create the temporary file that contains our payload, and set tight
    # permissions for it may container sensitive information.
    try:
        # XXX: When there's a way to get the current ansible temporary directory
        # drop the mkstemp call and rely on ANSIBLE_KEEP_REMOTE_FILES to retain
        # the payload (thus removing the `save_payload` option).
        fname = tempfile.mkstemp()[1]
        fh = open(fname, 'w')
        os.chmod(fname, 0o400)
        fh.write(vmdef_json)
        fh.close()
    except Exception as e:
        module.fail_json(
            msg='Could not save JSON payload', exception=traceback.format_exc(e))

    return fname

def vm_state_transition(module, uuid, vm_state):
    ret = set_vm_state(module, uuid, vm_state)

    # Whether the VM changed state.
    if ret is None:
        return False
    elif ret:
        return True
    else:
        module.fail_json(msg='Failed to set VM {0} to state {1}'.format(uuid, vm_state))


def is_valid_uuid(uuid):
    if re.match('^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$', uuid, re.IGNORECASE):
        return True
    else:
        return False


def validate_uuids(module):
    # Perform basic UUID validation.
    failed = []

    for u in [['uuid', module.params['uuid']],
              ['image_uuid', module.params['image_uuid']]]:
        if u[1] and u[1] != '*':
            if not is_valid_uuid(u[1]):
                failed.append(u[0])

    if len(failed) > 0:
        module.fail_json(msg='No valid UUID(s) found for: {0}'.format(", ".join(failed)))


def manage_all_vms(module, vm_state):
    # Handle operations for all VMs, which can by definition only
    # be state transitions.
    state = module.params['state']

    if state == 'created':
        module.fail_json(msg='State "created" is only valid for tasks with a single VM')

    # If any of the VMs has a change, the task as a whole has a change.
    any_changed = False

    # First get all VM uuids and for each check their state, and adjust it if needed.
    for uuid in get_all_vm_uuids(module):
        current_vm_state = get_vm_prop(module, uuid, 'state')
        if not current_vm_state and vm_state == 'deleted':
            any_changed = False
        else:
            if module.check_mode:
                if (not current_vm_state) or (get_vm_prop(module, uuid, 'state') != state):
                    any_changed = True
            else:
                any_changed = (vm_state_transition(module, uuid, vm_state) | any_changed)

    return any_changed


def main():
    # In order to reduce the clutter and boilerplate for trivial options,
    # abstract the vmadm properties and build the dict of arguments later.
    # Dict of all options that are simple to define based on their type.
    # They're not required and have a default of None.
    properties = {
        'str': [
            'disk_driver', 'dns_domain', 'fs_allowed', 'hostname', 'image_uuid',
            'kernel_version', 'nic_driver', 'qemu_extra_opts', 'uuid', 'zpool'
        ],
        'bool': [
            'autoboot', 'debug', 'delegate_dataset', 'firewall_enabled',
            'force', 'indestructible_zoneroot', 'maintain_resolvers',
        ],
        'int': [
            'cpu_cap', 'cpu_shares', 'max_physical_memory', 'max_swap',
            'quota', 'ram', 'vcpus', 'vnc_port', 'zfs_io_priority',
        ],
        'dict': ['customer_metadata', 'internal_metadata'],
        'list': ['disks', 'nics', 'resolvers', 'filesystems']
    }

    # Start with the options that are not as trivial as those above.
    options = dict(
        state=dict(
            default='running',
            type='str',
            choices=['present', 'running', 'absent', 'deleted', 'stopped', 'created', 'restarted', 'rebooted']
        ),
        name=dict(
            default=None, type='str',
            aliases=['alias']
        ),
        brand=dict(
            default='joyent',
            type='str',
            choices=['joyent', 'joyent-minimal', 'kvm', 'lx']
        ),
    )

    # Add our 'simple' options to options dict.
    for type in properties:
        for p in properties[type]:
            option = dict(default=None, type=type)
            options[p] = option

    module = AnsibleModule(
        argument_spec=options,
        supports_check_mode=True,
        required_one_of=[['name', 'uuid']]
    )

    module.vmadm = module.get_bin_path('vmadm', required=True)

    p = module.params
    uuid = p['uuid']
    state = p['state']

    # Translate the state paramter into something we can use later on.
    if state in ['present', 'running']:
        vm_state = 'running'
    elif state in ['stopped', 'created']:
        vm_state = 'stopped'
    elif state in ['absent', 'deleted']:
        vm_state = 'deleted'
    elif state in ['restarted', 'rebooted']:
        vm_state = 'rebooted'

    result = {'state': state}

    # While it's possible to refer to a given VM by it's `alias`, it's easier
    # to operate on VMs by their UUID. So if we're not given a `uuid`, look
    # it up.
    if not uuid:
        uuid = get_vm_uuid(module, p['name'])
        # Bit of a chicken and egg problem here for VMs with state == deleted.
        # If they're going to be removed in this play, we have to lookup the
        # uuid. If they're already deleted there's nothing to looup.
        # So if state == deleted and get_vm_uuid() returned '', the VM is already
        # deleted and there's nothing else to do.
        if uuid is None and vm_state == 'deleted':
            result['name'] = p['name']
            module.exit_json(**result)

    validate_uuids(module)

    if p['name']:
        result['name'] = p['name']
    result['uuid'] = uuid

    if uuid == '*':
        result['changed'] = manage_all_vms(module, vm_state)
        module.exit_json(**result)

    # The general flow is as follows:
    # - first the current state of the VM is obtained by it's UUID.
    # - If the state was not found and the desired state is 'deleted', return.
    # - If the state was not found, it means the VM has to be created.
    #   Subsequently the VM will be set to the desired state (i.e. stopped)
    # - Otherwise, it means the VM exists already and we operate on it's
    #   state (i.e. reboot it.)
    #
    # In the future it should be possible to query the VM for a particular
    # property as a valid state (i.e. queried) so the result can be
    # registered.
    # Also, VMs should be able to get their properties updated.
    # Managing VM snapshots should be part of a standalone module.

    # First obtain the VM state to determine what needs to be done with it.
    current_vm_state = get_vm_prop(module, uuid, 'state')

    # First handle the case where the VM should be deleted and is not present.
    if not current_vm_state and vm_state == 'deleted':
        result['changed'] = False
    elif module.check_mode:
        # Shortcut for check mode, if there is no VM yet, it will need to be created.
        # Or, if the VM is not in the desired state yet, it needs to transition.
        if (not current_vm_state) or (get_vm_prop(module, uuid, 'state') != state):
            result['changed'] = True
        else:
            result['changed'] = False

        module.exit_json(**result)
    # No VM was found that matched the given ID (alias or uuid), so we create it.
    elif not current_vm_state:
        result['changed'], result['uuid'] = new_vm(module, uuid, vm_state)
    else:
        # VM was found, operate on its state directly.
        result['changed'] = vm_state_transition(module, uuid, vm_state)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
