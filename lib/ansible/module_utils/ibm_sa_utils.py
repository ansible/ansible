# Copyright (C) 2018 IBM CORPORATION
# Author(s): Tzur Eliyahu <tzure@il.ibm.com>
#
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from functools import wraps
from ansible.module_utils._text import to_native

PYXCLI_INSTALLED = True
try:
    from pyxcli import client, errors
except ImportError:
    PYXCLI_INSTALLED = False

AVAILABLE_PYXCLI_FIELDS = ['pool', 'size', 'snapshot_size',
                           'domain', 'perf_class', 'vol',
                           'iscsi_chap_name', 'iscsi_chap_secret',
                           'cluster', 'host', 'lun', 'override',
                           'fcaddress', 'iscsi_name']


def xcli_wrapper(func):
    """ Catch xcli errors and return a proper message"""
    @wraps(func)
    def wrapper(module, *args, **kwargs):
        try:
            return func(module, *args, **kwargs)
        except errors.CommandExecutionError as e:
            module.fail_json(msg=to_native(e))
    return wrapper


@xcli_wrapper
def connect_ssl(module):
    endpoints = module.params['endpoints']
    username = module.params['username']
    password = module.params['password']
    if not (username and password and endpoints):
        module.fail_json(
            msg="Username, password or endpoints arguments "
            "are missing from the module arguments")

    try:
        return client.XCLIClient.connect_multiendpoint_ssl(username,
                                                           password,
                                                           endpoints)
    except errors.CommandFailedConnectionError as e:
        module.fail_json(
            msg="Connection with Spectrum Accelerate system has "
            "failed: {[0]}.".format(to_native(e)))


def spectrum_accelerate_spec():
    """ Return arguments spec for AnsibleModule """
    return dict(
        endpoints=dict(required=True),
        username=dict(required=True),
        password=dict(no_log=True, required=True),
    )


@xcli_wrapper
def execute_pyxcli_command(module, xcli_command, xcli_client):
    pyxcli_args = build_pyxcli_command(module.params)
    getattr(xcli_client.cmd, xcli_command)(**(pyxcli_args))
    return True


def build_pyxcli_command(fields):
    """ Builds the args for pyxcli using the exact args from ansible"""
    pyxcli_args = {}
    for field in fields:
        if field in AVAILABLE_PYXCLI_FIELDS and fields[field]:
            pyxcli_args[field] = fields[field]
    return pyxcli_args


def is_pyxcli_installed(module):
    if not PYXCLI_INSTALLED:
        module.fail_json(
            msg='pyxcli is required, use \'pip install pyxcli\' '
            'in order to install it.')
