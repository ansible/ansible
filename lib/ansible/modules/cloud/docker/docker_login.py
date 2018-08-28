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
      modules, the Docker CLI and docker-py without needing to provide credentials.
    - Running in check mode will perform the authentication without updating the config file.
options:
  registry_url:
    required: False
    description:
      - The registry URL.
    default: "https://index.docker.io/v1/"
    aliases:
      - registry
      - url
  username:
    description:
      - The username for the registry account
    required: True
  password:
    description:
      - The plaintext password for the registry account
    required: True
  email:
    required: False
    description:
      - "The email address for the registry account. NOTE: private registries may not require this,
        but Docker Hub requires it."
  reauthorize:
    description:
      - Refresh exiting authentication found in the configuration file.
    type: bool
    default: 'no'
    aliases:
      - reauth
  config_path:
    description:
      - Custom path to the Docker CLI configuration file.
    default: ~/.docker/config.json
    aliases:
      - self.config_path
      - dockercfg_path
  state:
    version_added: '2.3'
    description:
      - This controls the current state of the user. C(present) will login in a user, C(absent) will log them out.
      - To logout you only need the registry server, which defaults to DockerHub.
      - Before 2.1 you could ONLY log in.
      - docker does not support 'logout' with a custom config file.
    choices: ['present', 'absent']
    default: 'present'

extends_documentation_fragment:
    - docker
requirements:
    - "python >= 2.6"
    - "docker-py >= 1.7.0"
    - "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
       module has been superseded by L(docker,https://pypi.org/project/docker/)
       (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
       For Python 2.6, C(docker-py) must be used. Otherwise, it is recommended to
       install the C(docker) Python module. Note that both modules should I(not)
       be installed at the same time. Also note that when both modules are installed
       and one of them is uninstalled, the other might no longer function and a
       reinstall of it is required."
    - "Docker API >= 1.20"
    - 'Only to be able to logout (state=absent): the docker command line utility'
author:
    - "Olaf Kilian <olaf.kilian@symanex.com>"
    - "Chris Houseknecht (@chouseknecht)"
'''

EXAMPLES = '''

- name: Log into DockerHub
  docker_login:
    username: docker
    password: rekcod
    email: docker@docker.io

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
    email: docker@docker.io
    config_path: /tmp/.mydockercfg

- name: Log out of DockerHub
  docker_login:
    state: absent
    email: docker@docker.com
'''

RETURN = '''
login_results:
    description: Results from the login.
    returned: when state='present'
    type: dict
    sample: {
        "email": "testuer@yahoo.com",
        "serveraddress": "localhost:5000",
        "username": "testuser"
    }
'''

import base64
import json
import os
import re

from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.docker_common import AnsibleDockerClient, DEFAULT_DOCKER_REGISTRY, DockerBaseClass, EMAIL_REGEX


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
            self.update_config_file()

    def logout(self):
        '''
        Log out of the registry. On success update the config file.
        TODO: port to API once docker.py supports this.

        :return: None
        '''

        cmd = "%s logout " % self.client.module.get_bin_path('docker', True)
        # TODO: docker does not support config file in logout, restore this when they do
        # if self.config_path and self.config_file_exists(self.config_path):
        #     cmd += "--config '%s' " % self.config_path
        cmd += "'%s'" % self.registry_url

        (rc, out, err) = self.client.module.run_command(cmd)
        if rc != 0:
            self.fail("Could not log out: %s" % err)

    def config_file_exists(self, path):
        if os.path.exists(path):
            self.log("Configuration file %s exists" % (path))
            return True
        self.log("Configuration file %s not found." % (path))
        return False

    def create_config_file(self, path):
        '''
        Create a config file with a JSON blob containing an auths key.

        :return: None
        '''

        self.log("Creating docker config file %s" % (path))
        config_path_dir = os.path.dirname(path)
        if not os.path.exists(config_path_dir):
            try:
                os.makedirs(config_path_dir)
            except Exception as exc:
                self.fail("Error: failed to create %s - %s" % (config_path_dir, str(exc)))
        self.write_config(path, dict(auths=dict()))

    def write_config(self, path, config):
        try:
            json.dump(config, open(path, "w"), indent=5, sort_keys=True)
        except Exception as exc:
            self.fail("Error: failed to write config to %s - %s" % (path, str(exc)))

    def update_config_file(self):
        '''
        If the authorization not stored in the config file or reauthorize is True,
        update the config file with the new authorization.

        :return: None
        '''

        path = self.config_path
        if not self.config_file_exists(path):
            self.create_config_file(path)

        try:
            # read the existing config
            config = json.load(open(path, "r"))
        except ValueError:
            self.log("Error reading config from %s" % (path))
            config = dict()

        if not config.get('auths'):
            self.log("Adding auths dict to config.")
            config['auths'] = dict()

        if not config['auths'].get(self.registry_url):
            self.log("Adding registry_url %s to auths." % (self.registry_url))
            config['auths'][self.registry_url] = dict()

        b64auth = base64.b64encode(
            to_bytes(self.username) + b':' + to_bytes(self.password)
        )
        auth = to_text(b64auth)

        encoded_credentials = dict(
            auth=auth,
            email=self.email
        )

        if config['auths'][self.registry_url] != encoded_credentials or self.reauthorize:
            # Update the config file with the new authorization
            config['auths'][self.registry_url] = encoded_credentials
            self.log("Updating config file %s with new authorization for %s" % (path, self.registry_url))
            self.results['actions'].append("Updated config file %s with new authorization for %s" % (
                path, self.registry_url))
            self.results['changed'] = True
            self.write_config(path, config)


def main():

    argument_spec = dict(
        registry_url=dict(type='str', required=False, default=DEFAULT_DOCKER_REGISTRY, aliases=['registry', 'url']),
        username=dict(type='str', required=False),
        password=dict(type='str', required=False, no_log=True),
        email=dict(type='str'),
        reauthorize=dict(type='bool', default=False, aliases=['reauth']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        config_path=dict(type='path', default='~/.docker/config.json', aliases=['self.config_path', 'dockercfg_path']),
    )

    required_if = [
        ('state', 'present', ['username', 'password']),
    ]

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if
    )

    results = dict(
        changed=False,
        actions=[],
        login_result={}
    )

    if client.module.params['state'] == 'present' and client.module.params['registry_url'] == DEFAULT_DOCKER_REGISTRY and not client.module.params['email']:
        client.module.fail_json(msg="'email' is required when logging into DockerHub")

    LoginManager(client, results)
    if 'actions' in results:
        del results['actions']
    client.module.exit_json(**results)


if __name__ == '__main__':
    main()
