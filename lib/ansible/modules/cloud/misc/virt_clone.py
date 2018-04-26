#!/usr/bin/python
# -*- coding: utf-8 -*-

# Larry Smith Jr. <mrlesmithjr@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Requirements:
# libvirt-python
# OSX: brew install libvirt, pip install libvirt-python
# Debian: apt-get install libvirt-python
# python-virtinst
# Debian: apt-get install python-virtinst

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
author: Larry Smith Jr. (@mrlesmithjr)
module: virt_clone
short_description: Clones VMs from templates
description:
  - "This module creates clones for libvirt."
version_added: "2.6"
options:
  auto:
    default: true
    description:
        - Generates a new guest name, and paths for new storage - default true
  mac:
    description:
        - Allows a pre-defined MAC address to be assigned to the cloned VM
  name:
    aliases: [ "dest", "guest" ]
    description:
        - The VM to create
    required: true
  template:
    aliases: [ "src" ]
    description:
        - The VM to use as the source (template)
    required: true
  state:
    choices: [ "present", "started" ]
    default: present
    description:
        - If the clone should be present or started - default present
    required: false
  uuid:
    description:
        - Allows a static UUID to be defined for the VM when cloning
    required: false
'''

RETURN = ''' # '''

EXAMPLES = '''
- name:       Cloning a VM
  virt_clone:
    name:     web01
    state:    started
    template: ubuntu1604-packer-template
  become:     true
- name:       Cloning a VM with MAC address defined
  virt_clone:
    mac:      "52:54:00:34:11:54"
    name:     web01
    state:    started
    template: ubuntu1604-packer-template
  become:     true
- name:       Cloning a VM with UUID defined
  virt_clone:
    name:     web01
    state:    started
    template: ubuntu1604-packer-template
    uuid:     c9e58ffc-e1e4-4fc5-a383-818bdceecf4d
  become:     true
'''

try:
    import libvirt
except ImportError:
    HAS_VIRT = False
else:
    HAS_VIRT = True

from ansible.module_utils.basic import AnsibleModule


def main():

    module = AnsibleModule(
        argument_spec=dict(
            auto=dict(type='str', default=True),
            mac=dict(type='str'),
            name=dict(type='str', aliases=['dest', 'guest'], required=True),
            state=dict(type='str', choices=[
                'present', 'started'], default='present'),
            template=dict(type='str', aliases=['src'], required=True),
            uuid=dict(type='str')
        ),
        supports_check_mode=True,
    )

    if not HAS_VIRT:
        module.fail_json(
            msg="Python module `libvirt` is missing. See requirements.")

    # changed = False
    virt_clone = module.get_bin_path('virt-clone', True)
    dest = module.params['name']
    src = module.params['template']

    conn = libvirt.open('qemu:///system')
    domains = conn.listAllDomains(0)

    vms = []
    if domains:
        for domain in domains:
            vms.append(domain.name())

    if src not in vms:
        module.fail_json(msg="The source(template) `%s` does not exist!" % src)

    if (module.params['state'] == 'present' or
            module.params['state'] == 'started'):
        if dest not in vms:
            if not module.check_mode:
                virt_clone_params = ""
                if module.params['auto']:
                    virt_clone_params = virt_clone_params + " --auto-clone"
                if module.params['mac']:
                    mac = module.params['mac']
                    virt_clone_params = virt_clone_params + " --mac=%s" % mac
                if module.params['uuid']:
                    uuid = module.params['uuid']
                    virt_clone_params = virt_clone_params + " --uuid=%s" % uuid
                module.run_command(
                    '%s --original=%s --name=%s %s' % (
                        virt_clone, src, dest, virt_clone_params),
                    check_rc=True)
                if module.params['state'] == 'started':
                    domain = conn.lookupByName(dest)
                    domain.create()
                changed = True
            else:
                changed = True
        else:
            changed = False

    conn.close()

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
