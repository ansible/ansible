# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017 Fortinet, Inc
# All rights reserved.
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

# check for pyFMG lib
try:
    from pyFMG.fortimgr import FortiManager
    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False


class AnsibleFortiManager(object):

    def __init__(self, module, ip=None, username=None, passwd=None, use_ssl=True, verify_ssl=False, timeout=300):
        self.ip = ip
        self.username = username
        self.passwd = passwd
        self.use_ssl = use_ssl
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.fmgr_instance = None

        if not HAS_PYFMGR:
            module.fail_json(msg='Could not import the python library pyFMG required by this module')

        self.module = module

    def login(self):
        if self.ip is not None:
            self.fmgr_instance = FortiManager(self.ip, self.username, self.passwd, use_ssl=self.use_ssl,
                                              verify_ssl=self.verify_ssl, timeout=self.timeout, debug=False,
                                              disable_request_warnings=True)
            return self.fmgr_instance.login()

    def logout(self):
        if self.fmgr_instance.sid is not None:
            self.fmgr_instance.logout()

    def get(self, url, data):
        return self.fmgr_instance.get(url, **data)

    def set(self, url, data):
        return self.fmgr_instance.set(url, **data)

    def update(self, url, data):
        return self.fmgr_instance.update(url, **data)

    def delete(self, url, data):
        return self.fmgr_instance.delete(url, **data)

    def add(self, url, data):
        return self.fmgr_instance.add(url, **data)

    def execute(self, url, data):
        return self.fmgr_instance.execute(url, **data)

    def move(self, url, data):
        return self.fmgr_instance.move(url, **data)

    def clone(self, url, data):
        return self.fmgr_instance.clone(url, **data)
