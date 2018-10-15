# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2018, Sandeep Kasargod <sandeep@vexata.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from os import environ

HAS_VEXATAPI = True
try:
    from vexatapi.vexata_api_proxy import VexataAPIProxy
except ImportError:
    HAS_VEXATAPI = False


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

    if user and password:
        system = VexataAPIProxy(array, user, password, verify_cert=False)
    elif environ.get('VEXATA_USER') and environ.get('VEXATA_PASSWORD'):
        user = environ.get('VEXATA_USER')
        password = environ.get('VEXATA_PASSWORD')
        system = VexataAPIProxy(array, user, password, verify_cert=False)
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
        module.fail_json(msg='Vexata API access failed: {0}'.format(str(e)))


def argument_spec():
    """Return standard base dictionary used for the argument_spec argument in AnsibleModule"""
    return dict(
        array=dict(type='str', required=True),
        user=dict(type='str'),
        password=dict(type='str', no_log=True),
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
