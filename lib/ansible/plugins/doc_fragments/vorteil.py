# -*- coding: utf-8 -*-
# Copyright: (c) 2019 Wilhelm, Wonigkeit (wilhelm.wonigkeit@vorteil.io)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
    repo_key:
        description:
            - The access key for the Vorteil.io repo (user specific and generated during user configuration).
            - Only required if the repo has been configured for authenticated connections.
        required: false
        type: str
    repo_address:
        description:
            - FQDN for the Vorteil.io Repository to query
            - This can be set to "localhost" to connect you a systems local vorteil daemon process.
        required: true
        type: str
    repo_proto:
        description:
            - Protocol to use (either http[default] or https)
        choices: ['http', 'https']
        default: 'http'
        type: str
        required: true
    repo_port:
        description:
            - Admin port on which the repository is configured to listen (default 7472)
        required: false
        type: str
'''

    BUCKET = r'''
options:
    repo_bucket:
        description:
            - Repo bucket to query for a list of applications
        required: true
        type: str
'''

    APP = r'''
options:
    repo_app:
        description:
            - Repo application to query within the bucket
        required: true
        type: str
'''
