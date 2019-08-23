#!/usr/bin/python
#
# (c) 2016 Olaf Kilian <olaf.kilian@symanex.com>
#          Chris Houseknecht, <house@redhat.com>
#          James Tanner, <jtanner@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: docker_login
short_description: Log into a Docker registry.
version_added: "2.0"
description:
    - Provides functionality similar to the "docker login" command.
    - Authenticate with a docker registry and add the credentials to your local Docker config file. Adding the
      credentials to the config files allows future connections to the registry using tools such as Ansible's Docker
      modules, the Docker CLI and Docker SDK for Python without needing to provide credentials.
    - Running in check mode will perform the authentication without updating the config file.
options:
  registry_url:
    required: False
    description:
      - The registry URL.
    type: str
    default: "https://index.docker.io/v1/"
    aliases:
      - registry
      - url
  username:
    description:
      - The username for the registry account
    type: str
    required: yes
  password:
    description:
      - The plaintext password for the registry account
    type: str
    required: yes
  email:
    required: False
    description:
      - Does nothing, do not use.
    type: str
  reauthorize:
    description:
      - Refresh existing authentication found in the configuration file.
    type: bool
    default: no
    aliases:
      - reauth
  config_path:
    description:
      - Custom path to the Docker CLI configuration file.
    type: path
    default: ~/.docker/config.json
    aliases:
      - dockercfg_path
  state:
    version_added: '2.3'
    description:
      - This controls the current state of the user. C(present) will login in a user, C(absent) will log them out.
      - To logout you only need the registry server, which defaults to DockerHub.
      - Before 2.1 you could ONLY log in.
      - Docker does not support 'logout' with a custom config file.
    type: str
    default: 'present'
    choices: ['present', 'absent']

extends_documentation_fragment:
  - docker
  - docker.docker_py_1_documentation
requirements:
  - "L(Docker SDK for Python,https://docker-py.readthedocs.io/en/stable/) >= 1.8.0 (use L(docker-py,https://pypi.org/project/docker-py/) for Python 2.6)"
  - "L(Python bindings for docker credentials store API) >= 0.2.1
    (use L(docker-pycreds,https://pypi.org/project/docker-pycreds/) when using Docker SDK for Python < 4.0.0)"
  - "Docker API >= 1.20"
  - "Only to be able to logout, that is for I(state) = C(absent): the C(docker) command line utility"
author:
  - Olaf Kilian (@olsaki) <olaf.kilian@symanex.com>
  - Chris Houseknecht (@chouseknecht)
'''

EXAMPLES = '''

- name: Log into DockerHub
  docker_login:
    username: docker
    password: rekcod

- name: Log into private registry and force re-authorization
  docker_login:
    registry: your.private.registry.io
    username: yourself
    password: secrets3
    reauthorize: yes

- name: Log into DockerHub using a custom config file
  docker_login:
    username: docker
    password: rekcod
    config_path: /tmp/.mydockercfg

- name: Log out of DockerHub
  docker_login:
    state: absent
'''

RETURN = '''
login_results:
    description: Results from the login.
    returned: when state='present'
    type: dict
    sample: {
        "serveraddress": "localhost:5000",
        "username": "testuser"
    }
'''

import os
import re
import traceback

try:
    from docker.errors import DockerException
except ImportError:
    # missing Docker SDK for Python handled in ansible.module_utils.docker.common
    pass

from ansible.module_utils.docker.common import (
    CredentialsNotFound,
    AnsibleDockerClient,
    DEFAULT_DOCKER_REGISTRY,
    DockerBaseClass,
    EMAIL_REGEX,
    RequestException,
)


class LoginManager(DockerBaseClass):

    def __init__(self, client, results):

        super(LoginManager, self).__init__()

        self.client = client
        self.results = results
        parameters = self.client.module.params
        self.check_mode = self.client.check_mode

        self.registry_url = parameters.get('registry_url')
        self.username = parameters.get('username')
        self.password = parameters.get('password')
        self.email = parameters.get('email')
        self.reauthorize = parameters.get('reauthorize')
        self.config_path = parameters.get('config_path')

        # As far as I can tell, email is not supported by credential helpers at all.
        if self.email:
            client.module.deprecate("The email parameter is deprecated and presently does nothing", "2.13")

        if parameters['state'] == 'present':
            self.login()
        else:
            self.logout()

    def fail(self, msg):
        self.client.fail(msg)

    def login(self):
        '''
        Log into the registry with provided username/password. On success update the config
        file with the new authorization.

        :return: None
        '''

        if self.email and not re.match(EMAIL_REGEX, self.email):
            self.fail("Parameter error: the email address appears to be incorrect. Expecting it to match "
                      "/%s/" % (EMAIL_REGEX))

        self.results['actions'].append("Logged into %s" % (self.registry_url))
        self.log("Log into %s with username %s" % (self.registry_url, self.username))
        try:
            response = self.client.login(
                self.username,
                password=self.password,
                email=self.email,
                registry=self.registry_url,
                reauth=self.reauthorize,
                dockercfg_path=self.config_path
            )
        except Exception as exc:
            self.fail("Logging into %s for user %s failed - %s" % (self.registry_url, self.username, str(exc)))

        # If user is already logged in, then response contains password for user
        # This returns correct password if user is logged in and wrong password is given.
        if 'password' in response:
            del response['password']
        self.results['login_result'] = response

        if not self.check_mode:
            self.update_credentials()

    def logout(self):
        '''
        Log out of the registry. On success update the config file.

        :return: None
        '''

        # Get the configuration store.
        store = self.client.get_credential_store_instance(self.registry_url, self.config_path)

        try:
            current = store.get(self.registry_url)
        except CredentialsNotFound:
            # get raises and exception on not found.
            self.log("Credentials for %s not present, doing nothing." % (self.registry_url))
            self.results['changed'] = False

            return

        store.erase(self.registry_url)
        self.results['changed'] = True

    def update_credentials(self):
        '''
        If the authorization is not stored attempt to store authorization values via
        the appropriate credential helper or to the config file.

        :return: None
        '''

        # Check to see if credentials already exist.
        store = self.client.get_credential_store_instance(self.registry_url, self.config_path)

        try:
            current = store.get(self.registry_url)
        except CredentialsNotFound:
            # get raises and exception on not found.
            current = dict(
                Username='',
                Secret=''
            )

        if current['Username'] != self.username or current['Secret'] != self.password or self.reauthorize:
            store.store(self.registry_url, self.username, self.password)
            self.log("Writing credentials to configured helper %s for %s" % (store.program, self.registry_url))
            self.results['actions'].append("Wrote credentials to configured helper %s for %s" % (
                store.program, self.registry_url))
            self.results['changed'] = True


def main():

    argument_spec = dict(
        registry_url=dict(type='str', default=DEFAULT_DOCKER_REGISTRY, aliases=['registry', 'url']),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
        email=dict(type='str'),
        reauthorize=dict(type='bool', default=False, aliases=['reauth']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        config_path=dict(type='path', default='~/.docker/config.json', aliases=['dockercfg_path']),
    )

    required_if = [
        ('state', 'present', ['username', 'password']),
    ]

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if,
        min_docker_api_version='1.20',
    )

    try:
        results = dict(
            changed=False,
            actions=[],
            login_result={}
        )

        LoginManager(client, results)
        if 'actions' in results:
            del results['actions']
        client.module.exit_json(**results)
    except DockerException as e:
        client.fail('An unexpected docker error occurred: {0}'.format(e), exception=traceback.format_exc())
    except RequestException as e:
        client.fail('An unexpected requests error occurred when docker-py tried to talk to the docker daemon: {0}'.format(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
