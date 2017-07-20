#!/usr/bin/env python

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ansible.constants as C
import os

from ansible.errors import AnsibleError

galaxy_imported = None
try:
    from ansible.galaxy import Galaxy
    from ansible.galaxy.role import GalaxyRole
    galaxy_imported = True
except ImportError as e:
    galaxy_imported = False


class GalaxyOptions(object):
    '''Stub to initialize the Galaxy object'''
    def __init__(self):
        self.ignore_certs = True
        self.api_server = C.GALAXY_SERVER


def get_role_by_module_fqn(module_fqn):
    '''Use the module FQN to enumerate role and install it'''

    # deferred galaxy imports (because the plugin loader mucks things up)
    if not galaxy_imported:
        from ansible.galaxy import Galaxy
        from ansible.galaxy.role import GalaxyRole

    iparts = module_fqn.split('.')
    role_fqn = '.'.join(iparts[0:2])
    gopts = GalaxyOptions()
    galaxy = Galaxy(gopts)
    galaxy.roles_paths = C.DEFAULT_ROLES_PATH
    gr = GalaxyRole(galaxy, role_fqn)
    install_info = gr.install_info
    if not gr.install_info:
        # not installed to cache, so install it
        installed = gr.install()
        if not installed:
            raise AnsibleError('failed to install %s: %s' % (role_fqn, installed))
    gr.module_file = os.path.join(gr.path, 'library', '%s.py' % iparts[-1])
    return gr


