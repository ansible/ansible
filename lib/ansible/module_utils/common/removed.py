# Copyright (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import sys

from ansible.module_utils._text import to_native


def removed_module(removed_in, msg='This module has been removed. The module documentation for'
                                   ' Ansible-%(version)s may contain hints for porting'):
    """
    Returns module failure along with a message about the module being removed

    :arg removed_in: The version that the module was removed in
    :kwarg msg: Message to use in the module's failure message. The default says that the module
        has been removed and what version of the Ansible documentation to search for porting help.

    Remove the actual code and instead have boilerplate like this::

        from ansible.module_utils.common.removed import removed_module

        if __name__ == '__main__':
            removed_module("2.4")
    """
    results = {'failed': True}

    # Convert numbers into strings
    removed_in = to_native(removed_in)

    version = removed_in.split('.')
    try:
        numeric_minor = int(version[-1])
    except Exception:
        last_version = None
    else:
        version = version[:-1]
        version.append(to_native(numeric_minor - 1))
        last_version = '.'.join(version)

    if last_version is None:
        results['warnings'] = ['removed modules should specify the version they were removed in']
        results['msg'] = 'This module has been removed'
    else:
        results['msg'] = msg % {'version': last_version}

    print('\n{0}\n'.format(json.dumps(results)))
    sys.exit(1)
