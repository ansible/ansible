# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
# (c) 2017 Cisco Systems Inc.
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
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = """
options:
  provider:
    description:
      - A dict object containing connection details.
    type: dict
    suboptions:
      server_endpoint:
        description:
          - Specifies the DNS host name or address for connecting to the remote
            tetration cluster
          - Value can also be specified using C(TETRATION_SERVER_ENDPOINT) environment
            variable.
        aliases:
          - endpoint
          - host
        type: str
        required: true
      api_key:
        description:
          - API Key used for tetration authentication
          - Value can also be specified using C(TETRATION_API_KEY) environment
            variable.
        type: str
        required: true
      api_secret:
        description:
          - Specifies the API secret used for tetration authentication
          - Value can also be specified using C(TETRATION_API_SECRET) environment
            variable.
        type: str
        required: true
      verify:
        description:
          - Boolean value to enable or disable verifying SSL certificates
          - Value can also be specified using C(TETRATION_VERIFY) environment
            variable.
        type: bool
        default: 'no'
      silent_ssl_warnings:
        description:
          - Specifies whether to ignore ssl warnings
        required: false
        type: bool
        default: True
      timeout:
        description:
          - The amount of time before to wait before receiving a response
          - Value can also be specified using C(TETRATION_TIMEOUT) environment
            variable.
        type: int
        default: 10
      max_retries:
        description:
          - Configures the number of attempted retries before the connection
            is declared usable
          - Value can also be specified using C(TETRATION_MAX_RETRIES) environment
            variable.
        type: int
        default: 3
      api_version:
        description:
          - Specifies the version of Tetration OpenAPI to use
          - Value can also be specified using C(TETRATION_API_VERSION) environment
            variable.
        type: str
        default: v1
notes:
  - "This module must be run locally, which can be achieved by specifying C(connection: local)."
  - Please read the :ref:`tetration_guide` for more detailed information on how to use Tetration with Ansible.

requirements:
  - tetpyclient
"""
