# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
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


class ModuleDocFragment(object):

    # Cisco UCS doc fragment
    DOCUMENTATION = '''

options:
    ucs_ip:
        description:
            - IP address or hostname of the Cisco UCS server.
        type: str
    ucs_username:
        description:
            - Username as configured on Cisco UCS server.
        type: str
        default: admin
    ucs_password:
        description:
            - Password as configured on Cisco UCS server.
        type: str
    port:
        description:
            - Port number to be used during connection.(By default uses 443 for https and 80 for http connection)
        type: int
        default: null
    secure:
        description:
            - True for secure connection, otherwise False.
        type: bool
        default: null
    proxy:
        description:
            - Proxy to be used for connection.
        type: str
        default: null
    ucs_server:
        description:
            - UcsHandle object to interact with Cisco UCS server.
        type: UcsHandle
        default: null

requirements:
    - 'ucsmsdk'
    - 'ucsm_apis'
    - 'python2 >= 2.7.9 or python3 >= 3.2'
    - 'openssl version >= 1.0.1'

author: "Cisco Systems Inc(ucs-python@cisco.com)"
'''
