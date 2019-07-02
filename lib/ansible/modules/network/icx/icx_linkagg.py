from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = """
---
module: icx_linkagg
version_added: "2.7"
author: "Ruckus: https://support.ruckuswireless.com/contact-us"
short_description: Manage link aggregation groups on Ruckus ICX 7000 series switches
description:
  - This module provides declarative management of link aggregation groups
    on Ruckus ICX network devices.
options:
  group:
    description:
      - Channel-group number for the port-channel
        Link aggregation group. Range 1-255 or set to 'auto' to auto-generates a LAG ID
  name:
    description:
      - Name of the LAG
  mode:
    description:
      - Mode of the link aggregation group.
    choices: ['dynamic', 'static']
  members:
    description:
      - List of port members or ranges of the link aggregation group.
  aggregate:
    description: List of link aggregation definitions.
  state:
    description:
      - State of the link aggregation group.
    default: present
    choices: ['present', 'absent']
  purge:
    description:
      - Purge links not defined in the I(aggregate) parameter.
    type: bool
    default: false
  check_running_config:
    description:
      - Check running configuration. This can be set as environment variable. Module will use environment variable value(default:True), unless it is overriden, by specifying it as module parameter.
    type: bool
    default: As set in environment variable
"""

EXAMPLES = """
- name: create static link aggregation group
  icx_linkagg:
    group: 10
    mode: static
    name: LAG1

- name: create link aggregation group with auto id
  icx_linkagg:
    group: auto
    mode: dynamic
    name: LAG2

- name: delete link aggregation group
  icx_linkagg:
    group: 10
    state: absent

- name: Set members to LAG
  icx_linkagg:
    group: 200
    mode: static
    members:
      - ethernet 1/1/1 to 1/1/6
      - ethernet 1/1/10

- name: Remove links other then LAG id 100 and 3 using purge
  icx_linkagg:
    aggregate:
      - { group: 3}
      - { group: 100}
    purge: true
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - lag LAG1 dynamic id 11
    - ports ethernet 1/1/1 to 1/1/6
    - no ports ethernet 1/1/10
    - no lag LAG1 dynamic id 12
"""


import re
from copy import deepcopy

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import ConnectionError,exec_command
from ansible.module_utils.network.icx.icx import run_commands, get_config, load_config
from ansible.module_utils.network.common.config import CustomNetworkConfig
from ansible.module_utils.network.common.utils import remove_default_spec

def range_to_members(ranges,prefix=""):
  match = re.findall(r'(ethe[a-z]* [0-9]/[0-9]/[0-9]+)( to [0-9]/[0-9]/[0-9]+)?', ranges)
  members = list()
  for m in match:
      start,end = m
      if(end==''):
        start = start.replace("ethe ","ethernet ")
        members.append("%s%s"%(prefix,start))
      else:
          start_tmp = re.search(r'[0-9]/[0-9]/([0-9]+)',start)
          end_tmp = re.search(r'[0-9]/[0-9]/([0-9]+)',end)
          start = int(start_tmp.group(1))
          end = int(end_tmp.group(1))+1
          for num in range(start, end):
              members.append("%sethernet 1/1/%s"%(prefix,num))
  return members


def map_config_to_obj(module):
    objs = dict()
    compare=module.params['check_running_config']
    config = get_config(module,None,compare=compare)
    obj = None
    for line in config.split('\n'):
        l = line.strip()
        match1 = re.search(r'lag (\S+) (\S+) id (\S+)', l, re.M)
        if match1:
            obj = dict()
            obj['name'] = match1.group(1)
            obj['mode'] = match1.group(2)
            obj['group'] = match1.group(3)
            obj['state'] = 'present'
            obj['members'] = list()
        else:
            match2 = re.search(r'ports .*', l, re.M)
            if match2 and obj!=None:
                # if(obj.get('members')==None):
                #     obj['members'] = list()
                obj['members'].extend(range_to_members(match2.group(0)))
            elif obj!=None:
                objs[obj['group']] = obj
                obj = None
    return objs

def map_params_to_obj(module):
    obj = []

    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]
            d = item.copy()
            d['group'] = str(d['group'])
            obj.append(d)
    else:
        obj.append({
            'group': str(module.params['group']),
            'mode': module.params['mode'],
            'members': module.params['members'],
            'state': module.params['state'],
            'name': module.params['name']
        })

    return obj

def search_obj_in_list(group, lst):
    for o in lst:
        if o['group'] == group:
            return o
    return None

def is_member(member,lst):
    for li in lst:
      ml = range_to_members(li)
      if member in ml:
        return True
    return False

def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    purge = module.params['purge']

    for w in want:
        if have == {} and w['state']=='absent':
          commands.append("%slag %s %s id %s"%('no ' if w['state']=='absent' else '', w['name'],w['mode'],w['group']))
        # if(purge==False and (w.get('mode')==None or w.get('group')==None or w.get('name')==None)):  #Arguments check
        #     module.fail_json(msg="arguments named 'group','mode','name' are required.")
        elif have.get(w['group']) == None:
            commands.append("%slag %s %s id %s"%('no ' if w['state']=='absent' else '', w['name'],w['mode'],w['group']))
            if(w.get('members')!=None and w['state']=='present'):
                for m in w['members']:
                    commands.append("ports %s"%( m))
            if w['state']=='present':
              commands.append("exit")
        else:
            # for key in w:
            #     have[w['group']][key] = w[key]
            #w = have[w['group']]
            commands.append("%slag %s %s id %s"%('no ' if w['state']=='absent' else '', w['name'],w['mode'],w['group']))
            if(w.get('members')!=None and w['state']=='present'):
                for m in have[w['group']]['members']:
                  if not is_member(m, w['members']):
                    commands.append("no ports %s"%(m))
                for m in w['members']:
                    sm = range_to_members(ranges=m)
                    for smm in sm:
                      if not smm in have[w['group']]['members']:
                        commands.append("ports %s"%(smm))

            if w['state']=='present':
              commands.append("exit")
    if purge:
        for h in have:
            if search_obj_in_list(have[h]['group'],want) == None:
                commands.append("no lag %s %s id %s"%(have[h]['name'],have[h]['mode'],have[h]['group']))
    return commands

# def check_args(module):
#     if(module.params.get('aggregate')==None and (module.params.get('group') == None or module.params.get('mode')==None or module.params.get('name') == None)):
#         module.fail_json(msg="arguments named 'group','mode','name' are required.")


def main():
    element_spec = dict(
        group=dict(type='int'),
        name=dict(type='str'),
        mode=dict(choices=['dynamic', 'static']),
        members=dict(type='list'),
        state=dict(default='present',
        choices=['present', 'absent']),
        check_running_config=dict(type='bool')
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['group'] = dict(required=True)

    required_one_of = [['group', 'aggregate']]
    #required_together = [['members', 'mode']]
    required_together = [['name', 'group']]
    mutually_exclusive = [['group', 'aggregate']]

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec,
                       required_together=required_together),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    #argument_spec.update(ios_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           required_together=required_together,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    #check_args(module)

    warnings = list()
    result = {'changed': False}
    exec_command(module,'skip')
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands((want, have), module)

    # result["want"] = want
    # result["have"] = have
    result["commands"] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
