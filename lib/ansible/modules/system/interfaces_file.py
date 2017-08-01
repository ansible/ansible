#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, Roman Belyakovsky <ihryamzik () gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: interfaces_file
short_description: Tweak settings in /etc/network/interfaces files
extends_documentation_fragment: files
description:
     - Manage (add, remove, change) individual interface options in an interfaces-style file without having
       to manage the file as a whole with, say, M(template) or M(assemble). Interface has to be presented in a file.
     - Read information about interfaces from interfaces-styled files
version_added: "2.4"
options:
  dest:
    description:
      - Path to the interfaces file
    required: false
    default: /etc/network/interfaces
  iface:
    description:
      - Name of the interface, required for value changes or option remove
    required: false
    default: null
  option:
    description:
      - Name of the option, required for value changes or option remove
    required: false
    default: null
  value:
    description:
      - If I(option) is not presented for the I(interface) and I(state) is C(present) option will be added.
        If I(option) already exists and is not C(pre-up), C(up), C(post-up) or C(down), it's value will be updated.
        C(pre-up), C(up), C(post-up) and C(down) options can't be updated, only adding new options, removing existing
        ones or cleaning the whole option set are supported
    required: false
    default: null
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  state:
    description:
      - If set to C(absent) the option or section will be removed if present instead of created.
    required: false
    default: "present"
    choices: [ "present", "absent" ]

notes:
   - If option is defined multiple times last one will be updated but all will be deleted in case of an absent state
requirements: []
author: "Roman Belyakovsky (@hryamzik)"
'''

RETURN = '''
dest:
    description: destination file/path
    returned: success
    type: string
    sample: "/etc/network/interfaces"
ifaces:
    description: interfaces dictionary
    returned: success
    type: complex
    contains:
      ifaces:
        description: interface dictionary
        returned: success
        type: dictionary
        contains:
          eth0:
            description: Name of the interface
            returned: success
            type: dictionary
            contains:
              address_family:
                description: interface address family
                returned: success
                type: string
                sample: "inet"
              method:
                description: interface method
                returned: success
                type: string
                sample: "manual"
              mtu:
                description: other options, all values returned as strings
                returned: success
                type: string
                sample: "1500"
              pre-up:
                description: list of C(pre-up) scripts
                returned: success
                type: list
                sample:
                  - "route add -net 10.10.10.0/24 gw 10.10.10.1 dev eth1"
                  - "route add -net 10.10.11.0/24 gw 10.10.11.1 dev eth2"
              up:
                description: list of C(up) scripts
                returned: success
                type: list
                sample:
                  - "route add -net 10.10.10.0/24 gw 10.10.10.1 dev eth1"
                  - "route add -net 10.10.11.0/24 gw 10.10.11.1 dev eth2"
              post-up:
                description: list of C(post-up) scripts
                returned: success
                type: list
                sample:
                  - "route add -net 10.10.10.0/24 gw 10.10.10.1 dev eth1"
                  - "route add -net 10.10.11.0/24 gw 10.10.11.1 dev eth2"
              down:
                description: list of C(down) scripts
                returned: success
                type: list
                sample:
                  - "route del -net 10.10.10.0/24 gw 10.10.10.1 dev eth1"
                  - "route del -net 10.10.11.0/24 gw 10.10.11.1 dev eth2"
...
'''

EXAMPLES = '''
# Set eth1 mtu configuration value to 8000
- interfaces_file:
    dest: /etc/network/interfaces.d/eth1.cfg
    iface: eth1
    option: mtu
    value: 8000
    backup: yes
    state: present
  register: eth1_cfg
'''

import os
import re
import tempfile

from ansible.module_utils.basic import AnsibleModule


def lineDict(line):
    return {'line': line, 'line_type': 'unknown'}


def optionDict(line, iface, option, value):
    return {'line': line, 'iface': iface, 'option': option, 'value': value, 'line_type': 'option'}


def getValueFromLine(s):
    spaceRe = re.compile('\s+')
    for m in spaceRe.finditer(s):
        pass
    valueEnd = m.start()
    option = s.split()[0]
    optionStart = s.find(option)
    optionLen = len(option)
    valueStart = re.search('\s', s[optionLen + optionStart:]).end() + optionLen + optionStart
    return s[valueStart:valueEnd]


def read_interfaces_file(module, filename):
    f = open(filename, 'r')
    return read_interfaces_lines(module, f)


def read_interfaces_lines(module, line_strings):
    lines = []
    ifaces = {}
    currently_processing = None
    i = 0
    for line in line_strings:
        i += 1
        words = line.split()
        if len(words) < 1:
            lines.append(lineDict(line))
            continue
        if words[0][0] == "#":
            lines.append(lineDict(line))
            continue
        if words[0] == "mapping":
            # currmap = calloc(1, sizeof *currmap);
            lines.append(lineDict(line))
            currently_processing = "MAPPING"
        elif words[0] == "source":
            lines.append(lineDict(line))
            currently_processing = "NONE"
        elif words[0] == "source-dir":
            lines.append(lineDict(line))
            currently_processing = "NONE"
        elif words[0] == "iface":
            currif = {
                "pre-up": [],
                "up": [],
                "down": [],
                "post-up": []
            }
            iface_name, address_family_name, method_name = words[1:4]
            if len(words) != 4:
                module.fail_json(msg="Incorrect number of parameters (%d) in line %d, must be exectly 3" % (len(words), i))
                # TODO: put line and count parameters
                return None, None

            currif['address_family'] = address_family_name
            currif['method'] = method_name

            ifaces[iface_name] = currif
            lines.append({'line': line, 'iface': iface_name, 'line_type': 'iface', 'params': currif})
            currently_processing = "IFACE"
        elif words[0] == "auto":
            lines.append(lineDict(line))
            currently_processing = "NONE"
        elif words[0] == "allow-":
            lines.append(lineDict(line))
            currently_processing = "NONE"
        elif words[0] == "no-auto-down":
            lines.append(lineDict(line))
            currently_processing = "NONE"
        elif words[0] == "no-scripts":
            lines.append(lineDict(line))
            currently_processing = "NONE"
        else:
            if currently_processing == "IFACE":
                option_name = words[0]
                # TODO: if option_name in currif.options
                value = getValueFromLine(line)
                lines.append(optionDict(line, iface_name, option_name, value))
                if option_name in ["pre-up", "up", "down", "post-up"]:
                    currif[option_name].append(value)
                else:
                    currif[option_name] = value
            elif currently_processing == "MAPPING":
                lines.append(lineDict(line))
            elif currently_processing == "NONE":
                lines.append(lineDict(line))
            else:
                module.fail_json(msg="misplaced option %s in line %d" % (line, i))
                return None, None
    return lines, ifaces


def setInterfaceOption(module, lines, iface, option, raw_value, state):
    value = str(raw_value)
    changed = False

    iface_lines = [item for item in lines if "iface" in item and item["iface"] == iface]

    if len(iface_lines) < 1:
        # interface not found
        module.fail_json(msg="Error: interface %s not found" % iface)
        return changed

    iface_options = list(filter(lambda i: i['line_type'] == 'option', iface_lines))
    target_options = list(filter(lambda i: i['option'] == option, iface_options))

    if state == "present":
        if len(target_options) < 1:
            changed = True
            # add new option
            last_line_dict = iface_lines[-1]
            lines = addOptionAfterLine(option, value, iface, lines, last_line_dict, iface_options)
        else:
            if option in ["pre-up", "up", "down", "post-up"]:
                if len(list(filter(lambda i: i['value'] == value, target_options))) < 1:
                    changed = True
                    lines = addOptionAfterLine(option, value, iface, lines, target_options[-1], iface_options)
            else:
                # if more than one option found edit the last one
                if target_options[-1]['value'] != value:
                    changed = True
                    target_option = target_options[-1]
                    old_line = target_option['line']
                    old_value = target_option['value']
                    prefix_start = old_line.find(option)
                    optionLen = len(option)
                    old_value_position = re.search("\s+".join(old_value.split()), old_line[prefix_start + optionLen:])
                    start = old_value_position.start() + prefix_start + optionLen
                    end = old_value_position.end() + prefix_start + optionLen
                    line = old_line[:start] + value + old_line[end:]
                    index = len(lines) - lines[::-1].index(target_option) - 1
                    lines[index] = optionDict(line, iface, option, value)
    elif state == "absent":
        if len(target_options) >= 1:
            if option in ["pre-up", "up", "down", "post-up"] and value is not None and value != "None":
                for target_option in filter(lambda i: i['value'] == value, target_options):
                    changed = True
                    lines = list(filter(lambda l: l != target_option, lines))
            else:
                changed = True
                for target_option in target_options:
                    lines = list(filter(lambda l: l != target_option, lines))
    else:
        module.fail_json(msg="Error: unsupported state %s, has to be either present or absent" % state)

    return changed, lines
    pass


def addOptionAfterLine(option, value, iface, lines, last_line_dict, iface_options):
    last_line = last_line_dict['line']
    prefix_start = last_line.find(last_line.split()[0])
    suffix_start = last_line.rfind(last_line.split()[-1]) + len(last_line.split()[-1])
    prefix = last_line[:prefix_start]

    if len(iface_options) < 1:
        # interface has no options, ident
        prefix += "    "

    line = prefix + "%s %s" % (option, value) + last_line[suffix_start:]
    option_dict = optionDict(line, iface, option, value)
    index = len(lines) - lines[::-1].index(last_line_dict)
    lines.insert(index, option_dict)
    return lines


def write_changes(module, lines, dest):

    tmpfd, tmpfile = tempfile.mkstemp()
    f = os.fdopen(tmpfd, 'wb')
    f.writelines(lines)
    f.close()
    module.atomic_move(tmpfile, os.path.realpath(dest))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            dest=dict(default='/etc/network/interfaces', required=False),
            iface=dict(required=False),
            option=dict(required=False),
            value=dict(required=False),
            backup=dict(default='no', type='bool'),
            state=dict(default='present', choices=['present', 'absent']),
        ),
        add_file_common_args=True,
        supports_check_mode=True
    )

    dest = os.path.expanduser(module.params['dest'])

    iface = module.params['iface']
    option = module.params['option']
    value = module.params['value']
    backup = module.params['backup']
    state = module.params['state']

    if option is not None and iface is None:
        module.fail_json(msg="Inteface must be set if option is defined")

    if option is not None and state == "present" and value is None:
        module.fail_json(msg="Value must be set if option is defined and state is 'present'")

    lines, ifaces = read_interfaces_file(module, dest)

    changed = False

    if option is not None:
        changed, lines = setInterfaceOption(module, lines, iface, option, value, state)

    if changed:
        _, ifaces = read_interfaces_lines(module, [d['line'] for d in lines if 'line' in d])

    if changed and not module.check_mode:
        if backup:
            module.backup_local(dest)
        write_changes(module, [d['line'] for d in lines if 'line' in d], dest)

    module.exit_json(dest=dest, changed=changed, ifaces=ifaces)


if __name__ == '__main__':
    main()
