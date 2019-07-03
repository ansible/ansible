#!/usr/bin/python
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {"metadata_version": "1.1",
                    "status": ["preview"],
                    "supported_by": "community"}

DOCUMENTATION = '''
---
module: lvm

short_description: Create, remove, modify LVM devices

version_added: "2.9"

description:
    - "Module utilizes Logical Volume Management (LVM) to create, modify or
      remove LVM layers."

options:
    devices:
        description:
            - "List of devices (e.g. C(/dev/vda1)) to work with."
        type: list
    state:
        description:
            - "Desired state of all of the the LVM layers."
            - "Cannot be used together with pv, vg, or lv I(state)."
            - "However it can be used with other pv, vg, or lv suboptions"
        type: str
        choices: [present, absent]
    pv:
        description:
            - "Suboption for more refined control over Physical Volumes (PV)."
        suboptions:
            state:
                description:
                    - "Desired state of PV"
                    - "When removing PV (I(state=absent)), the higher layers
                      (e.g. VG or LV) have to be removed first.
                      The module tries to do that automatically but having
                      contradicting states of these layers
                      (e.g. I(vg.state=present)) will lead to failure."
                type: str
                choices: [present, absent]
        type: dict
    vg:
        description:
            - "Suboption for more refined control over Volume Groups (VG)."
        suboptions:
              state:
                  description:
                      - "Desired state of VG"
                      - "When removing a VG (I(state=absent)), the higher layers
                        (e.g. LV) have to be removed first.
                        Module tries to do that automatically but having
                        contradicting states of these layers
                        (e.g. I(lv.state=present)) will fail."
                      - "When creating a VG (I(state=present)), the lower layers
                        (e.g. PV) have to be created first.
                        The module tries to do that automatically but having
                        contradicting states of these layers
                        (e.g. I(pv.state=absent)) will lead to failure."
                  type: str
                  choices: [present, absent]
              name:
                  description:
                      - "Name of the VG."
                      - "When I(state=present), the module will look for
                        existing VG with this name. If not found, it will be created."
                      - "When I(state=absent), the module will try to remove VG
                        with this name. If not found, it will do nothing."
                  type: str
        type: dict
    lv:
        description:
            - "Suboption for more refined control over Logical Volumes (LV)."
        suboptions:
              state:
                  description:
                      - "Desired state of LV"
                  type: str
                  choices: [present, absent]
              name:
                  description:
                      - "Name of the LV."
                      - "When I(state=present), the module will look for
                        existing LV with this name. If not found, it will be created."
                      - "When I(state=absent), the module will try to remove LV
                        with this name. If not found, it will do nothing."
                  type: str
        type: dict

requirements:
    - "libblockdev"
    - "libblockdev-lvm"
    - "gobject-introspection"

author:
    Jan Pokorny (@japokorn)"

'''

EXAMPLES = '''
- name: create PV, VG and LV over vda1 and vdb1 devices
  lvm:
    devices:
      - /dev/vda1
      - /dev/vdb1
    state: present

- name: create PV, VG and LV over vda1 and vdb1 devices
  lvm:
    devices:
      - /dev/vda1
      - /dev/vdb1

    pv:
      state: present
    vg:
      name: vg1
      state: present
    lv:
      name: lv1
      state: present

- name: remove VG named "vg_00" (LV will be removed as well if present)
  lvm:
    devices:
      - /dev/vda1
      - /dev/vdb1

    vg:
      name: vg_00
      state: absent

'''

RETURN = '''
layer_execution:
    description: "List of results of individual LVM layers."
    returned: success
    type: dict
    sample: "{'lv': {'changed': 1, 'lv_name': 'lv_00'},
              'pv': {'changed': 1},
              'vg': {'changed': 1, 'vg_name': 'vg_00'}}"

layer_execution_order:
    description: "Order in which LVM layers was called."
    returned: success
    type: list
    sample: "['pv', 'vg', 'lv']"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.storage.lvm import pv, vg, lv


class LVM_Layer(object):
    ''' Virtual class. Not to be created directly.
        It contains class variable that serves its offsprings
    '''

    suggested_states = {}
    args = {}

    def __init__(self):
        self.layer_name = None
        self.module = None
        self.priorities = {}
        self.desired_state = None

    @property
    def priority(self):
        return self.priorities.get(self.desired_state, None)

    def check_suggested(self, layer, value):
        ''' Verify that suggested value for LVM layer is valid
        '''
        existing_value = LVM_Layer.suggested_states.get(layer, None)

        if existing_value is not None and existing_value != value:
            # having opposite suggested values means invalid input values combination
            raise ValueError('invalid combination of states')

    def mark_suggested(self, layer, value):
        ''' Mark value for LVM layer as suggested
        '''
        self.check_suggested(layer, value)
        LVM_Layer.suggested_states[layer] = value

    def run(self, args):
        return self.module.run(self.get_module_args(args))


class PV_Layer(LVM_Layer):

    def __init__(self):
        super(PV_Layer, self).__init__()
        self.layer_name = 'pv'
        self.module = pv
        self.priorities = {'present': 1000, 'absent': 100}

    def __getitem__(self, arg):
        return self.args['pv'][arg]

    def get_module_args(self, module_results):
        ''' Produce arguments for the corresponding layer
        '''
        # module_results argument is needed only for compatibility reasons
        result = {'state': None,
                  'devices': None}
        if self.desired_state is not None:
            result['state'] = self.desired_state

        if self.args['devices'] is not None:
            result['devices'] = self.args['devices']

        return result

    def resolve_desired_state(self):
        ''' Based on given arguments decide what is the desired state
            of this LVM layer. Has to be run twice for each layer.
            First run mainly provides data to other layers and
            provides only incomplete solution.
            The result is stored in self.desired_state.
        '''

        self.desired_state = self.args['pv']['state']
        if self.desired_state is None:
            self.desired_state = LVM_Layer.suggested_states.get('pv')

        if self.args['pv']['state'] == 'absent':
            self.desired_state = 'absent'
            self.mark_suggested('vg', 'absent')
            self.mark_suggested('lv', 'absent')
        self.check_suggested('pv', self.desired_state)


class VG_Layer(LVM_Layer):

    def __init__(self):
        super(VG_Layer, self).__init__()
        self.layer_name = 'vg'
        self.module = vg
        self.priorities = {'present': 500, 'absent': 500}

    def __getitem__(self, arg):
        return self.args['vg'][arg]

    def get_module_args(self, module_results):
        ''' Produce arguments for the corresponding layer
        '''
        result = {'state': None,
                  'pvs': None,
                  'name': None}

        if self.desired_state is not None:
            result['state'] = self.desired_state

        if self.args['devices'] is not None:
            result['pvs'] = self.args['devices']

        if self.args['vg']['name'] is not None:
            result['name'] = self.args['vg']['name']

        return result

    def resolve_desired_state(self):
        ''' Based on given arguments decide what is the desired state
            of this LVM layer. Has to be run twice for each layer.
            First run mainly provides data to other layers and
            provides only incomplete solution.
            The result is stored in self.desired_state.
        '''

        self.desired_state = self.args['vg']['state']
        if self.desired_state is None:
            self.desired_state = LVM_Layer.suggested_states.get('vg')

        if self.args['vg']['state'] == 'present':
            self.mark_suggested('pv', 'present')
        if self.args['vg']['state'] == 'absent':
            self.mark_suggested('lv', 'absent')

        self.check_suggested('vg', self.desired_state)


class LV_Layer(LVM_Layer):

    def __init__(self):
        super(LV_Layer, self).__init__()
        self.layer_name = 'lv'
        self.module = lv
        self.priorities = {'present': 100, 'absent': 1000}

    def __getitem__(self, arg):
        return self.args['lv'][arg]

    def get_module_args(self, module_results):
        ''' Produce arguments for the corresponding layer
        '''
        result = {'state': None,
                  'vg_name': None,
                  'lv_name': None}
        if self.desired_state is not None:
            result['state'] = self.desired_state

        # get VG name from arguments if possible
        if self.args['vg']['name'] is not None:
            result['vg_name'] = self.args['vg']['name']

        # VG name can be also present in the VG module results
        if 'vg' in module_results:
            result['vg_name'] = module_results['vg']['vg_name']

        if self.args['lv']['name'] is not None:
            result['lv_name'] = self.args['lv']['name']

        return result

    def resolve_desired_state(self):
        ''' Based on given arguments decide what is the desired state
            of this LVM layer. Has to be run twice for each layer.
            First run mainly provides data to other layers and
            provides only incomplete solution.
            The result is stored in self.desired_state.
        '''

        self.desired_state = self.args['lv']['state']
        if self.desired_state is None:
            self.desired_state = LVM_Layer.suggested_states.get('lv')

        if self.args['lv']['state'] == 'present':
            self.mark_suggested('pv', 'present')
            self.mark_suggested('vg', 'present')

        self.check_suggested('lv', self.desired_state)


def process_module_arguments(args):
    ''' Return complete arguments dictionary
        Create missing empty arguments for the structure
        Make it safe to use
    '''

    args_dict = {'devices': args.get('devices', None),
                 'state': args.get('state', None),
                 'pv': {'state': None},
                 'vg': {'state': None, 'name': None},
                 'lv': {'state': None, 'name': None}}

    if args.get('pv', None) is not None:
        args_dict['pv']['state'] = args['pv'].get('state', None)

    if args.get('vg', None) is not None:
        args_dict['vg']['state'] = args['vg'].get('state', None)
        args_dict['vg']['name'] = args['vg'].get('name', None)

    if args.get('lv', None) is not None:
        args_dict['lv']['state'] = args['lv'].get('state', None)
        args_dict['lv']['name'] = args['lv'].get('name', None)

    return args_dict


def run_module():

    # available arguments/parameters that a user can pass
    module_args = dict(
        devices=dict(type="list",
                     required=True),
        state=dict(type="str",
                   choices=["present", "absent"],
                   required=False),
        pv=dict(type="dict",
                     required=False),
        vg=dict(type="dict",
                     required=False),
        lv=dict(type="dict",
                     required=False)
    )

    module = AnsibleModule(argument_spec=module_args,
                           supports_check_mode=False)

    # seed the result dict in the object
    result = dict(
        changed=False,
        module_execution={}
    )

    # process arguments to be complete and safe to use
    args = process_module_arguments(module.params)

    LVM_Layer.args = args

    layers = [
        PV_Layer(),
        VG_Layer(),
        LV_Layer()]

    if LVM_Layer.args['state'] is not None:
        # if state was specified, all layers should be of that state
        for layer in layers:
            if layer['state'] is not None:
                module.fail_json(msg='combined usage of lvm.state and %s.state' % layer.layer_name)
            layer.desired_state = LVM_Layer.args['state']
    else:
        # LVM_Layer.args['state'] was not specified
        # resolve desired state for each layer
        try:
            for i in range(2):
                # resolve_desired_states function works incrementally:
                # each run provides some data but it takes two runs
                # of each function to gather them all
                for layer in layers:
                    layer.resolve_desired_state()
        except ValueError as e:
            module.fail_json(msg=e)

    # get layers ordered by priority; remove layers with priority=None
    ordered_layers = [x for x in layers if x.priority is not None]
    ordered_layers = sorted(ordered_layers, key=lambda x: x.priority, reverse=True)

    module_results = {}

    for layer in ordered_layers:
        if not layer.has_gi():
            module.fail_json(msg='Could not import gi (GObject Introspection)')

        try:
            module_results[layer.layer_name] = layer.run(module_results)
        except (OSError, ValueError) as e:
            module.fail_json(msg=e)

    for mod_name, mod_result in module_results.items():
        result['layer_execution'][mod_name] = mod_result
        if 'failed' in mod_result:
            result['failed'] = True
            result['msg'] = mod_result['msg']
            break
        if mod_result['changed']:
            result['changed'] = True

    result['layer_execution_order'] = [x.layer_name for x in ordered_layers]

    # Success - return result
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
