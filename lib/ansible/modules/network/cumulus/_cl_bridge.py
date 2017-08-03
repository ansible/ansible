#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Cumulus Networks <ce-ceng@cumulusnetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cl_bridge
version_added: "2.1"
author: "Cumulus Networks (@CumulusNetworks)"
short_description: Configures a bridge port on Cumulus Linux
deprecated: Deprecated in 2.3. Use M(nclu) instead.
description:
    - Configures a bridge interface on Cumulus Linux To configure a bond port
      use the cl_bond module. To configure any other type of interface use the
      cl_interface module. Follow the guidelines for bridging found in the
      Cumulus User Guide at U(http://docs.cumulusnetworks.com)
options:
    name:
        description:
            - Name of the interface.
        required: true
    alias_name:
        description:
            - Description of the port.
    ipv4:
        description:
            - List of IPv4 addresses to configure on the interface.
              In the form I(X.X.X.X/YY).
    ipv6:
        description:
            - List of IPv6 addresses to configure on the interface.
              In the form I(X:X:X::X/YYY).
    addr_method:
        description:
            - Configures the port to use DHCP.
              To enable this feature use the option I(dhcp).
        choices: ['dhcp']
    mtu:
        description:
            - Set MTU. Configure Jumbo Frame by setting MTU to I(9000).
    virtual_ip:
        description:
            - Define IPv4 virtual IP used by the Cumulus Linux VRR feature.
    virtual_mac:
        description:
            - Define Ethernet mac associated with Cumulus Linux VRR feature.
    vids:
        description:
            - In vlan-aware mode, lists VLANs defined under the interface.
    pvid:
        description:
            - In vlan-aware mode, defines vlan that is the untagged vlan.
    stp:
        description:
            - Enables spanning tree Protocol. As of Cumulus Linux 2.5 the default
              bridging mode, only per vlan RSTP or 802.1d is supported. For the
              vlan aware mode, only common instance STP is supported
        default: 'yes'
        choices: ['yes', 'no']
    ports:
        description:
            - List of bridge members.
        required: True
    vlan_aware:
        description:
            - Enables vlan-aware mode.
        choices: ['yes', 'no']
    mstpctl_treeprio:
        description:
            - Set spanning tree root priority. Must be a multiple of 4096.
    location:
        description:
            - Interface directory location.
        default:
            - '/etc/network/interfaces.d'


requirements: [ Alternate Debian network interface manager
ifupdown2 @ github.com/CumulusNetworks/ifupdown2 ]
notes:
    - As this module writes the interface directory location, ensure that
      ``/etc/network/interfaces`` has a 'source /etc/network/interfaces.d/\*' or
      whatever path is mentioned in the ``location`` attribute.

    - For the config to be activated, i.e installed in the kernel,
      "service networking reload" needs be be executed. See EXAMPLES section.
'''

EXAMPLES = '''
# Options ['virtual_mac', 'virtual_ip'] are required together
# configure a bridge vlan aware bridge.
- cl_bridge:
    name: br0
    ports: 'swp1-12'
    vlan_aware: 'yes'
  notify: reload networking

# configure bridge interface to define a default set of vlans
- cl_bridge:
    name: bridge
    ports: 'swp1-12'
    vlan_aware: 'yes'
    vids: '1-100'
  notify: reload networking

# define cl_bridge once in tasks file
# then write interface config in variables file
# with just the options you want.
- cl_bridge:
    name: "{{ item.key }}"
    ports: "{{ item.value.ports }}"
    vlan_aware: "{{ item.value.vlan_aware|default(omit) }}"
    ipv4:  "{{ item.value.ipv4|default(omit) }}"
    ipv6: "{{ item.value.ipv6|default(omit) }}"
    alias_name: "{{ item.value.alias_name|default(omit) }}"
    addr_method: "{{ item.value.addr_method|default(omit) }}"
    mtu: "{{ item.value.mtu|default(omit) }}"
    vids: "{{ item.value.vids|default(omit) }}"
    virtual_ip: "{{ item.value.virtual_ip|default(omit) }}"
    virtual_mac: "{{ item.value.virtual_mac|default(omit) }}"
    mstpctl_treeprio: "{{ item.value.mstpctl_treeprio|default(omit) }}"
  with_dict: "{{ cl_bridges }}"
  notify: reload networking

# In vars file
# ============
---
cl_bridge:
  br0:
    alias_name: 'vlan aware bridge'
    ports: ['swp1', 'swp3']
    vlan_aware: true
    vids: ['1-100']
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

import os
import re
import tempfile

from ansible.module_utils.basic import AnsibleModule


# handy helper for calling system calls.
# calls AnsibleModule.run_command and prints a more appropriate message
# exec_path - path to file to execute, with all its arguments.
# E.g "/sbin/ip -o link show"
# failure_msg - what message to print on failure
def run_cmd(module, exec_path):
    (_rc, out, _err) = module.run_command(exec_path)
    if _rc > 0:
        if re.search('cannot find interface', _err):
            return '[{}]'
        failure_msg = "Failed; %s Error: %s" % (exec_path, _err)
        module.fail_json(msg=failure_msg)
    else:
        return out


def current_iface_config(module):
    # due to a bug in ifquery, have to check for presence of interface file
    # and not rely solely on ifquery. when bug is fixed, this check can be
    # removed
    _ifacename = module.params.get('name')
    _int_dir = module.params.get('location')
    module.custom_current_config = {}
    if os.path.exists(_int_dir + '/' + _ifacename):
        _cmd = "/sbin/ifquery -o json %s" % (module.params.get('name'))
        module.custom_current_config = module.from_json(
            run_cmd(module, _cmd))[0]


def build_address(module):
    # if addr_method == 'dhcp', don't add IP address
    if module.params.get('addr_method') == 'dhcp':
        return
    _ipv4 = module.params.get('ipv4')
    _ipv6 = module.params.get('ipv6')
    _addresslist = []
    if _ipv4 and len(_ipv4) > 0:
        _addresslist += _ipv4

    if _ipv6 and len(_ipv6) > 0:
        _addresslist += _ipv6
    if len(_addresslist) > 0:
        module.custom_desired_config['config']['address'] = ' '.join(
            _addresslist)


def build_vids(module):
    _vids = module.params.get('vids')
    if _vids and len(_vids) > 0:
        module.custom_desired_config['config']['bridge-vids'] = ' '.join(_vids)


def build_pvid(module):
    _pvid = module.params.get('pvid')
    if _pvid:
        module.custom_desired_config['config']['bridge-pvid'] = str(_pvid)


def conv_bool_to_str(_value):
    if isinstance(_value, bool):
        if _value is True:
            return 'yes'
        else:
            return 'no'
    return _value


def build_generic_attr(module, _attr):
    _value = module.params.get(_attr)
    _value = conv_bool_to_str(_value)
    if _value:
        module.custom_desired_config['config'][
            re.sub('_', '-', _attr)] = str(_value)


def build_alias_name(module):
    alias_name = module.params.get('alias_name')
    if alias_name:
        module.custom_desired_config['config']['alias'] = alias_name


def build_addr_method(module):
    _addr_method = module.params.get('addr_method')
    if _addr_method:
        module.custom_desired_config['addr_family'] = 'inet'
        module.custom_desired_config['addr_method'] = _addr_method


def build_vrr(module):
    _virtual_ip = module.params.get('virtual_ip')
    _virtual_mac = module.params.get('virtual_mac')
    vrr_config = []
    if _virtual_ip:
        vrr_config.append(_virtual_mac)
        vrr_config.append(_virtual_ip)
        module.custom_desired_config.get('config')['address-virtual'] = \
            ' '.join(vrr_config)


def add_glob_to_array(_bridgemems):
    """
    goes through each bridge member if it sees a dash add glob
    before it
    """
    result = []
    if isinstance(_bridgemems, list):
        for _entry in _bridgemems:
            if re.search('-', _entry):
                _entry = 'glob ' + _entry
            result.append(_entry)
        return ' '.join(result)
    return _bridgemems


def build_bridge_attr(module, _attr):
    _value = module.params.get(_attr)
    _value = conv_bool_to_str(_value)
    _value = add_glob_to_array(_value)
    if _value:
        module.custom_desired_config['config'][
            'bridge-' + re.sub('_', '-', _attr)] = str(_value)


def build_desired_iface_config(module):
    """
    take parameters defined and build ifupdown2 compatible hash
    """
    module.custom_desired_config = {
        'addr_family': None,
        'auto': True,
        'config': {},
        'name': module.params.get('name')
    }

    for _attr in ['vlan_aware', 'pvid', 'ports', 'stp']:
        build_bridge_attr(module, _attr)

    build_addr_method(module)
    build_address(module)
    build_vids(module)
    build_alias_name(module)
    build_vrr(module)
    for _attr in ['mtu', 'mstpctl_treeprio']:
        build_generic_attr(module, _attr)


def config_dict_changed(module):
    """
    return true if 'config' dict in hash is different
    between desired and current config
    """
    current_config = module.custom_current_config.get('config')
    desired_config = module.custom_desired_config.get('config')
    return current_config != desired_config


def config_changed(module):
    """
    returns true if config has changed
    """
    if config_dict_changed(module):
        return True
    # check if addr_method is changed
    return module.custom_desired_config.get('addr_method') != \
        module.custom_current_config.get('addr_method')


def replace_config(module):
    temp = tempfile.NamedTemporaryFile()
    desired_config = module.custom_desired_config
    # by default it will be something like /etc/network/interfaces.d/swp1
    final_location = module.params.get('location') + '/' + \
        module.params.get('name')
    final_text = ''
    _fh = open(final_location, 'w')
    # make sure to put hash in array or else ifquery will fail
    # write to temp file
    try:
        temp.write(module.jsonify([desired_config]))
        # need to seek to 0 so that data is written to tempfile.
        temp.seek(0)
        _cmd = "/sbin/ifquery -a -i %s -t json" % (temp.name)
        final_text = run_cmd(module, _cmd)
    finally:
        temp.close()

    try:
        _fh.write(final_text)
    finally:
        _fh.close()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ports=dict(required=True, type='list'),
            name=dict(required=True, type='str'),
            ipv4=dict(type='list'),
            ipv6=dict(type='list'),
            alias_name=dict(type='str'),
            addr_method=dict(type='str',
                             choices=['', 'dhcp']),
            mtu=dict(type='str'),
            virtual_ip=dict(type='str'),
            virtual_mac=dict(type='str'),
            vids=dict(type='list'),
            pvid=dict(type='str'),
            mstpctl_treeprio=dict(type='str'),
            vlan_aware=dict(type='bool'),
            stp=dict(type='bool', default='yes'),
            location=dict(type='str',
                          default='/etc/network/interfaces.d')
        ),
        required_together=[
            ['virtual_ip', 'virtual_mac']
        ]
    )

    # if using the jinja default filter, this resolves to
    # create an list with an empty string ['']. The following
    # checks all lists and removes it, so that functions expecting
    # an empty list, get this result. May upstream this fix into
    # the AnsibleModule code to have it check for this.
    for k, _param in module.params.items():
        if isinstance(_param, list):
            module.params[k] = [x for x in _param if x]

    _location = module.params.get('location')
    if not os.path.exists(_location):
        _msg = "%s does not exist." % (_location)
        module.fail_json(msg=_msg)
        return  # for testing purposes only

    ifacename = module.params.get('name')
    _changed = False
    _msg = "interface %s config not changed" % (ifacename)
    current_iface_config(module)
    build_desired_iface_config(module)
    if config_changed(module):
        replace_config(module)
        _msg = "interface %s config updated" % (ifacename)
        _changed = True

    module.exit_json(changed=_changed, msg=_msg)


if __name__ == '__main__':
    main()
