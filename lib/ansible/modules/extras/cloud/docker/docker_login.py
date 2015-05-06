#!/usr/bin/python
#

# (c) 2015, Olaf Kilian <olaf.kilian@symanex.com>
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

######################################################################

DOCUMENTATION = '''
---
module: docker_login
author: Olaf Kilian
version_added: "2.0"
short_description: Manage Docker registry logins
description:
     - Ansible version of the "docker login" CLI command.
     - This module allows you to login to a Docker registry without directly pulling an image or performing any other actions.
     - It will write your login credentials to your local .dockercfg file that is compatible to the Docker CLI client as well as docker-py and all other Docker related modules that are based on docker-py.
options:
  registry:
    description:
       - URL of the registry, for example: https://index.docker.io/v1/
    required: true
  username:
    description:
       - The username for the registry account
    required: true
  password:
    description:
       - The plaintext password for the registry account
    required: true
  email:
    description:
       - The email address for the registry account
    required: false
  reauth:
    description:
       - Whether refresh existing authentication on the Docker server (boolean)
    required: false
    default: false
  dockercfg_path:
    description:
       - Use a custom path for the .dockercfg file
    required: false
    default: ~/.dockercfg
  docker_url:
    descriptions:
       - Refers to the protocol+hostname+port where the Docker server is hosted
    required: false
    default: unix://var/run/docker.sock
  timeout:
    description:
       - The HTTP request timeout in seconds
    required: false
    default: 600

requirements: [ "docker-py" ]
'''

EXAMPLES = '''
Login to a Docker registry without performing any other action. Make sure that the user you are using is either in the docker group which owns the Docker socket or use sudo to perform login actions:

- name: login to DockerHub remote registry using your account
  docker_login:
    username: docker
    password: rekcod
    email: docker@docker.io

- name: login to private Docker remote registry and force reauthentification
  docker_login:
    registry: https://your.private.registry.io/v1/
    username: yourself
    password: secrets3
    reauth: yes

- name: login to DockerHub remote registry using a custom dockercfg file location
  docker_login:
    username: docker
    password: rekcod
    email: docker@docker.io
    dockercfg_path: /tmp/.mydockercfg

'''

import os.path
import sys
import json
import base64
from urlparse import urlparse

try:
    import docker.client
    from docker.errors import APIError as DockerAPIError
    has_lib_docker = True
except ImportError, e:
    has_lib_docker = False

try:
    from requests.exceptions import *
    has_lib_requests_execeptions = True
except ImportError, e:
    has_lib_requests_execeptions = False

class DockerLoginManager:

    def __init__(self, module):

        self.module = module
        self.registry = self.module.params.get('registry')
        self.username = self.module.params.get('username')
        self.password = self.module.params.get('password')
        self.email = self.module.params.get('email')
        self.reauth = self.module.params.get('reauth')
        self.dockercfg_path = os.path.expanduser(self.module.params.get('dockercfg_path'))

        docker_url = urlparse(module.params.get('docker_url'))
        self.client = docker.Client(base_url=docker_url.geturl(), timeout=module.params.get('timeout'))

        self.changed = False
        self.response = False
        self.log = list()

    def login(self):

        if self.reauth:
            self.log.append("Enforcing reauthentification")

        # Connect to registry and login if not already logged in or reauth is enforced.
        try:
            self.response = self.client.login(
                self.username,
                password=self.password,
                email=self.email,
                registry=self.registry,
                reauth=self.reauth,
                dockercfg_path=self.dockercfg_path
            )
        except Exception as e:
            self.module.fail_json(msg="failed to login to the remote registry", error=repr(e))

        # Get status from registry response.
        if self.response.has_key("Status"):
            self.log.append(self.response["Status"])
            if self.response["Status"] == "Login Succeeded":
                self.changed = True
        else:
            self.log.append("Already Authentificated")

        # Update the dockercfg if changed but not failed.
        if self.has_changed() and not self.module.check_mode:
            self.update_dockercfg()

    # This is what the underlaying docker-py unfortunately doesn't do (yet).
    def update_dockercfg(self):

        # Create dockercfg file if it does not exist.
        if not os.path.exists(self.dockercfg_path):
            open(self.dockercfg_path, "w")
            self.log.append("Created new Docker config file at %s" % self.dockercfg_path)
        else:
            self.log.append("Updated existing Docker config file at %s" % self.dockercfg_path)

        # Get existing dockercfg into a dict.
        try:
            docker_config = json.load(open(self.dockercfg_path, "r"))
        except ValueError:
            docker_config = dict()
        if not docker_config.has_key(self.registry):
            docker_config[self.registry] = dict()
        docker_config[self.registry] = dict(
            auth  = base64.b64encode(self.username + b':' + self.password),
            email = self.email
        )

        # Write updated dockercfg to dockercfg file.
        try:
            json.dump(docker_config, open(self.dockercfg_path, "w"), indent=4, sort_keys=True)
        except Exception as e:
            self.module.fail_json(msg="failed to write auth details to file", error=repr(e))

    # Compatible to docker-py auth.decode_docker_auth()
    def encode_docker_auth(self, auth):
        s = base64.b64decode(auth)
        login, pwd = s.split(b':', 1)
        return login.decode('ascii'), pwd.decode('ascii')

    def get_msg(self):
        return ". ".join(self.log)

    def has_changed(self):
        return self.changed

def main():

    module = AnsibleModule(
        argument_spec = dict(
            registry        = dict(required=True),
            username        = dict(required=True),
            password        = dict(required=True),
            email           = dict(required=False, default=None),
            reauth          = dict(required=False, default=False, type='bool'),
            dockercfg_path  = dict(required=False, default='~/.dockercfg'),
            docker_url      = dict(default='unix://var/run/docker.sock'),
            timeout         = dict(default=10, type='int')
        ),
        supports_check_mode=True
    )

    if not has_lib_docker:
        module.fail_json(msg="python library docker-py required: pip install docker-py==1.1.0")

    if not has_lib_requests_execeptions:
        module.fail_json(msg="python library requests required: pip install requests")

    try:
        manager = DockerLoginManager(module)
        manager.login()
        module.exit_json(changed=manager.has_changed(), msg=manager.get_msg())

    except Exception as e:
        module.fail_json(msg="Module execution has failed due to an unexpected error", error=repr(e))

# import module snippets
from ansible.module_utils.basic import *

main()
