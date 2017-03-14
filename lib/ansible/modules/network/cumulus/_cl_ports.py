#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Cumulus Networks <ce-ceng@cumulusnetworks.com>
#
# This file is part of Ansible
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cl_ports
version_added: "2.1"
author: "Cumulus Networks (@CumulusNetworks)"
short_description: Configure Cumulus Switch port attributes (ports.conf)
deprecated: Deprecated in 2.3. Use M(nclu) instead.
description:
    - Set the initial port attribute defined in the Cumulus Linux ports.conf,
      file. This module does not do any error checking at the moment. Be careful
      to not include ports that do not exist on the switch. Carefully read the
      original ports.conf file for any exceptions or limitations.
      For more details go the Configure Switch Port Attribute Documentation at
      U(http://docs.cumulusnetworks.com).
options:
    speed_10g:
        description:
            - List of ports to run initial run at 10G.
    speed_40g:
        description:
            - List of ports to run initial run at 40G.
    speed_4_by_10g:
        description:
            - List of 40G ports that will be unganged to run as 4 10G ports.
    speed_40g_div_4:
        description:
            - List of 10G ports that will be ganged to form a 40G port.
'''
EXAMPLES = '''
# Use cl_ports module to manage the switch attributes defined in the
# ports.conf file on Cumulus Linux

## Unganged port configuration on certain ports
- name: configure ports.conf setup
  cl_ports:
    speed_4_by_10g:
      - swp1
      - swp32
    speed_40g:
      - swp2-31

## Unganged port configuration on certain ports
- name: configure ports.conf setup
  cl_ports:
    speed_4_by_10g:
      - swp1-3
      - swp6
    speed_40g:
      - swp4-5
      - swp7-32
'''

RETURN = '''
changed:
    description: whether the interface was changed
    returned: changed
    type: bool
    sample: True
msg:
    description: human-readable report of success or failure
    returned: always
    type: string
    sample: "interface bond0 config updated"
'''

PORTS_CONF = '/etc/cumulus/ports.conf'


def hash_existing_ports_conf(module):
    module.ports_conf_hash = {}
    if not os.path.exists(PORTS_CONF):
        return False

    try:
        existing_ports_conf = open(PORTS_CONF).readlines()
    except IOError:
        error_msg = get_exception()
        _msg = "Failed to open %s: %s" % (PORTS_CONF, error_msg)
        module.fail_json(msg=_msg)
        return # for testing only should return on module.fail_json

    for _line in existing_ports_conf:
        _m0 = re.match(r'^(\d+)=(\w+)', _line)
        if _m0:
            _portnum = int(_m0.group(1))
            _speed = _m0.group(2)
            module.ports_conf_hash[_portnum] = _speed


def generate_new_ports_conf_hash(module):
    new_ports_conf_hash = {}
    convert_hash = {
        'speed_40g_div_4': '40G/4',
        'speed_4_by_10g': '4x10G',
        'speed_10g': '10G',
        'speed_40g': '40G'
    }
    for k in module.params.keys():
        port_range = module.params[k]
        port_setting = convert_hash[k]
        if port_range:
            port_range = [x for x in port_range if x]
            for port_str in port_range:
                port_range_str = port_str.replace('swp', '').split('-')
                if len(port_range_str) == 1:
                    new_ports_conf_hash[int(port_range_str[0])] = \
                        port_setting
                else:
                    int_range = map(int, port_range_str)
                    portnum_range = range(int_range[0], int_range[1]+1)
                    for i in portnum_range:
                        new_ports_conf_hash[i] = port_setting
    module.new_ports_hash = new_ports_conf_hash


def compare_new_and_old_port_conf_hash(module):
    ports_conf_hash_copy = module.ports_conf_hash.copy()
    module.ports_conf_hash.update(module.new_ports_hash)
    port_num_length = len(module.ports_conf_hash.keys())
    orig_port_num_length = len(ports_conf_hash_copy.keys())
    if port_num_length != orig_port_num_length:
        module.fail_json(msg="Port numbering is wrong. \
Too many or two few ports configured")
        return False
    elif ports_conf_hash_copy == module.ports_conf_hash:
        return False
    return True


def make_copy_of_orig_ports_conf(module):
    if os.path.exists(PORTS_CONF + '.orig'):
        return

    try:
        shutil.copyfile(PORTS_CONF, PORTS_CONF + '.orig')
    except IOError:
        error_msg = get_exception()
        _msg = "Failed to save the original %s: %s" % (PORTS_CONF, error_msg)
        module.fail_json(msg=_msg)
        return  # for testing only

def write_to_ports_conf(module):
    """
    use tempfile to first write out config in temp file
    then write to actual location. may help prevent file
    corruption. Ports.conf is a critical file for Cumulus.
    Don't want to corrupt this file under any circumstance.
    """
    temp = tempfile.NamedTemporaryFile()
    try:
        try:
            temp.write('# Managed By Ansible\n')
            for k in sorted(module.ports_conf_hash.keys()):
                port_setting = module.ports_conf_hash[k]
                _str = "%s=%s\n" % (k, port_setting)
                temp.write(_str)
            temp.seek(0)
            shutil.copyfile(temp.name, PORTS_CONF)
        except IOError:
            error_msg = get_exception()
            module.fail_json(
                msg="Failed to write to %s: %s" % (PORTS_CONF, error_msg))
    finally:
        temp.close()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            speed_40g_div_4=dict(type='list'),
            speed_4_by_10g=dict(type='list'),
            speed_10g=dict(type='list'),
            speed_40g=dict(type='list')
        ),
        required_one_of=[['speed_40g_div_4',
                          'speed_4_by_10g',
                          'speed_10g',
                          'speed_40g']]
    )

    _changed = False
    hash_existing_ports_conf(module)
    generate_new_ports_conf_hash(module)
    if compare_new_and_old_port_conf_hash(module):
        make_copy_of_orig_ports_conf(module)
        write_to_ports_conf(module)
        _changed = True
        _msg = "/etc/cumulus/ports.conf changed"
    else:
        _msg = 'No change in /etc/ports.conf'
    module.exit_json(changed=_changed, msg=_msg)


# import module snippets
from ansible.module_utils.basic import *
# from ansible.module_utils.urls import *
import os
import tempfile
import shutil

if __name__ == '__main__':
    main()
