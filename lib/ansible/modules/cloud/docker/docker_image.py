#!/usr/bin/python
#

# (c) 2014, Pavel Antonov <antonov@adwz.ru>
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
module: docker_image
author: "Pavel Antonov (@softzilla)"
version_added: "1.5"
short_description: manage docker images
description:
     - Create, check and remove docker images
options:
  path:
    description:
       - Path to directory with Dockerfile
    required: false
    default: null
    aliases: []
  dockerfile:
    description:
       - Dockerfile to use
    required: false
    default: Dockerfile
    version_added: "2.0"
  name:
    description:
       - Image name to work with
    required: true
    default: null
    aliases: []
  tag:
    description:
       - Image tag to work with
    required: false
    default: "latest"
    aliases: []
  nocache:
    description:
      - Do not use cache with building
    required: false
    default: false
    aliases: []
  docker_url:
    description:
      - URL of docker host to issue commands to
    required: false
    default: ${DOCKER_HOST} or unix://var/run/docker.sock
    aliases: []
  use_tls:
    description:
      - Whether to use tls to connect to the docker server.  "no" means not to
        use tls (and ignore any other tls related parameters). "encrypt" means
        to use tls to encrypt the connection to the server.  "verify" means to
        also verify that the server's certificate is valid for the server
        (this both verifies the certificate against the CA and that the
        certificate was issued for that host. If this is unspecified, tls will
        only be used if one of the other tls options require it.
    choices: [ "no", "encrypt", "verify" ]
    version_added: "2.0"
  tls_client_cert:
    description:
      - Path to the PEM-encoded certificate used to authenticate docker client.
        If specified tls_client_key must be valid
    default: ${DOCKER_CERT_PATH}/cert.pem
    version_added: "2.0"
  tls_client_key:
    description:
      - Path to the PEM-encoded key used to authenticate docker client. If
        specified tls_client_cert must be valid
    default: ${DOCKER_CERT_PATH}/key.pem
    version_added: "2.0"
  tls_ca_cert:
    description:
      - Path to a PEM-encoded certificate authority to secure the Docker connection.
        This has no effect if use_tls is encrypt.
    default: ${DOCKER_CERT_PATH}/ca.pem
    version_added: "2.0"
  tls_hostname:
    description:
      - A hostname to check matches what's supplied in the docker server's
        certificate.  If unspecified, the hostname is taken from the docker_url.
    default: Taken from docker_url
    version_added: "2.0"
  docker_api_version:
    description:
      - Remote API version to use. This defaults to the current default as
        specified by docker-py.
    default: docker-py default remote API version
    version_added: "2.0"
  state:
    description:
      - Set the state of the image
    required: false
    default: present
    choices: [ "present", "absent", "build" ]
    aliases: []
  timeout:
    description:
      - Set image operation timeout
    required: false
    default: 600
    aliases: []
requirements:
    - "python >= 2.6"
    - "docker-py"
    - "requests"
'''

EXAMPLES = '''
Build docker image if required. Path should contains Dockerfile to build image:

- hosts: web
  sudo: yes
  tasks:
  - name: check or build image
    docker_image: path="/path/to/build/dir" name="my/app" state=present

Build new version of image:

- hosts: web
  sudo: yes
  tasks:
  - name: check or build image
    docker_image: path="/path/to/build/dir" name="my/app" state=build

Remove image from local docker storage:

- hosts: web
  sudo: yes
  tasks:
  - name: remove image
    docker_image: name="my/app" state=absent

'''

import re
import os
from urlparse import urlparse

try:
    import json
except ImportError:
    import simplejson as json

try:
    from requests.exceptions import *
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import docker.client
    HAS_DOCKER_CLIENT = True
except ImportError:
    HAS_DOCKER_CLIENT = False

DEFAULT_DOCKER_API_VERSION = None
if HAS_DOCKER_CLIENT:
    try:
        from docker.errors import APIError as DockerAPIError
    except ImportError:
        from docker.client import APIError as DockerAPIError

    try:
        # docker-py 1.2+
        import docker.constants
        DEFAULT_DOCKER_API_VERSION = docker.constants.DEFAULT_DOCKER_API_VERSION
    except (ImportError, AttributeError):
        # docker-py less than 1.2
        DEFAULT_DOCKER_API_VERSION = docker.client.DEFAULT_DOCKER_API_VERSION

class DockerImageManager:

    def __init__(self, module):
        self.module = module
        self.path = self.module.params.get('path')
        self.dockerfile = self.module.params.get('dockerfile')
        self.name = self.module.params.get('name')
        self.tag = self.module.params.get('tag')
        self.nocache = self.module.params.get('nocache')

        # Connect to the docker server using any configured host and TLS settings.

        env_host = os.getenv('DOCKER_HOST')
        env_docker_verify = os.getenv('DOCKER_TLS_VERIFY')
        env_cert_path = os.getenv('DOCKER_CERT_PATH')
        env_docker_hostname = os.getenv('DOCKER_TLS_HOSTNAME')

        docker_url = module.params.get('docker_url')
        if not docker_url:
            if env_host:
                docker_url = env_host
            else:
                docker_url = 'unix://var/run/docker.sock'

        docker_api_version = module.params.get('docker_api_version')

        tls_client_cert = module.params.get('tls_client_cert', None)
        if not tls_client_cert and env_cert_path:
            tls_client_cert = os.path.join(env_cert_path, 'cert.pem')

        tls_client_key = module.params.get('tls_client_key', None)
        if not tls_client_key and env_cert_path:
            tls_client_key = os.path.join(env_cert_path, 'key.pem')

        tls_ca_cert = module.params.get('tls_ca_cert')
        if not tls_ca_cert and env_cert_path:
            tls_ca_cert = os.path.join(env_cert_path, 'ca.pem')

        tls_hostname = module.params.get('tls_hostname')
        if tls_hostname is None:
            if env_docker_hostname:
                tls_hostname = env_docker_hostname
            else:
                parsed_url = urlparse(docker_url)
                if ':' in parsed_url.netloc:
                    tls_hostname = parsed_url.netloc[:parsed_url.netloc.rindex(':')]
                else:
                    tls_hostname = parsed_url
        if not tls_hostname:
            tls_hostname = True

        # use_tls can be one of four values:
        # no: Do not use tls
        # encrypt: Use tls.  We may do client auth.  We will not verify the server
        # verify: Use tls.  We may do client auth.  We will verify the server
        # None: Only use tls if the parameters for client auth were specified
        #   or tls_ca_cert (which requests verifying the server with
        #   a specific ca certificate)
        use_tls = module.params.get('use_tls')
        if use_tls is None and env_docker_verify is not None:
            use_tls = 'verify'

        tls_config = None
        if use_tls != 'no':
            params = {}

            # Setup client auth
            if tls_client_cert and tls_client_key:
                params['client_cert'] = (tls_client_cert, tls_client_key)

            # We're allowed to verify the connection to the server
            if use_tls == 'verify' or (use_tls is None and tls_ca_cert):
                if tls_ca_cert:
                    params['ca_cert'] = tls_ca_cert
                    params['verify'] = True
                    params['assert_hostname'] = tls_hostname
                else:
                    params['verify'] = True
                    params['assert_hostname'] = tls_hostname
            elif use_tls == 'encrypt':
                params['verify'] = False

            if params:
                # See https://github.com/docker/docker-py/blob/d39da11/docker/utils/utils.py#L279-L296
                docker_url = docker_url.replace('tcp://', 'https://')
                tls_config = docker.tls.TLSConfig(**params)

        self.client = docker.Client(
            base_url=docker_url,
            version=module.params.get('docker_api_version'),
            timeout=module.params.get('timeout'),
            tls=tls_config)

        self.changed = False
        self.log = []
        self.error_msg = None

    def get_log(self, as_string=True):
        return "".join(self.log) if as_string else self.log

    def build(self):
        stream = self.client.build(self.path, dockerfile=self.dockerfile, tag=':'.join([self.name, self.tag]), nocache=self.nocache, rm=True, stream=True)
        success_search = r'Successfully built ([0-9a-f]+)'
        image_id = None
        self.changed = True

        for chunk in stream:
            if not chunk:
                continue

            try:
                chunk_json = json.loads(chunk)
            except ValueError:
                continue

            if 'error' in chunk_json:
                self.error_msg = chunk_json['error']
                return None

            if 'stream' in chunk_json:
                output = chunk_json['stream']
                self.log.append(output)
                match = re.search(success_search, output)
                if match:
                    image_id = match.group(1)

        # Just in case we skipped evaluating the JSON returned from build
        # during every iteration, add an error if the image_id was never
        # populated
        if not image_id:
            self.error_msg = 'Unknown error encountered'

        return image_id

    def has_changed(self):
        return self.changed

    def get_images(self):
        filtered_images = []
        images = self.client.images()
        for i in images:
            # Docker-py version >= 0.3 (Docker API >= 1.8)
            if 'RepoTags' in i:
                repotag = ':'.join([self.name, self.tag])
                if not self.name or repotag in i['RepoTags']:
                    filtered_images.append(i)
            # Docker-py version < 0.3 (Docker API < 1.8)
            elif (not self.name or self.name == i['Repository']) and (not self.tag or self.tag == i['Tag']):
                filtered_images.append(i)
        return filtered_images

    def remove_images(self):
        images = self.get_images()
        for i in images:
            try:
                self.client.remove_image(i['Id'])
                self.changed = True
            except DockerAPIError as e:
                # image can be removed by docker if not used
                pass


def main():
    module = AnsibleModule(
        argument_spec = dict(
            path               = dict(required=False, default=None, type='path'),
            dockerfile         = dict(required=False, default="Dockerfile"),
            name               = dict(required=True),
            tag                = dict(required=False, default="latest"),
            nocache            = dict(default=False, type='bool'),
            state              = dict(default='present', choices=['absent', 'present', 'build']),
            use_tls            = dict(default=None, choices=['no', 'encrypt', 'verify']),
            tls_client_cert    = dict(required=False, default=None, type='str'),
            tls_client_key     = dict(required=False, default=None, type='str'),
            tls_ca_cert        = dict(required=False, default=None, type='str'),
            tls_hostname       = dict(required=False, type='str', default=None),
            docker_url         = dict(),
            docker_api_version = dict(required=False,
                                      default=DEFAULT_DOCKER_API_VERSION,
                                      type='str'),
            timeout            = dict(default=600, type='int'),
        )
    )
    if not HAS_DOCKER_CLIENT:
        module.fail_json(msg='docker-py is needed for this module')
    if not HAS_REQUESTS:
        module.fail_json(msg='requests is needed for this module')

    try:
        manager = DockerImageManager(module)
        state = module.params.get('state')
        failed = False
        image_id = None
        msg = ''
        do_build = False

        # build image if not exists
        if state == "present":
            images = manager.get_images()
            if len(images) == 0:
                do_build = True
        # build image
        elif state == "build":
            do_build = True
        # remove image or images
        elif state == "absent":
            manager.remove_images()

        if do_build:
            image_id = manager.build()
            if image_id:
                msg = "Image built: %s" % image_id
            else:
                failed = True
                msg = "Error: %s\nLog:%s" % (manager.error_msg, manager.get_log())

        module.exit_json(failed=failed, changed=manager.has_changed(), msg=msg, image_id=image_id)

    except SSLError as e:
        if get_platform() == "Darwin":
            # Ensure that the environment variables has been set
            if "DOCKER_HOST" not in os.environ:
                environment_error = '''
                It looks like you have not set your docker environment
                variables. Please ensure that you have set the requested
                variables as instructed when running boot2docker up. If
                they are set in .bash_profile you will need to symlink
                it to .bashrc.
                '''
                module.exit_json(failed=True, changed=manager.has_changed(), msg="SSLError: " + str(e) + environment_error)
            # If the above is true it's likely the hostname does not match
            else:
                environment_error = '''
                You may need to ignore hostname missmatches by setting
                tls_hostname=boot2docker in your role. If this does not
                resolve the issue please open an issue at
                ansible/ansible-modules-core and ping michaeljs1990
                '''
                module.exit_json(failed=True, changed=manager.has_changed(), msg="SSLError: " + str(e) + environment_error)
        # General error for non darwin users
        else:
            module.exit_json(failed=True, changed=manager.has_changed(), msg="SSLError: " + str(e))

    except ConnectionError as e:
        if get_platform() == "Darwin" and "DOCKER_HOST" not in os.environ:
            # Ensure that the environment variables has been set
            environment_error = '''
            It looks like you have not set your docker environment
            variables. Please ensure that you have set the requested
            variables as instructed when running boot2docker up. If
            they are set in .bash_profile you will need to symlink
            it to .bashrc.
            '''
            module.exit_json(failed=True, changed=manager.has_changed(), msg="ConnectionError: " + str(e) + environment_error)

        module.exit_json(failed=True, changed=manager.has_changed(), msg="ConnectionError: " + str(e))

    except DockerAPIError as e:
        module.exit_json(failed=True, changed=manager.has_changed(), msg="Docker API error: " + e.explanation)

    except RequestException as e:
        module.exit_json(failed=True, changed=manager.has_changed(), msg=repr(e))

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
