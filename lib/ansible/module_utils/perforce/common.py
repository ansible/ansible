"""
This module adds shared support for Perforce Helix modules
"""

from __future__ import (absolute_import, division, print_function)
import traceback
__metaclass__ = type

try:
    from P4 import P4, P4Exception
    HAS_P4 = True
except ImportError:
    P4_IMP_ERR = traceback.format_exc()
    HAS_P4 = False

from ansible.module_utils.basic import env_fallback, missing_required_lib


def helix_connect(module, script_name):
    """
    Pass this function a user, p4port, password to connect to a Helix Core server
    """

    if not HAS_P4:
        module.fail_json(msg=missing_required_lib('p4python', url='https://pypi.org/project/p4python/'), exception=P4_IMP_ERR)

    try:
        p4 = P4()
        p4.prog = script_name
        p4.port = module.params['server']
        p4.user = module.params['user']
        p4.password = module.params['password']
        p4.charset = module.params['charset']
        p4.connect()
        p4.run_login()
        if p4.connected() is not True:
            module.fail_json(msg="Unable to connect to Helix")
        return p4
    except Exception as e:
        module.fail_json(msg="There was a problem connecting to Helix: {0}".format(e))


def helix_disconnect(module, connection):
    """
    Pass this function a connection object to disconnect the Helix Core
    session
    """

    try:
        connection.disconnect()
    except Exception as e:
        module.fail_json(msg="There was a problem disconnecting from Helix: {0}".format(e))
