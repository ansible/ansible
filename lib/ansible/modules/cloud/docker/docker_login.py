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
    - Authenticate with a docker registry and add the credentials to your local Docker config file respectively the
      credentials store associated to the registry. Adding the credentials to the config files resp. the credential
      store allows future connections to the registry using tools such as Ansible's Docker modules, the Docker CLI
      and Docker SDK for Python without needing to provide credentials.
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
      - Does nothing, do not use.
      - Will be removed in Ansible 2.14.
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
    registry_url: your.private.registry.io
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

import base64
import json
import os
import re
import traceback
from ansible.module_utils._text import to_bytes, to_text

try:
    from docker.errors import DockerException
    from docker import auth

    # Earlier versions of docker/docker-py put decode_auth
    # in docker.auth.auth instead of docker.auth
    if hasattr(auth, 'decode_auth'):
        from docker.auth import decode_auth
    else:
        from docker.auth.auth import decode_auth

except ImportError:
    # missing Docker SDK for Python handled in ansible.module_utils.docker.common
    pass

from ansible.module_utils.docker.common import (
    AnsibleDockerClient,
    HAS_DOCKER_PY,
    DEFAULT_DOCKER_REGISTRY,
    DockerBaseClass,
    EMAIL_REGEX,
    RequestException,
)

NEEDS_DOCKER_PYCREDS = False

# Early versions of docker/docker-py rely on docker-pycreds for
# the credential store api.
if HAS_DOCKER_PY:
    try:
        from docker.credentials.errors import StoreError, CredentialsNotFound
        from docker.credentials import Store
    except ImportError:
        try:
            from dockerpycreds.errors import StoreError, CredentialsNotFound
            from dockerpycreds.store import Store
        except ImportError as exc:
            HAS_DOCKER_ERROR = str(exc)
            NEEDS_DOCKER_PYCREDS = True


if NEEDS_DOCKER_PYCREDS:
    # docker-pycreds missing, so we need to create some place holder classes
    # to allow instantiation.

    class StoreError(Exception):
        pass

    class CredentialsNotFound(Exception):
        pass


class DockerFileStore(object):
    '''
    A custom credential store class that implements only the functionality we need to
    update the docker config file when no credential helpers is provided.
    '''

    program = "<legacy config>"

    def __init__(self, config_path):
        self._config_path = config_path

        # Make sure we have a minimal config if none is available.
        self._config = dict(
            auths=dict()
        )

        try:
            # Attempt to read the existing config.
            with open(self._config_path, "r") as f:
                config = json.load(f)
        except (ValueError, IOError):
            # No config found or an invalid config found so we'll ignore it.
            config = dict()

        # Update our internal config with what ever was loaded.
        self._config.update(config)

    @property
    def config_path(self):
        '''
        Return the config path configured in this DockerFileStore instance.
        '''

        return self._config_path

    def get(self, server):
        '''
        Retrieve credentials for `server` if there are any in the config file.
        Otherwise raise a `StoreError`
        '''

        server_creds = self._config['auths'].get(server)
        if not server_creds:
            raise CredentialsNotFound('No matching credentials')

        (username, password) = decode_auth(server_creds['auth'])

        return dict(
            Username=username,
            Secret=password
        )

    def _write(self):
        '''
        Write config back out to disk.
        '''
        # Make sure directory exists
        dir = os.path.dirname(self._config_path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        # Write config; make sure it has permissions 0x600
        content = json.dumps(self._config, indent=4, sort_keys=True).encode('utf-8')
        f = os.open(self._config_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(f, content)
        finally:
            os.close(f)

    def store(self, server, username, password):
        '''
        Add a credentials for `server` to the current configuration.
        '''

        b64auth = base64.b64encode(
            to_bytes(username) + b':' + to_bytes(password)
        )
        auth = to_text(b64auth)

        # build up the auth structure
        new_auth = dict(
            auths=dict()
        )
        new_auth['auths'][server] = dict(
            auth=auth
        )

        self._config.update(new_auth)
        self._write()

    def erase(self, server):
        '''
        Remove credentials for the given server from the configuration.
        '''

        self._config['auths'].pop(server)
        self._write()


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
        self.state = parameters.get('state')

    def run(self):
        '''
        Do the actuall work of this task here. This allows instantiation for partial
        testing.
        '''

        if self.state == 'present':
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
        if 'password' in response:
            # This returns correct password if user is logged in and wrong password is given.
            # So if it returns another password as we passed, and the user didn't request to
            # reauthorize, still do it.
            if not self.reauthorize and response['password'] != self.password:
                try:
                    response = self.client.login(
                        self.username,
                        password=self.password,
                        email=self.email,
                        registry=self.registry_url,
                        reauth=True,
                        dockercfg_path=self.config_path
                    )
                except Exception as exc:
                    self.fail("Logging into %s for user %s failed - %s" % (self.registry_url, self.username, str(exc)))
            response.pop('password', None)
        self.results['login_result'] = response

        self.update_credentials()

    def logout(self):
        '''
        Log out of the registry. On success update the config file.

        :return: None
        '''

        # Get the configuration store.
        store = self.get_credential_store_instance(self.registry_url, self.config_path)

        try:
            current = store.get(self.registry_url)
        except CredentialsNotFound:
            # get raises an exception on not found.
            self.log("Credentials for %s not present, doing nothing." % (self.registry_url))
            self.results['changed'] = False
            return

        if not self.check_mode:
            store.erase(self.registry_url)
        self.results['changed'] = True

    def update_credentials(self):
        '''
        If the authorization is not stored attempt to store authorization values via
        the appropriate credential helper or to the config file.

        :return: None
        '''

        # Check to see if credentials already exist.
        store = self.get_credential_store_instance(self.registry_url, self.config_path)

        try:
            current = store.get(self.registry_url)
        except CredentialsNotFound:
            # get raises an exception on not found.
            current = dict(
                Username='',
                Secret=''
            )

        if current['Username'] != self.username or current['Secret'] != self.password or self.reauthorize:
            if not self.check_mode:
                store.store(self.registry_url, self.username, self.password)
            self.log("Writing credentials to configured helper %s for %s" % (store.program, self.registry_url))
            self.results['actions'].append("Wrote credentials to configured helper %s for %s" % (
                store.program, self.registry_url))
            self.results['changed'] = True

    def get_credential_store_instance(self, registry, dockercfg_path):
        '''
        Return an instance of docker.credentials.Store used by the given registry.

        :return: A Store or None
        :rtype: Union[docker.credentials.Store, NoneType]
        '''

        # Older versions of docker-py don't have this feature.
        try:
            credstore_env = self.client.credstore_env
        except AttributeError:
            credstore_env = None

        config = auth.load_config(config_path=dockercfg_path)

        if hasattr(auth, 'get_credential_store'):
            store_name = auth.get_credential_store(config, registry)
        elif 'credsStore' in config:
            store_name = config['credsStore']
        else:
            store_name = None

        # Make sure that there is a credential helper before trying to instantiate a
        # Store object.
        if store_name:
            self.log("Found credential store %s" % store_name)
            return Store(store_name, environment=credstore_env)

        return DockerFileStore(dockercfg_path)


def main():

    argument_spec = dict(
        registry_url=dict(type='str', default=DEFAULT_DOCKER_REGISTRY, aliases=['registry', 'url']),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
        email=dict(type='str', removed_in_version='2.14'),
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

        manager = LoginManager(client, results)
        manager.run()

        if 'actions' in results:
            del results['actions']
        client.module.exit_json(**results)
    except DockerException as e:
        client.fail('An unexpected docker error occurred: {0}'.format(e), exception=traceback.format_exc())
    except RequestException as e:
        client.fail('An unexpected requests error occurred when docker-py tried to talk to the docker daemon: {0}'.format(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
