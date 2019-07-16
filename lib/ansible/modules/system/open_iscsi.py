#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Serge van Ginderachter <serge@vanginderachter.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: open_iscsi
author:
- Serge van Ginderachter (@srvg)
version_added: "1.4"
short_description: Manage iSCSI targets with Open-iSCSI
description:
    - Discover targets on given portal, (dis)connect targets, mark targets to
      manually or auto start, return device nodes of connected targets.
requirements:
    - open_iscsi library and tools (iscsiadm)
options:
    portal:
        description:
        - The IP address of the iSCSI target.
        type: str
        aliases: [ ip ]
    port:
        description:
        - The port on which the iSCSI target process listens.
        type: str
        default: 3260
    target:
        description:
        - The iSCSI target name.
        type: str
        aliases: [ name, targetname ]
    login:
        description:
        - Whether the target node should be connected.
        type: bool
        aliases: [ state ]
    node_auth:
        description:
        - The value for C(discovery.sendtargets.auth.authmethod).
        type: str
        default: CHAP
    node_user:
        description:
        - The value for C(discovery.sendtargets.auth.username).
        type: str
    node_pass:
        description:
        - The value for C(discovery.sendtargets.auth.password).
        type: str
    auto_node_startup:
        description:
        - Whether the target node should be automatically connected at startup.
        type: bool
        aliases: [ automatic ]
    discover:
        description:
        - Whether the list of target nodes on the portal should be
          (re)discovered and added to the persistent iSCSI database.
        - Keep in mind that C(iscsiadm) discovery resets configuration, like C(node.startup)
          to manual, hence combined with C(auto_node_startup=yes) will always return
          a changed state.
        type: bool
    show_nodes:
        description:
        - Whether the list of nodes in the persistent iSCSI database should be returned by the module.
        type: bool
'''

EXAMPLES = r'''
- name: Perform a discovery on 10.1.2.3 and show available target nodes
  open_iscsi:
    show_nodes: yes
    discover: yes
    portal: 10.1.2.3

# NOTE: Only works if exactly one target is exported to the initiator
- name: Discover targets on portal and login to the one available
  open_iscsi:
    portal: '{{ iscsi_target }}'
    login: yes
    discover: yes

- name: Connect to the named target, after updating the local persistent database (cache)
  open_iscsi:
    login: yes
    target: iqn.1986-03.com.sun:02:f8c1f9e0-c3ec-ec84-c9c9-8bfb0cd5de3d

- name: Discconnect from the cached named target
  open_iscsi:
    login: no
    target: iqn.1986-03.com.sun:02:f8c1f9e0-c3ec-ec84-c9c9-8bfb0cd5de3d
'''

import glob
import os
import time

from ansible.module_utils.basic import AnsibleModule

ISCSIADM = 'iscsiadm'


def compare_nodelists(l1, l2):
    l1.sort()
    l2.sort()
    return l1 == l2


def iscsi_get_cached_nodes(module, portal=None):
    cmd = '%s --mode node' % iscsiadm_cmd
    (rc, out, err) = module.run_command(cmd)

    if rc == 0:
        lines = out.splitlines()
        nodes = []
        for line in lines:
            # line format is "ip:port,target_portal_group_tag targetname"
            parts = line.split()
            if len(parts) > 2:
                module.fail_json(msg='error parsing output', cmd=cmd)
            target = parts[1]
            parts = parts[0].split(':')
            target_portal = parts[0]

            if portal is None or portal == target_portal:
                nodes.append(target)

    # older versions of scsiadm don't have nice return codes
    # for newer versions see iscsiadm(8); also usr/iscsiadm.c for details
    # err can contain [N|n]o records...
    elif rc == 21 or (rc == 255 and "o records found" in err):
        nodes = []
    else:
        module.fail_json(cmd=cmd, rc=rc, msg=err)

    return nodes


def iscsi_discover(module, portal, port):
    cmd = '%s --mode discovery --type sendtargets --portal %s:%s' % (iscsiadm_cmd, portal, port)
    (rc, out, err) = module.run_command(cmd)

    if rc > 0:
        module.fail_json(cmd=cmd, rc=rc, msg=err)


def target_loggedon(module, target):
    cmd = '%s --mode session' % iscsiadm_cmd
    (rc, out, err) = module.run_command(cmd)

    if rc == 0:
        return target in out
    elif rc == 21:
        return False
    else:
        module.fail_json(cmd=cmd, rc=rc, msg=err)


def target_login(module, target, portal=None, port=None):
    node_auth = module.params['node_auth']
    node_user = module.params['node_user']
    node_pass = module.params['node_pass']

    if node_user:
        params = [('node.session.auth.authmethod', node_auth),
                  ('node.session.auth.username', node_user),
                  ('node.session.auth.password', node_pass)]
        for (name, value) in params:
            cmd = '%s --mode node --targetname %s --op=update --name %s --value %s' % (iscsiadm_cmd, target, name, value)
            (rc, out, err) = module.run_command(cmd)
            if rc > 0:
                module.fail_json(cmd=cmd, rc=rc, msg=err)

    cmd = '%s --mode node --targetname %s --login' % (iscsiadm_cmd, target)
    if portal is not None and port is not None:
        cmd += ' --portal %s:%s' % (portal, port)

    (rc, out, err) = module.run_command(cmd)

    if rc > 0:
        module.fail_json(cmd=cmd, rc=rc, msg=err)


def target_logout(module, target):
    cmd = '%s --mode node --targetname %s --logout' % (iscsiadm_cmd, target)
    (rc, out, err) = module.run_command(cmd)

    if rc > 0:
        module.fail_json(cmd=cmd, rc=rc, msg=err)


def target_device_node(module, target):
    # if anyone know a better way to find out which devicenodes get created for
    # a given target...

    devices = glob.glob('/dev/disk/by-path/*%s*' % target)
    devdisks = []
    for dev in devices:
        # exclude partitions
        if "-part" not in dev:
            devdisk = os.path.realpath(dev)
            # only add once (multi-path?)
            if devdisk not in devdisks:
                devdisks.append(devdisk)
    return devdisks


def target_isauto(module, target):
    cmd = '%s --mode node --targetname %s' % (iscsiadm_cmd, target)
    (rc, out, err) = module.run_command(cmd)

    if rc == 0:
        lines = out.splitlines()
        for line in lines:
            if 'node.startup' in line:
                return 'automatic' in line
        return False
    else:
        module.fail_json(cmd=cmd, rc=rc, msg=err)


def target_setauto(module, target):
    cmd = '%s --mode node --targetname %s --op=update --name node.startup --value automatic' % (iscsiadm_cmd, target)
    (rc, out, err) = module.run_command(cmd)

    if rc > 0:
        module.fail_json(cmd=cmd, rc=rc, msg=err)


def target_setmanual(module, target):
    cmd = '%s --mode node --targetname %s --op=update --name node.startup --value manual' % (iscsiadm_cmd, target)
    (rc, out, err) = module.run_command(cmd)

    if rc > 0:
        module.fail_json(cmd=cmd, rc=rc, msg=err)


def main():
    # load ansible module object
    module = AnsibleModule(
        argument_spec=dict(

            # target
            portal=dict(type='str', aliases=['ip']),
            port=dict(type='str', default=3260),
            target=dict(type='str', aliases=['name', 'targetname']),
            node_auth=dict(type='str', default='CHAP'),
            node_user=dict(type='str'),
            node_pass=dict(type='str', no_log=True),

            # actions
            login=dict(type='bool', aliases=['state']),
            auto_node_startup=dict(type='bool', aliases=['automatic']),
            discover=dict(type='bool', default=False),
            show_nodes=dict(type='bool', default=False),
        ),

        required_together=[['discover_user', 'discover_pass'],
                           ['node_user', 'node_pass']],
        supports_check_mode=True,
    )

    global iscsiadm_cmd
    iscsiadm_cmd = module.get_bin_path('iscsiadm', required=True)

    # parameters
    portal = module.params['portal']
    target = module.params['target']
    port = module.params['port']
    login = module.params['login']
    automatic = module.params['auto_node_startup']
    discover = module.params['discover']
    show_nodes = module.params['show_nodes']

    check = module.check_mode

    cached = iscsi_get_cached_nodes(module, portal)

    # return json dict
    result = {}
    result['changed'] = False

    if discover:
        if portal is None:
            module.fail_json(msg="Need to specify at least the portal (ip) to discover")
        elif check:
            nodes = cached
        else:
            iscsi_discover(module, portal, port)
            nodes = iscsi_get_cached_nodes(module, portal)
        if not compare_nodelists(cached, nodes):
            result['changed'] |= True
            result['cache_updated'] = True
    else:
        nodes = cached

    if login is not None or automatic is not None:
        if target is None:
            if len(nodes) > 1:
                module.fail_json(msg="Need to specify a target")
            else:
                target = nodes[0]
        else:
            # check given target is in cache
            check_target = False
            for node in nodes:
                if node == target:
                    check_target = True
                    break
            if not check_target:
                module.fail_json(msg="Specified target not found")

    if show_nodes:
        result['nodes'] = nodes

    if login is not None:
        loggedon = target_loggedon(module, target)
        if (login and loggedon) or (not login and not loggedon):
            result['changed'] |= False
            if login:
                result['devicenodes'] = target_device_node(module, target)
        elif not check:
            if login:
                target_login(module, target, portal, port)
                # give udev some time
                time.sleep(1)
                result['devicenodes'] = target_device_node(module, target)
            else:
                target_logout(module, target)
            result['changed'] |= True
            result['connection_changed'] = True
        else:
            result['changed'] |= True
            result['connection_changed'] = True

    if automatic is not None:
        isauto = target_isauto(module, target)
        if (automatic and isauto) or (not automatic and not isauto):
            result['changed'] |= False
            result['automatic_changed'] = False
        elif not check:
            if automatic:
                target_setauto(module, target)
            else:
                target_setmanual(module, target)
            result['changed'] |= True
            result['automatic_changed'] = True
        else:
            result['changed'] |= True
            result['automatic_changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
