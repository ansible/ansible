# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Sandeep Kasargod <sandeep@vexata.com>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)


HAS_VEXATAPI = True
try:
    from vexatapi.vexata_api_proxy import VexataAPIProxy
except ImportError:
    HAS_VEXATAPI = False

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import env_fallback

VXOS_VERSION = None


def get_version(iocs_json):
    if not iocs_json:
        raise Exception('Invalid IOC json')
    active = filter(lambda x: x['mgmtRole'], iocs_json)
    if not active:
        raise Exception('Unable to detect active IOC')
    active = active[0]
    ver = active['swVersion']
    if ver[0] != 'v':
        raise Exception('Illegal version string')
    ver = ver[1:ver.find('-')]
    ver = map(int, ver.split('.'))
    return tuple(ver)


def get_array(module):
    """Return storage array object or fail"""
    global VXOS_VERSION
    array = module.params['array']
    user = module.params.get('user', None)
    password = module.params.get('password', None)
    validate = module.params.get('validate_certs')

    if not HAS_VEXATAPI:
        module.fail_json(msg='vexatapi library is required for this module. '
                             'To install, use `pip install vexatapi`')

    if user and password:
        system = VexataAPIProxy(array, user, password, verify_cert=validate)
    else:
        module.fail_json(msg='The user/password are required to be passed in to '
                             'the module as arguments or by setting the '
                             'VEXATA_USER and VEXATA_PASSWORD environment variables.')
    try:
        if system.test_connection():
            VXOS_VERSION = get_version(system.iocs())
            return system
        else:
            module.fail_json(msg='Test connection to array failed.')
    except Exception as e:
        module.fail_json(msg='Vexata API access failed: {0}'.format(to_native(e)))


def argument_spec():
    """Return standard base dictionary used for the argument_spec argument in AnsibleModule"""
    return dict(
        array=dict(type='str',
                   required=True),
        user=dict(type='str',
                  fallback=(env_fallback, ['VEXATA_USER'])),
        password=dict(type='str',
                      no_log=True,
                      fallback=(env_fallback, ['VEXATA_PASSWORD'])),
        validate_certs=dict(type='bool',
                            required=False,
                            default=False),
    )


def required_together():
    """Return the default list used for the required_together argument to AnsibleModule"""
    return [['user', 'password']]


def size_to_MiB(size):
    """Convert a '<integer>[MGT]' string to MiB, return -1 on error."""
    quant = size[:-1]
    exponent = size[-1]
    if not quant.isdigit() or exponent not in 'MGT':
        return -1
    quant = int(quant)
    if exponent == 'G':
        quant <<= 10
    elif exponent == 'T':
        quant <<= 20
    return quant
