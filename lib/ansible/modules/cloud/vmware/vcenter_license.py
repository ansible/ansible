#!/usr/bin/python

# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
module: vcenter_license
short_description: Manage VMware vCenter license keys
description:
- Add and delete vCenter license keys.
version_added: '2.4'
author:
- Dag Wieers (@dagwieers)
requirements:
- pyVmomi
options:
  labels:
    description:
    - The optional labels of the license key to manage in vSphere vCenter.
    - This is dictionary with key/value pair.
    default: {
        'source': 'ansible'
    }
  license:
    description:
    - The license key to manage in vSphere vCenter.
    required: yes
  state:
    description:
    -  Whether to add (C(present)) or remove (C(absent)) the license key.
    choices: [absent, present]
    default: present
notes:
- This module will also auto-assign the current vCenter to the license key
  if the product matches the license key, and vCenter us currently assigned
  an evaluation license only.
- The evaluation license (00000-00000-00000-00000-00000) is not listed
  when unused.
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Add a new vCenter license
  vcenter_license:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    license: f600d-21ae3-5592b-249e0-cc341
    state: present
  delegate_to: localhost

- name: Remove an (unused) vCenter license
  vcenter_license:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    license: f600d-21ae3-5592b-249e0-cc341
    state: absent
  delegate_to: localhost
'''

RETURN = r'''
licenses:
    description: list of license keys after module executed
    returned: always
    type: list
    sample:
    - f600d-21ae3-5592b-249e0-cc341
    - 143cc-0e942-b2955-3ea12-d006f
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import connect_to_api, vmware_argument_spec


def find_key(licenses, license):
    for item in licenses:
        if item.licenseKey == license:
            return item
    return None


def list_keys(licenses):
    keys = []
    for item in licenses:
        # Filter out evaluation license key
        if item.used is None:
            continue
        keys.append(item.licenseKey)
    return keys


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        labels=dict(type='dict', default=dict(source='ansible')),
        license=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    license = module.params['license']
    state = module.params['state']

    # FIXME: This does not seem to work on vCenter v6.0
    labels = []
    for k in module.params['labels']:
        kv = vim.KeyValue()
        kv.key = k
        kv.value = module.params['labels'][k]
        labels.append(kv)

    result = dict(
        changed=False,
        diff=dict(),
    )

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    content = connect_to_api(module)
    lm = content.licenseManager

    result['licenses'] = list_keys(lm.licenses)
    if module._diff:
        result['diff']['before'] = '\n'.join(result['licenses']) + '\n'

    if state == 'present' and license not in result['licenses']:

        result['changed'] = True
        if module.check_mode:
            result['licenses'].append(license)
        else:
            lm.AddLicense(license, labels)

            # Automatically assign to current vCenter, if needed
            key = find_key(lm.licenses, license)
            if content.about.name in key.name:
                try:
                    lam = lm.licenseAssignmentManager
                    lam.UpdateAssignedLicense(entity=content.about.instanceUuid, licenseKey=license)
                except:
                    module.warn('Could not assign "%s" (%s) to vCenter.' % (license, key.name))

            result['licenses'] = list_keys(lm.licenses)
        if module._diff:
            result['diff']['after'] = '\n'.join(result['licenses']) + '\n'

    elif state == 'absent' and license in result['licenses']:

        # Check if key is in use
        key = find_key(lm.licenses, license)
        if key.used > 0:
            module.fail_json(msg='Cannot remove key "%s", still in use %s time(s).' % (license, key.used))

        result['changed'] = True
        if module.check_mode:
            result['licenses'].remove(license)
        else:
            lm.RemoveLicense(license)
            result['licenses'] = list_keys(lm.licenses)
        if module._diff:
            result['diff']['after'] = '\n'.join(result['licenses']) + '\n'

    module.exit_json(**result)


if __name__ == '__main__':
    main()
