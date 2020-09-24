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
    description:
      - The registry URL.
    type: str
    default: "https://index.docker.io/v1/"
    aliases:
      - registry
      - url
  username:
    description:
      - The username for the registry account.
      - Required when I(state) is C(present).
    type: str
  password:
    description:
      - The plaintext password for the registry account.
      - Required when I(state) is C(present).
    type: str
  email:
    description:
      - "The email address for the registry account."
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
        "email": "testuer@yahoo.com",
        "serveraddress": "localhost:5000",
        "username": "testuser"
    }
'''

import base64
import json
import os
import re
import traceback

try:
    from docker.errors import DockerException
except ImportError:
    # missing Docker SDK for Python handled in ansible.module_utils.docker.common
    pass

from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.docker.common import (
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

        # Newer docker returns the same "Removing login credentials" message
        # regardless of whether or not we are already logged out.
        # So to try to determine ourselves, we try reading the config if we can
        # and looking at the 'auths' section. Then we do it again after, and
        # compare.
        path = self.config_path
        found_config = self.config_file_exists(path)
        if found_config:
            has_auth = self.auth_in_config(path)
            # This is also enough to restore check_mode functionality
            # If it's in the config, then logging out should remove it.
            if self.check_mode:
                self.results['changed'] = has_auth
                return

        cmd = [self.client.module.get_bin_path('docker', True), "logout", self.registry_url]
        # TODO: docker does not support config file in logout, restore this when they do
        # if self.config_path and self.config_file_exists(self.config_path):
        #     cmd.extend(["--config", self.config_path])

        (rc, out, err) = self.client.module.run_command(cmd)
        if rc != 0:
            self.fail("Could not log out: %s" % err)
        if 'Not logged in to ' in out:
            self.results['changed'] = False
        elif 'Removing login credentials for ' in out:
            # See note above about this.
            if found_config:
                has_auth_after_logout = self.auth_in_config(path)
                self.results['changed'] = has_auth != has_auth_after_logout
            else:
                # If we didn't find a config, something weird likely happened.
                # We lose idempotency here, but keep the backwards compatible
                # behavior instead of erroring.
                self.results['changed'] = True
        else:
            self.client.module.warn('Unable to determine whether logout was successful.')

        # Adding output to actions, so that user can inspect what was actually returned
        self.results['actions'].append(to_text(out))

    def config_file_exists(self, path):
        if os.path.exists(path):
            self.log("Configuration file %s exists" % (path))
            return True
        self.log("Configuration file %s not found." % (path))
        return False

    def auth_in_config(self, path):
        try:
            with open(path, "r") as file:
                config = json.load(file)
                return self.registry_url in config.get('auths', {})
        except ValueError:
            self.log("Error reading config from %s" % (path))
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
            # Write config; make sure it has permissions 0x600
            content = json.dumps(config, indent=5, sort_keys=True).encode('utf-8')
            f = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            try:
                os.write(f, content)
            finally:
                os.close(f)
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
            with open(path, "r") as file:
                config = json.load(file)
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
