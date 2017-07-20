# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


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
