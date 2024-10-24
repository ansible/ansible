# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def get_command_args():
    '''
    The function for a centralised list for retrieval of shell module options
    '''
    return dict(
        _raw_params=dict(),
        _uses_shell=dict(type='bool', default=False),
        argv=dict(type='list', elements='str'),
        chdir=dict(type='path'),
        executable=dict(),
        expand_argument_vars=dict(type='bool', default=True),
        creates=dict(type='path'),
        removes=dict(type='path'),
        # The default for this really comes from the action plugin
        stdin=dict(required=False),
        stdin_add_newline=dict(type='bool', default=True),
        strip_empty_ends=dict(type='bool', default=True),
        cmd=dict(),
    )
