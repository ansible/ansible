#!/usr/bin/python
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: cyberark_credential
short_description: Module for retrieval of CyberArk vaulted credential using PAS Web Services SDK through the Central Credential Provider
author:
 - Edward Nunez (@enunez-cyberark)
 - Cyberark Bizdev (@cyberark-bizdev)
 - erasmix (@erasmix)
 - James Stutes (@jimmyjamcabd)
version_added: "2.8"
description:
    - Creates a URI for retrieving a credential from the Cyberark Vault through the Privileged
      Account Security Web Services SDK by requesting access to a specific object through an Application ID
      It returns an Ansible fact called I(cyberarkcredential) as a JSON message with object information
      that can be used by other modules. Every module can use this fact as C(cyberarkcredential) parameter.
options:
    api_base_url:
        description:
            - A string containing the base URL of the server hosting the Central Credential Provider
        type: str
    validate_certs:
        type: bool
        default: 'true'
        description:
            - If C(false), SSL certificate chain will not be validated.  This should only
              set to C(true) if you have a root CA certificate installed on each node.
    app_id:
        description:
            - A string containing the Application ID authorized for retrieving the credential.
    query:
        description:
            - A string containing details of the object being queried
              parameters
                Safe=<safe name>
                Folder=<folder name within safe>
                Object=<object name>
                UserName=<username of object>
                Address=<address listed for object>
                Database=<optional file category for database objects>
                PolicyID=<platform id managing object>.
        required: True
    client_cert:
        required: False
        description:
            - A string containing the file location and name of the client certificate used for authentication.
    client_key:
        required: False
        description:
            - A string containing the file location and name of the private key of the client certificate used for authentication.
    reason:
        required: False
        description:
            - Reason for requesting credential if required by policy.
    state:
        default: present
        choices: [present]
        description:
            - Specifies the state.
"""

EXAMPLES = """
- name: Retrieve credential from CyberArk Vault using PAS Web Services SDK via Central Credential Provider
  cyberark_credential:
    api_base_url: "{{ web_services_base_url }}"
    app_id: "{{ application_id }}"
    query: "Safe=test&UserName=admin"
  register: cyberarkcredential
  result:
    '{ api_base_url }"/AIMWebService/api/Accounts?AppId="{ app_id }"&"{ query }'

- name: Retrieve credential from CyberArk Vault using PAS Web Services SDK via Central Credential Provider
  cyberark_credential:
    api_base_url: "{{ web_services_base_url }}"
    validate_certs: yes
    client_cert: /etc/pki/ca-trust/source/client.pem
    client_key: /etc/pki/ca-trust/source/priv-key.pem
    app_id: "{{ application_id }}"
    query: "Safe=test&UserName=admin"
    reason: "requesting credential for Ansible deployment"
  register: cyberarkcredential
  result:
    '{ api_base_url }"/AIMWebService/api/Accounts?AppId="{ app_id }"&"{ query }'
"""

RETURN = """
cyberark_credential:
    description: CyberArk credential retrieved.
    returned: success
    type: dict
    sample:
      Address:
        description: The target address of the credential being queried
        type: string
        returned: if required
      Content:
        description: The password for the object being queried
        type: string
        returned: always
      CreationMethod:
        description: This is how the object was created in the Vault
        type: string
        returned: always
      DeviceType:
        description: An internal File Category for more granular management of Platforms
        type: string
        returned: always
      Folder:
        description: The folder within the Safe where the credential is stored
        type: string
        returned: always
      Name:
        description: The Cyberark unique object ID of the credential being queried
        type: string
        returned: always
      PasswordChangeInProcess:
        description: If the password has a change flag placed by the CPM
        type: bool
        returned: always
      PolicyID:
        description: Whether or not SSL certificates should be validated.
        type: string
        returned: if assigned to a policy
      Safe:
        description: The safe where the queried credential is stored
        type: string
        returned: always
      Username:
        description: The username of the credential being queried
        type: string
        returned: if required
      LogonDomain:
        description: The Address friendly name resolved by the CPM
        type: string
        returned: if populated
      CPMDisabled:
        description: A description of why this vaulted credential is not being managed by the CPM
        type: string
        returned: if CPM management is disabled and a reason is given
      status_code: 200
"""

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import HTTPError
import json
import urllib
try:
    import httplib
except ImportError:
    # Python 3
    import http.client as httplib


def retrieveCredential(module):

    # Getting parameters from module

    api_base_url = module.params["api_base_url"]
    validate_certs = module.params["validate_certs"]
    app_id = module.params["app_id"]
    query = module.params["query"]
    client_cert = None
    client_key = None

    if "client_cert" in module.params:
        client_cert = module.params["client_cert"]
    if "client_key" in module.params:
        client_key = module.params["client_key"]

    end_point = "/AIMWebService/api/Accounts?AppId=%s&Query=%s" % (urllib.quote(app_id), urllib.quote(query))

    if "reason" in module.params and module.params["reason"] is not None:
        reason = urllib.quote(module.params["reason"])
        end_point = end_point + "&reason=%s" % reason

    result = None
    response = None

    try:

        response = open_url(
            api_base_url + end_point,
            method="GET",
            validate_certs=validate_certs,
            client_cert=client_cert,
            client_key=client_key)

    except (HTTPError, httplib.HTTPException) as http_exception:

        module.fail_json(
            msg=("Error while retrieving credential."
                 "Please validate parameters provided, and permissions for the application and provider in CyberArk."
                 "\n*** end_point=%s%s\n ==> %s" % (api_base_url, end_point, to_text(http_exception))),
            status_code=http_exception.code)

    except Exception as unknown_exception:

        module.fail_json(
            msg=("Unknown error while retrieving credential."
                 "\n*** end_point=%s%s\n%s" % (api_base_url, end_point, to_text(unknown_exception))),
            status_code=-1)

    if response.getcode() == 200:  # Success

        # Result token from REST Api uses a different key based
        try:
            result = json.loads(response.read())
        except Exception as e:
            module.fail_json(
                msg="Error obtain cyberark credential result from http body\n%s" % (to_text(e)),
                status_code=-1)

        return (result, response.getcode())

    else:
        module.fail_json(
            msg="error in end_point=>" +
            end_point)


def main():

    fields = {
        "api_base_url": {"required": True, "type": "str"},
        "app_id": {"required": True, "type": "str"},
        "query": {"required": True, "type": "str"},
        "reason": {"required": False, "type": "str"},
        "validate_certs": {"type": "bool",
                           "default": True},
        "client_cert": {"type": "str", "required": False},
        "client_key": {"type": "str", "required": False},
        "state": {"type": "str",
                  "choices": ["present"],
                  "default": "present"},
    }

    module = AnsibleModule(
        argument_spec=fields,
        supports_check_mode=True)

    (result, status_code) = retrieveCredential(module)

    module.exit_json(
        changed=False,
        result=result,
        status_code=status_code)


if __name__ == '__main__':
    main()
