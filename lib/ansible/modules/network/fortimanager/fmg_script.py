#!/usr/bin/python
#
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
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fmg_script
version_added: "2.5"
author: update by Andrew Welsh, original Jacob McGill (@jmcgill298)
short_description: Add/Edit/Delete and execute scripts
description:
  -  Create/edit/delete scripts and execute the scripts on the FortiManager using jsonrpc API

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: true
  host:
    description:
      - The FortiManager's Address.
    required: true
  lock:
    description:
      - True locks the ADOM, makes necessary configuration updates, saves the config, and unlocks the ADOM
    required: false
    default: True
    type: bool
  password:
    description:
      - The password associated with the username account.
    required: false
  port:
    description:
      - The TCP port used to connect to the FortiManager if other than the default used by the transport
        method(http=80, https=443).
    required: false
  provider:
    description:
      - Dictionary which acts as a collection of arguments used to define the characteristics
        of how to connect to the device.
      - Arguments hostname, username, and password must be specified in either provider or local param.
      - Local params take precedence, e.g. hostname is preferred to provider["hostname"] when both are specified.
    required: false
  session_id:
    description:
      - The session_id of an established and active session
    required: false
  state:
    description:
      - The desired state of the specified object.
      - present - will create a script.
      - execute - execute the scipt.
      - delete - delete the script.
    required: false
    default: present
    choices: ["present", "execute", "delete"]
  use_ssl:
    description:
      - Determines whether to use HTTPS(True) or HTTP(False).
    required: false
    default: True
    type: bool
  username:
    description:
      - The username used to authenticate with the FortiManager.

  validate_certs:
    description:
      - Determines whether to validate certs against a trusted certificate file (True), or accept all certs (False)
    required: false
    default: False
    type: bool

  script_name:
    description:
      - The name of the script.
    required: True
  script_type:
    description:
      - The type of script (CLI or TCL).
    required: false
  script_target:
    description:
      - The target of the script to be run.
    required: false
  script_description:
    description:
      - The description of the script.
    required: false
  script_content:
    description:
      - The script content that will be executed.
    required: false
  script_scope:
    description:
      - (datasource) The devices that the script will run on, can have both device member and device group member.
    required: false
  script_package:
    description:
      - (datasource) Policy package object to run the script against
    required: false
'''

EXAMPLES = '''
- name: CREATE SCRIPT
  fmg_script:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "root"
    script_name: "TestScript"
    script_type: "cli"
    script_target: "remote_device"
    script_description: "Create by Ansible"
    script_content: "get system status"
- name: EXECUTE SCRIPT
  fmg_script:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "root"
    script_name: "TestScript"
    state: "execute"
    script_scope: "FGT1,FGT2"
- name: DELETE SCRIPT
  fmg_script:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "root"
    script_name: "TestScript"
    state: "delete"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: string
"""

import requests
from ansible.module_utils.basic import AnsibleModule, env_fallback, return_values

requests.packages.urllib3.disable_warnings()


class FortiManager(object):
    """
    This is the Base Class for FortiManager modules. All methods common across several FortiManager Classes should be
    defined here and inherited by the sub-class.
    """

    def __init__(self, host, user, passw, use_ssl=True, verify=False, adom="", package="", api_endpoint="", **kwargs):
        """
        :param host: Type str.
                     The IP or resolvable hostname of the FortiManager.
        :param user: Type str.
                     The username used to authenticate with the FortiManager.
        :param passw: Type str.
                      The password associated with the user account.
        :param use_ssl: Type bool.
                        The default is True, which uses HTTPS instead of HTTP.
        :param verify: Type bool.
                       The default is False, which does not verify the certificate against the list of trusted
                       certificates.
        :param adom: Type str.
                     The FortiManager ADOM which the configuration should belong to.
        :param package: Type str.
                        The FortiManager policy package that should be used.
        :param api_endpoint: Type str.
                             The API endpoint used for a particular configuration section.
        :param kwargs: Type dict. Currently supports port.
        :param headers: Type dict.
                        The headers to include in HTTP requests.
        :param port: Type str.
                     Passing the port parameter will override the default HTTP(S) port when making requests.
        """
        self.host = host
        self.user = user
        self.passw = passw
        self.verify = verify
        self.api_endpoint = api_endpoint
        self.adom = adom
        self.package = package
        self.headers = {"Content-Type": "application/json"}

        if "port" not in kwargs:
            self.port = ""
        else:
            self.port = ":{}".format(kwargs["port"])

        if use_ssl:
            self.url = "https://{fw}{port}/jsonrpc".format(fw=self.host, port=self.port)
        else:
            self.url = "http://{fw}{port}/jsonrpc".format(fw=self.host, port=self.port)

    def set_script(self, script_name, script_type, script_content, script_desc, script_target, adom):
        """

        This method sets a script.
        """
        fields = dict()
        fields["content"] = script_content
        fields["desc"] = script_desc
        fields["name"] = script_name
        fields["target"] = script_target
        fields["type"] = script_type

        body = {"method": "set", "params": [{"url": '/dvmdb/adom/{adom}/script/'.format(adom=adom), "data": fields, "session": self.session}]}
        response = self.make_request(body).json()
        return response

    def delete_script(self, script_name, adom):
        """

        This method deletes a script.
        """
        fields = dict()
        fields["name"] = script_name

        body = {"method": "delete", "params": [{"url": '/dvmdb/adom/{adom}/script/'.format(adom=adom), "data": fields, "session": self.session}]}
        response = self.make_request(body).json()
        return response

    # def set_script_schedule(self, script_name, adom):
    #     """
    #     This method will set a script execution schedule.
    #     """
    #
    #     fields = dict()
    #     fields["adom"] = adom
    #     fields["datetime"] = adom
    #     fields["day_of_week"] = scope
    #     fields["name"] = script_name
    #     fields["run_on_db"] = package
    #     fields["type"] = scope
    #     fields["device"] = script_name
    #
    #     body = {"method": "exec", "params": [{"url": '/dvmdb/adom/{adom_name}/script/execute'.format(adom=adom), "data": fields, "session": self.session}]}
    #     response = self.make_request(body).json()
    #     return response
    #
    #     '''
    #     wrapper = list()
    #     data = dict()
    #     data['url'] = '/dvmdb/adom/{adom}/script/{script_name}/script_schedule'.format(adom=adom, script_name=script_name)
    #     data['datetime'] = (datetime.datetime.now() + datetime.timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
    #     data['day_of_week'] = 'tues'
    #     data['name'] = 'apitest'
    #     data['run_on_db'] = 'disable'
    #     data['type'] = 'onetime'
    #     data['device'] = 131
    #     #data['option'] = 'syntax'
    #     '''

    def execute_script(self, script_name, scope, package, adom, vdom):
        """
        This method will execute a specific script.
        """

        fields = dict()
        fields["adom"] = adom
        fields["scope"] = scope
        fields["script"] = script_name
        fields["package"] = package
        scope_list = list()
        scope = scope.replace(' ', '')
        scope = scope.split(',')
        for dev_name in scope:
            scope_list.append({'name': dev_name, 'vdom': vdom})
        fields['scope'] = scope_list

        body = {"method": "exec", "params": [{"url": '/dvmdb/adom/{adom}/script/execute'.format(adom=adom), "data": fields, "session": self.session}]}
        response = self.make_request(body).json()
        return response

    def login(self):
        """
        The login method is used to establish a session with the FortiManager. All necessary parameters need to be
        established at class instantiation.

        :return: The response from the login request. The instance session is also set, and defaults to None if the
        login was not successful
        """
        params = [{"url": "/sys/login/user", "data": {"user": self.user, "passwd": self.passw}}]
        body = {"method": "exec", "params": params}
        login = self.make_request(body)

        self.session = login.json().get("session")

        return login

    def logout(self):
        """
        The login method is used to establish a session with the FortiManager. All necessary parameters need to be
        established at class instantiation.

        :return: The response from the login request. The instance session is also set, and defaults to None if the
        login was not successful
        """
        body = dict(method="exec", params=[{"url": "/sys/logout"}], session=self.session)
        logout = self.make_request(body)

        return logout

    def make_request(self, body):
        """
        This method is used to make a request to the FortiManager API. All requests to FortiManager use the POST method
        to the same URL.

        :param body: Type dict.
                     The JSON body with the necessary request params.
        :return: The response from the API request.
        """
        response = requests.post(self.url, json=body, headers=self.headers, verify=self.verify)

        return response


class FMdevice(FortiManager):
    """
    This is the class used for interacting with the "device" API Endpoint. In addition to device specific methods, the
    api endpoint default value is set to "device."
    """

    def __init__(self, host, user, passw, use_ssl=True, verify=False, adom="", package="", api_endpoint="device",
                 **kwargs):
        super(FMdevice, self).__init__(host, user, passw, use_ssl, verify, adom, package, api_endpoint, **kwargs)

# This dictionary maintains the input parameters for ansible playbooks


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str"),
        vdom=dict(required=False, type="str"),
        host=dict(required=False, type="str"),
        lock=dict(required=False, type="bool"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        port=dict(required=False, type="int"),
        provider=dict(required=False, type="dict"),
        session_id=dict(required=False, type="str"),
        state=dict(choices=["execute", "delete", "schedule", "present"], type="str"),
        use_ssl=dict(required=False, type="bool"),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"])),
        validate_certs=dict(required=False, type="bool"),

        script_name=dict(required=True, type="str"),
        script_type=dict(required=False, type="str"),
        script_target=dict(required=False, type="str"),
        script_description=dict(required=False, type="str"),
        script_content=dict(required=False, type="str"),
        script_scope=dict(required=False, type="str"),
        script_package=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=True,)

    provider = module.params["provider"] or {}

    # prevent secret params in provider from logging
    no_log = ["password", "device_username", "device_password"]
    for param in no_log:
        if provider.get(param):
            module.no_log_values.update(return_values(provider[param]))

    # allow local params to override provider
    for param, pvalue in provider.items():
        if module.params.get(param) is None:
            module.params[param] = pvalue

    # handle params passed via provider and insure they are represented as the data type expected by fortimanager
    adom = module.params["adom"]
    if adom is None:
        adom = "root"
    vdom = module.params["vdom"]
    if vdom is None:
        vdom = "root"
    host = module.params["host"]
    lock = module.params["lock"]
    if lock is None:
        module.params["lock"] = True
    password = module.params["password"]
    port = module.params["port"]
    session_id = module.params["session_id"]
    state = module.params["state"]
    if state is None:
        state = "present"
    use_ssl = module.params["use_ssl"]
    if use_ssl is None:
        use_ssl = True
    username = module.params["username"]
    validate_certs = module.params["validate_certs"]
    if validate_certs is None:
        validate_certs = False

    script_name = module.params["script_name"]
    script_type = module.params["script_type"]
    script_target = module.params["script_target"]
    script_description = module.params["script_description"]
    script_content = module.params["script_content"]
    script_scope = module.params["script_scope"]
    script_package = module.params["script_package"]

    # validate required arguments are passed; not used in argument_spec to allow params to be called from provider
    argument_check = dict(adom=adom, host=host)
    for key, val in argument_check.items():
        if not val:
            module.fail_json(msg="{} is required".format(key))

    kwargs = dict()
    if port:
        kwargs["port"] = port

    # validate successful login or use established session id
    session = FMdevice(host, username, password, use_ssl, validate_certs, adom, **kwargs)
    if not session_id:
        session_login = session.login()
        if not session_login.json()["result"][0]["status"]["code"] == 0:
            module.fail_json(msg="Unable to login", fortimanager_response=session_login.json())
    else:
        session.session = session_id
    # if state is present the add the script, if its execute then run the script
    if state == "present":
        # add script
        results = session.set_script(script_name, script_type, script_content, script_description, script_target, adom)
        if not results["result"][0]["status"]["code"] == 0:
            module.fail_json(msg="Setting Script Failed", **results)
    elif state == "execute":
        # run script
        results = session.execute_script(script_name, script_scope, script_package, adom, vdom)
        if not results["result"][0]["status"]["code"] == 0:
            module.fail_json(msg="Script Execution Failed", **results)

    elif state == "delete":
        results = session.delete_script(script_name, adom)

    # logout, build in check for future logging capabilities
    if not session_id:
        session_logout = session.logout()
        # if not session_logout.json()["result"][0]["status"]["code"] == 0:
        #     results["msg"] = "Completed tasks, but unable to logout of FortiManager"
        #     module.fail_json(**results)

    return module.exit_json(**results)


if __name__ == "__main__":
    main()
