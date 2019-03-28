#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018, KubeVirt Team <@kubevirt>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: k8s_auth

short_description: Authenticate to Kubernetes clusters which require an explicit login step

version_added: "2.8"

author: KubeVirt Team (@kubevirt)

description:
  - "This module handles authenticating to Kubernetes clusters requiring I(explicit) authentication procedures,
    meaning ones where a client logs in (obtains an authentication token), performs API operations using said
    token and then logs out (revokes the token). An example of a Kubernetes distribution requiring this module
    is OpenShift."
  - "On the other hand a popular configuration for username+password authentication is one utilizing HTTP Basic
    Auth, which does not involve any additional login/logout steps (instead login credentials can be attached
    to each and every API call performed) and as such is handled directly by the C(k8s) module (and other
    resource–specific modules) by utilizing the C(host), C(username) and C(password) parameters. Please
    consult your preferred module's documentation for more details."

options:
  state:
    description:
    - If set to I(present) connect to the API server using the URL specified in C(host) and attempt to log in.
    - If set to I(absent) attempt to log out by revoking the authentication token specified in C(api_key).
    default: present
    choices:
    - present
    - absent
  host:
    description:
    - Provide a URL for accessing the API server.
    required: true
  username:
    description:
    - Provide a username for authenticating with the API server.
  password:
    description:
    - Provide a password for authenticating with the API server.
  ca_cert:
    description:
    - "Path to a CA certificate file used to verify connection to the API server. The full certificate chain
      must be provided to avoid certificate validation errors."
    aliases: [ ssl_ca_cert ]
  validate_certs:
    description:
    - "Whether or not to verify the API server's SSL certificates."
    type: bool
    default: true
    aliases: [ verify_ssl ]
  api_key:
    description:
    - When C(state) is set to I(absent), this specifies the token to revoke.

requirements:
  - python >= 2.7
  - urllib3
  - requests
  - requests-oauthlib
'''

EXAMPLES = '''
- hosts: localhost
  module_defaults:
    group/k8s:
      host: https://k8s.example.com/
      ca_cert: ca.pem
  tasks:
  - block:
    # It's good practice to store login credentials in a secure vault and not
    # directly in playbooks.
    - include_vars: k8s_passwords.yml

    - name: Log in (obtain access token)
      k8s_auth:
        username: admin
        password: "{{ k8s_admin_password }}"
      register: k8s_auth_results

    # Previous task provides the token/api_key, while all other parameters
    # are taken from module_defaults
    - name: Get a list of all pods from any namespace
      k8s_facts:
        api_key: "{{ k8s_auth_results.k8s_auth.api_key }}"
        kind: Pod
      register: pod_list

    always:
    - name: If login succeeded, try to log out (revoke access token)
      when: k8s_auth_results.k8s_auth.api_key is defined
      k8s_auth:
        state: absent
        api_key: "{{ k8s_auth_results.k8s_auth.api_key }}"
'''

# Returned value names need to match k8s modules parameter names, to make it
# easy to pass returned values of k8s_auth to other k8s modules.
# Discussion: https://github.com/ansible/ansible/pull/50807#discussion_r248827899
RETURN = '''
k8s_auth:
  description: Kubernetes authentication facts.
  returned: success
  type: complex
  contains:
    api_key:
      description: Authentication token.
      returned: success
      type: str
    host:
      description: URL for accessing the API server.
      returned: success
      type: str
    ca_cert:
      description: Path to a CA certificate file used to verify connection to the API server.
      returned: success
      type: str
    validate_certs:
      description: "Whether or not to verify the API server's SSL certificates."
      returned: success
      type: bool
    username:
      description: Username for authenticating with the API server.
      returned: success
      type: str
'''


import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib_parse import urlparse, parse_qs, urlencode

# 3rd party imports
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from requests_oauthlib import OAuth2Session
    HAS_REQUESTS_OAUTH = True
except ImportError:
    HAS_REQUESTS_OAUTH = False

try:
    from urllib3.util import make_headers
    HAS_URLLIB3 = True
except ImportError:
    HAS_URLLIB3 = False


K8S_AUTH_ARG_SPEC = {
    'state': {
        'default': 'present',
        'choices': ['present', 'absent'],
    },
    'host': {'required': True},
    'username': {},
    'password': {'no_log': True},
    'ca_cert': {'type': 'path', 'aliases': ['ssl_ca_cert']},
    'validate_certs': {
        'type': 'bool',
        'default': True,
        'aliases': ['verify_ssl']
    },
    'api_key': {'no_log': True},
}


class KubernetesAuthModule(AnsibleModule):
    def __init__(self):
        AnsibleModule.__init__(
            self,
            argument_spec=K8S_AUTH_ARG_SPEC,
            required_if=[
                ('state', 'present', ['username', 'password']),
                ('state', 'absent', ['api_key']),
            ]
        )

        if not HAS_REQUESTS:
            self.fail("This module requires the python 'requests' package. Try `pip install requests`.")

        if not HAS_REQUESTS_OAUTH:
            self.fail("This module requires the python 'requests-oauthlib' package. Try `pip install requests-oauthlib`.")

        if not HAS_URLLIB3:
            self.fail("This module requires the python 'urllib3' package. Try `pip install urllib3`.")

    def execute_module(self):
        state = self.params.get('state')
        verify_ssl = self.params.get('validate_certs')
        ssl_ca_cert = self.params.get('ca_cert')

        self.auth_username = self.params.get('username')
        self.auth_password = self.params.get('password')
        self.auth_api_key = self.params.get('api_key')
        self.con_host = self.params.get('host')

        # python-requests takes either a bool or a path to a ca file as the 'verify' param
        if verify_ssl and ssl_ca_cert:
            self.con_verify_ca = ssl_ca_cert  # path
        else:
            self.con_verify_ca = verify_ssl   # bool

        # Get needed info to access authorization APIs
        self.openshift_discover()

        if state == 'present':
            new_api_key = self.openshift_login()
            result = dict(
                host=self.con_host,
                validate_certs=verify_ssl,
                ca_cert=ssl_ca_cert,
                api_key=new_api_key,
                username=self.auth_username,
            )
        else:
            self.openshift_logout()
            result = dict()

        self.exit_json(changed=False, k8s_auth=result)

    def openshift_discover(self):
        url = '{0}/.well-known/oauth-authorization-server'.format(self.con_host)
        ret = requests.get(url, verify=self.con_verify_ca)

        if ret.status_code != 200:
            self.fail_request("Couldn't find OpenShift's OAuth API", method='GET', url=url,
                              reason=ret.reason, status_code=ret.status_code)

        try:
            oauth_info = ret.json()

            self.openshift_auth_endpoint = oauth_info['authorization_endpoint']
            self.openshift_token_endpoint = oauth_info['token_endpoint']
        except Exception as e:
            self.fail_json(msg="Something went wrong discovering OpenShift OAuth details.",
                           exception=traceback.format_exc())

    def openshift_login(self):
        os_oauth = OAuth2Session(client_id='openshift-challenging-client')
        authorization_url, state = os_oauth.authorization_url(self.openshift_auth_endpoint,
                                                              state="1", code_challenge_method='S256')
        auth_headers = make_headers(basic_auth='{0}:{1}'.format(self.auth_username, self.auth_password))

        # Request authorization code using basic auth credentials
        ret = os_oauth.get(
            authorization_url,
            headers={'X-Csrf-Token': state, 'authorization': auth_headers.get('authorization')},
            verify=self.con_verify_ca,
            allow_redirects=False
        )

        if ret.status_code != 302:
            self.fail_request("Authorization failed.", method='GET', url=authorization_url,
                              reason=ret.reason, status_code=ret.status_code)

        # In here we have `code` and `state`, I think `code` is the important one
        qwargs = {}
        for k, v in parse_qs(urlparse(ret.headers['Location']).query).items():
            qwargs[k] = v[0]
        qwargs['grant_type'] = 'authorization_code'

        # Using authorization code given to us in the Location header of the previous request, request a token
        ret = os_oauth.post(
            self.openshift_token_endpoint,
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
                # This is just base64 encoded 'openshift-challenging-client:'
                'Authorization': 'Basic b3BlbnNoaWZ0LWNoYWxsZW5naW5nLWNsaWVudDo='
            },
            data=urlencode(qwargs),
            verify=self.con_verify_ca
        )

        if ret.status_code != 200:
            self.fail_request("Failed to obtain an authorization token.", method='POST',
                              url=self.openshift_token_endpoint,
                              reason=ret.reason, status_code=ret.status_code)

        return ret.json()['access_token']

    def openshift_logout(self):
        url = '{0}/apis/oauth.openshift.io/v1/oauthaccesstokens/{1}'.format(self.con_host, self.auth_api_key)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {0}'.format(self.auth_api_key)
        }
        json = {
            "apiVersion": "oauth.openshift.io/v1",
            "kind": "DeleteOptions"
        }

        ret = requests.delete(url, headers=headers, json=json, verify=self.con_verify_ca)
        # Ignore errors, the token will time out eventually anyway

    def fail(self, msg=None):
        self.fail_json(msg=msg)

    def fail_request(self, msg, **kwargs):
        req_info = {}
        for k, v in kwargs.items():
            req_info['req_' + k] = v
        self.fail_json(msg=msg, **req_info)


def main():
    module = KubernetesAuthModule()
    try:
        module.execute_module()
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
