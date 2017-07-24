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


try:
    import ucsmsdk
    HAS_UCSMSDK = True
except:
    HAS_UCSMSDK = False

try:
    import ucsm_apis
    HAS_UCSMAPI = True
except:
    HAS_UCSMAPI = False


class UcsConnection():

    @staticmethod
    def is_login_param(param):
        return param in ["ucs_ip", "ucs_username", "ucs_password",
                         "ucs_port", "ucs_secure", "ucs_proxy", "ucs_server"]

    def __init__(self, module):
        if HAS_UCSMSDK is False:
            results = {}
            results["msg"] = "ucsmsdk is not installed"
            module.fail_json(**results)
        if HAS_UCSMAPI is False:
            results = {}
            results["msg"] = "ucsm_apis is not installed"
            module.fail_json(**results)
        self.module = module
        self.handle = None

    def login(self):
        ansible = self.module.params
        server = ansible.get('ucs_server')
        if server:
            return server

        from ucsmsdk.ucshandle import UcsHandle
        results = {}
        try:
            server = UcsHandle(ip=ansible["ucs_ip"],
                               username=ansible["ucs_username"],
                               password=ansible["ucs_password"],
                               port=ansible["ucs_port"],
                               secure=ansible["ucs_secure"],
                               proxy=ansible["ucs_proxy"])
            server.login()
        except Exception as e:
            results["msg"] = str(e)
            self.module.fail_json(**results)
        self.handle = server
        return server

    def logout(self):
        server = self.module.params.get('ucs_server')
        if server:
            # we used a pre-existing handle from a task.
            # do not logout
            return False

        if self.handle:
            self.handle.logout()
            return True
        return False
