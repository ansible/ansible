#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Serge van Ginderachter <serge@vanginderachter.be>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: open_iscsi
author: Serge van Ginderachter
version_added: "1.4"
short_description: Manage iscsi targets with open-iscsi
description:
    - Discover targets on given portal, (dis)connect targets, mark targets to
      manually or auto start, return device nodes of connected targets.
requirements:
    - open_iscsi library and tools (iscsiadm)
options:
    portal:
        required: false
        aliases: [ip]
        description:
        - the ip address of the iscsi target
    port:
        required: false
        default: 3260
        description:
        - the port on which the iscsi target process listens
    target:
        required: false
        aliases: [name, targetname]
        description:
        - the iscsi target name
    login:
        required: false
        choices: [true, false]
        description:
        - whether the target node should be connected
    node_auth:
        required: false
        default: CHAP
        description:
        - discovery.sendtargets.auth.authmethod
    node_user:
        required: false
        description:
        - discovery.sendtargets.auth.username
    node_pass:
        required: false
        description:
        - discovery.sendtargets.auth.password
    auto_node_startup:
        aliases: [automatic]
        required: false
        choices: [true, false]
        description:
        - whether the target node should be automatically connected at startup
    discover:
        required: false
        choices: [true, false]
        description:
        - whether the list of target nodes on the portal should be
          (re)discovered and added to the persistent iscsi database.
          Keep in mind that iscsiadm discovery resets configurtion, like node.startup
          to manual, hence combined with auto_node_startup=yes will allways return
          a changed state.
    show_nodes:
        required: false
        choices: [true, false]
        description:
        - whether the list of nodes in the persistent iscsi database should be
          returned by the module

examples:
    - description: perform a discovery on 10.1.2.3 and show available target
                   nodes
      code: >
        open_iscsi: show_nodes=yes discover=yes portal=10.1.2.3
    - description: discover targets on portal and login to the one available
                   (only works if exactly one target is exported to the initiator)
      code: >
        open_iscsi: portal={{iscsi_target}} login=yes discover=yes
    - description: connect to the named target, after updating the local
                   persistent database (cache)
      code: >
        open_iscsi: login=yes target=iqn.1986-03.com.sun:02:f8c1f9e0-c3ec-ec84-c9c9-8bfb0cd5de3d
    - description: discconnect from the cached named target
      code: >
        open_iscsi: login=no target=iqn.1986-03.com.sun:02:f8c1f9e0-c3ec-ec84-c9c9-8bfb0cd5de3d"
'''

import glob
import time

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


def target_login(module, target):

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
    if len(devices) == 0:
        return None
    else:
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
        argument_spec = dict(

            # target 
            portal = dict(required=False, aliases=['ip']),
            port = dict(required=False, default=3260),
            target = dict(required=False, aliases=['name', 'targetname']),
            node_auth = dict(required=False, default='CHAP'),
            node_user = dict(required=False),
            node_pass = dict(required=False),

            # actions
            login = dict(type='bool', aliases=['state']),
            auto_node_startup = dict(type='bool', aliases=['automatic']),
            discover = dict(type='bool', default=False),
            show_nodes = dict(type='bool', default=False)
        ),  

        required_together=[['discover_user', 'discover_pass'],
                           ['node_user', 'node_pass']],
        supports_check_mode=True
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
            module.fail_json(msg = "Need to specify at least the portal (ip) to discover")
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
                module.fail_json(msg = "Need to specify a target")
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
                module.fail_json(msg = "Specified target not found")

    if show_nodes:
        result['nodes'] = nodes

    if login is not None:
        loggedon = target_loggedon(module,target)
        if (login and loggedon) or (not login and not loggedon):
            result['changed'] |= False
            if login:
                result['devicenodes'] = target_device_node(module,target)
        elif not check:
            if login:
                target_login(module, target)
                # give udev some time
                time.sleep(1)
                result['devicenodes'] = target_device_node(module,target)
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



# import module snippets
from ansible.module_utils.basic import *

main()

