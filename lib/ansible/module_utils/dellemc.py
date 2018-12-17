# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Paul Martin <paule.martin@dell.com>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
VERSION = 1.1
USER_AGENT_BASE = 'Ansible'

try:
    import PyU4V
    HAS_PyU4V=True
except ImportError:
    HAS_PyU4V=False


def dellemc_argument_spec():
    return dict(
        unispherehost=dict(required=True),
        universion=dict(type='int', required=False),
        verifycert=dict(type='bool', required=True),
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        array_id=dict(type='str', required=True),
    )


def pmaxapi(module):
    if not HAS_PyU4V:
        module.fail_json(msg='PyU4V is required for this module')
    else:
        conn = PyU4V.U4VConn(server_ip=module.params['unispherehost'],
                             port=8443,
                             array_id=module.params['array_id'],
                             verify=module.params['verifycert'],
                             username=module.params['user'],
                             password=module.params['password'],
                             u4v_version=module.params['universion'])
    return conn


