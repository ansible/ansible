#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2016, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gluster_heal_facts
short_description: Gather facts about self-heal or rebalance status
author: "Devyani Kota (@devyanikota)"
version_added: "2.8"
description:
  - Gather facts about either self-heal or rebalance status.
options:
  name:
    description:
      - The volume name.
    required: true
    aliases: ['volume']
  status_filter:
    default: "self-heal"
    choices: ["self-heal", "rebalance"]
    description:
      - Determines which facts are to be returned.
      - If the C(status_filter) is C(self-heal), status of self-heal, along with the number of files still in process are returned.
      - If the C(status_filter) is C(rebalance), rebalance status is returned.
requirements:
  - GlusterFS > 3.2
'''

EXAMPLES = '''
- name: Gather self-heal facts about all gluster hosts in the cluster
  gluster_heal_facts:
    name: test_volume
    status_filter: self-heal
  register: self_heal_status
- debug:
    var: self_heal_status

- name: Gather rebalance facts about all gluster hosts in the cluster
  gluster_heal_facts:
    name: test_volume
    status_filter: rebalance
  register: rebalance_status
- debug:
    var: rebalance_status
'''

RETURN = '''
name:
    description: GlusterFS volume name
    returned: always
    type: str
status_filter:
    description: Whether self-heal or rebalance status is to be returned
    returned: always
    type: str
heal_info:
    description: List of files that still need healing process
    returned: On success
    type: list
rebalance_status:
    description: Status of rebalance operation
    returned: On success
    type: list
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from distutils.version import LooseVersion

glusterbin = ''


def run_gluster(gargs, **kwargs):
    global glusterbin
    global module
    args = [glusterbin, '--mode=script']
    args.extend(gargs)
    try:
        rc, out, err = module.run_command(args, **kwargs)
        if rc != 0:
            module.fail_json(msg='error running gluster (%s) command (rc=%d): %s' %
                             (' '.join(args), rc, out or err), exception=traceback.format_exc())
    except Exception as e:
        module.fail_json(msg='error running gluster (%s) command: %s' % (' '.join(args),
                                                                         to_native(e)), exception=traceback.format_exc())
    return out


def get_self_heal_status(name):
    out = run_gluster(['volume', 'heal', name, 'info'], environ_update=dict(LANG='C', LC_ALL='C', LC_MESSAGES='C'))
    raw_out = out.split("\n")
    heal_info = []
    # return files that still need healing.
    for line in raw_out:
        if 'Brick' in line:
            br_dict = {}
            br_dict['brick'] = line.strip().strip("Brick")
        elif 'Status' in line:
            br_dict['status'] = line.split(":")[1].strip()
        elif 'Number' in line:
            br_dict['no_of_entries'] = line.split(":")[1].strip()
        elif line.startswith('/') or '\n' in line:
            continue
        else:
            br_dict and heal_info.append(br_dict)
            br_dict = {}
    return heal_info


def get_rebalance_status(name):
    out = run_gluster(['volume', 'rebalance', name, 'status'], environ_update=dict(LANG='C', LC_ALL='C', LC_MESSAGES='C'))
    raw_out = out.split("\n")
    rebalance_status = []
    # return the files that are either still 'in progress' state or 'completed'.
    for line in raw_out:
        line = " ".join(line.split())
        line_vals = line.split(" ")
        if line_vals[0].startswith('-') or line_vals[0].startswith('Node'):
            continue
        node_dict = {}
        if len(line_vals) == 1 or len(line_vals) == 4:
            continue
        node_dict['node'] = line_vals[0]
        node_dict['rebalanced_files'] = line_vals[1]
        node_dict['failures'] = line_vals[4]
        if 'in progress' in line:
            node_dict['status'] = line_vals[5] + line_vals[6]
            rebalance_status.append(node_dict)
        elif 'completed' in line:
            node_dict['status'] = line_vals[5]
            rebalance_status.append(node_dict)
    return rebalance_status


def is_invalid_gluster_version(module, required_version):
    cmd = module.get_bin_path('gluster', True) + ' --version'
    result = module.run_command(cmd)
    ver_line = result[1].split('\n')[0]
    version = ver_line.split(' ')[1]
    # If the installed version is less than 3.2, it is an invalid version
    # return True
    return LooseVersion(version) < LooseVersion(required_version)


def main():
    global module
    global glusterbin
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True, aliases=['volume']),
            status_filter=dict(type='str', default='self-heal', choices=['self-heal', 'rebalance']),
        ),
    )

    glusterbin = module.get_bin_path('gluster', True)
    required_version = "3.2"
    status_filter = module.params['status_filter']
    volume_name = module.params['name']
    heal_info = ''
    rebalance_status = ''

    # Verify if required GlusterFS version is installed
    if is_invalid_gluster_version(module, required_version):
        module.fail_json(msg="GlusterFS version > %s is required" %
                         required_version)

    try:
        if status_filter == "self-heal":
            heal_info = get_self_heal_status(volume_name)
        elif status_filter == "rebalance":
            rebalance_status = get_rebalance_status(volume_name)
    except Exception as e:
        module.fail_json(msg='Error retrieving status: %s' % e, exception=traceback.format_exc())

    facts = {}
    facts['glusterfs'] = {'volume': volume_name, 'status_filter': status_filter, 'heal_info': heal_info, 'rebalance': rebalance_status}

    module.exit_json(ansible_facts=facts)


if __name__ == '__main__':
    main()
