#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Michael Tipton <mike () ibeta.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vmware_evc_mode
short_description: Enable/Disable EVC mode on vCenter
description:
    - This module can be used to enable/disable EVC mode on vCenter.
version_added: 2.9
author:
    - Michael Tipton (@castawayegr)
notes:
    - Tested on vSphere 6.7
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
  cluster_name:
    description:
    - The name of the cluster to enable or disable EVC mode on.
    required: True
  evc_mode:
    description:
    - Required for C(state=present). The EVC mode to enable or disable on the cluster. (intel-broadwell, intel-nehalem, intel-merom, etc.).
    required: True
  state:
    description:
    - Add or remove EVC mode.
    choices: [absent, present]
    default: present
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
    - name: Enable EVC Mode
      vmware_evc_mode:
         hostname: "{{ groups['vcsa'][0] }}"
         username: "{{ vcenter_username }}"
         password: "{{ site_password }}"
         cluster_name: "{{ cluster_name }}"
         evc_mode: "intel-broadwell"
         state: present
      delegate_to: localhost
      register: enable_evc

    - name: Disable EVC Mode
      vmware_evc_mode:
         hostname: "{{ groups['vcsa'][0] }}"
         username: "{{ vcenter_username }}"
         password: "{{ site_password }}"
         cluster_name: "{{ cluster_name }}"
         state: absent
      delegate_to: localhost
      register: disable_evc
'''

RETURN = """
result:
    description: information about performed operation
    returned: always
    type: str
    sample: "EVC Mode for 'intel-broadwell' has been enabled."
"""

try:
    from pyVmomi import vim
except ImportError:
    pass


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (connect_to_api, find_cluster_by_name, vmware_argument_spec,
                                         wait_for_task, TaskError)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        cluster_name=dict(type='str', required=True),
        evc_mode=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['cluster_name', 'evc_mode']]
        ]
    )

    state = module.params['state']
    cluster_name = module.params['cluster_name']
    evc_mode = module.params['evc_mode']

    content = connect_to_api(module, False)
    results = dict(changed=False, result=dict())
    cluster = find_cluster_by_name(content, cluster_name)
    evcm = cluster.EvcManager()
    evc_state = evcm.evcState
    current_evc_mode = evc_state.currentEVCModeKey
    supported_evc_modes = evc_state.supportedEVCMode

    if state == 'present' and current_evc_mode != evc_mode:
        try:
            if not module.check_mode:
                evc_task = evcm.ConfigureEvcMode_Task(evc_mode)
                wait_for_task(evc_task)
            results['changed'] = True
            results['result'] = "EVC Mode for '%s' has been enabled." % (evc_mode)
        except TaskError as invalid_argument:
            module.fail_json(msg="Failed to update EVC mode: %s" % to_native(invalid_argument))
    elif state == 'present' and current_evc_mode == evc_mode:
        results['changed'] = False
        results['result'] = "EVC Mode for '%s' is already enabled." % (evc_mode)
    elif state == 'absent' and not current_evc_mode:
        results['changed'] = False
        results['result'] = "EVC Mode for '%s' is already disabled." % (evc_mode)
    elif state == 'absent':
        try:
            if not module.check_mode:
                evc_disable_task = evcm.DisableEvcMode_Task()
                wait_for_task(evc_disable_task)
            results['changed'] = True
            results['result'] = "EVC Mode has been disabled."
        except TaskError as invalid_argument:
            module.fail_json(msg="Failed to disable EVC mode: %s" % to_native(invalid_argument))

    module.exit_json(**results)


if __name__ == '__main__':
    main()
