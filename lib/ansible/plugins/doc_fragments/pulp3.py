# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Timo Funke <timoses@msn.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options:
  url:
    description:
    - Pulp3 Host.
    default: http://localhost:24817
    type: str
'''

    PULP_PLUGIN = r'''
options:
  pulp_plugin:
    description:
    - Which pulp plugin to use.
    type: str
    required: true
    choices:
    - docker
    - file
    - rpm

notes:
  - This module requires the Pulp OpenAPI Client Python module
    (`pulp-<pulp_plugin>-client`) on the targetted host.
'''

    NAMED = r'''
options:
  name:
    description:
    - A unique name.
    required: true
    type: str

notes:
  - Names must be unique for each resource type.
  - Using the same name for different resource types is allowed
    (e.g. both a repository and a remote may be named `foo`).
'''
