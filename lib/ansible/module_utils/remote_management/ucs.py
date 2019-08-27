# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
# (c) 2019 Cisco Systems Inc.
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

import traceback

from ansible.module_utils.basic import missing_required_lib

UCSMSDK_IMP_ERR = None
try:
    import ucsmsdk
    HAS_UCSMSDK = True
except Exception:
    UCSMSDK_IMP_ERR = traceback.format_exc()
    HAS_UCSMSDK = False

ucs_argument_spec = dict(
    hostname=dict(type='str', required=True),
    username=dict(type='str', default='admin'),
    password=dict(type='str', required=True, no_log=True),
    port=dict(type='int', default=None),
    use_ssl=dict(type='bool', default=True),
    use_proxy=dict(type='bool', default=True),
    proxy=dict(type='str', default=None),
)


class UCSModule():

    def __init__(self, module):
        self.module = module
        self.result = {}
        if not HAS_UCSMSDK:
            self.module.fail_json(msg=missing_required_lib('ucsmsdk'), exception=UCSMSDK_IMP_ERR)
        self.login()

    def __del__(self):
        self.logout()

    def login(self):
        from ucsmsdk.ucshandle import UcsHandle

        # use_proxy=yes (default) and proxy=None (default) should be using the system defined proxy
        # use_proxy=yes (default) and proxy=value should use the provided proxy
        # use_proxy=no (user) should not be using a proxy
        if self.module.params['use_proxy']:
            proxy = self.module.params['proxy']
        else:
            # force no proxy to be used.  Note that proxy=None in UcsHandle will
            # use the system proxy so we must set to something else
            proxy = {}

        try:
            handle = UcsHandle(
                ip=self.module.params['hostname'],
                username=self.module.params['username'],
                password=self.module.params['password'],
                port=self.module.params['port'],
                secure=self.module.params['use_ssl'],
                proxy=proxy
            )
            handle.login()
        except Exception as e:
            self.result['msg'] = str(e)
            self.module.fail_json(**self.result)
        self.login_handle = handle

    def logout(self):
        if hasattr(self, 'login_handle'):
            self.login_handle.logout()
            return True
        return False
