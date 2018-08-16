#
#  Copyright 2016 Red Hat | Ansible
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

import os
import re
import json
import sys
import copy
from distutils.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE, BOOLEANS_FALSE

HAS_DOCKER_PY = True
HAS_DOCKER_PY_2 = False
HAS_DOCKER_PY_3 = False
HAS_DOCKER_ERROR = None

try:
    from requests.exceptions import SSLError
    from docker import __version__ as docker_version
    from docker.errors import APIError, TLSParameterError, NotFound
    from docker.tls import TLSConfig
    from docker.constants import DEFAULT_DOCKER_API_VERSION
    from docker import auth

    if LooseVersion(docker_version) >= LooseVersion('3.0.0'):
        HAS_DOCKER_PY_3 = True
        from docker import APIClient as Client
        from docker.types import Ulimit, LogConfig
    elif LooseVersion(docker_version) >= LooseVersion('2.0.0'):
        HAS_DOCKER_PY_2 = True
        from docker import APIClient as Client
        from docker.types import Ulimit, LogConfig
    else:
        from docker import Client
        from docker.utils.types import Ulimit, LogConfig

except ImportError as exc:
    HAS_DOCKER_ERROR = str(exc)
    HAS_DOCKER_PY = False


# The next 2 imports ``docker.models`` and ``docker.ssladapter`` are used
# to ensure the user does not have both ``docker`` and ``docker-py`` modules
# installed, as they utilize the same namespace are are incompatible
try:
    # docker
    import docker.models
    HAS_DOCKER_MODELS = True
except ImportError:
    HAS_DOCKER_MODELS = False

try:
    # docker-py
    import docker.ssladapter
    HAS_DOCKER_SSLADAPTER = True
except ImportError:
    HAS_DOCKER_SSLADAPTER = False


DEFAULT_DOCKER_HOST = 'unix://var/run/docker.sock'
DEFAULT_TLS = False
DEFAULT_TLS_VERIFY = False
DEFAULT_TLS_HOSTNAME = 'localhost'
MIN_DOCKER_VERSION = "1.7.0"
DEFAULT_TIMEOUT_SECONDS = 60

DOCKER_COMMON_ARGS = dict(
    docker_host=dict(type='str', aliases=['docker_url'], default=DEFAULT_DOCKER_HOST),
    tls_hostname=dict(type='str', default=DEFAULT_TLS_HOSTNAME),
    api_version=dict(type='str', aliases=['docker_api_version'], default='auto'),
    timeout=dict(type='int', default=DEFAULT_TIMEOUT_SECONDS),
    cacert_path=dict(type='str', aliases=['tls_ca_cert']),
    cert_path=dict(type='str', aliases=['tls_client_cert']),
    key_path=dict(type='str', aliases=['tls_client_key']),
    ssl_version=dict(type='str'),
    tls=dict(type='bool', default=DEFAULT_TLS),
    tls_verify=dict(type='bool', default=DEFAULT_TLS_VERIFY),
    debug=dict(type='bool', default=False)
)

DOCKER_MUTUALLY_EXCLUSIVE = [
    ['tls', 'tls_verify']
]

DOCKER_REQUIRED_TOGETHER = [
    ['cert_path', 'key_path']
]

DEFAULT_DOCKER_REGISTRY = 'https://index.docker.io/v1/'
EMAIL_REGEX = r'[^@]+@[^@]+\.[^@]+'
BYTE_SUFFIXES = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


if not HAS_DOCKER_PY:
    # No docker-py. Create a place holder client to allow
    # instantiation of AnsibleModule and proper error handing
    class Client(object):
        def __init__(self, **kwargs):
            pass

    class APIError(Exception):
        pass


class DockerBaseClass(object):

    def __init__(self):
        self.debug = False

    def log(self, msg, pretty_print=False):
        pass
        # if self.debug:
        #     log_file = open('docker.log', 'a')
        #     if pretty_print:
        #         log_file.write(json.dumps(msg, sort_keys=True, indent=4, separators=(',', ': ')))
        #         log_file.write(u'\n')
        #     else:
        #         log_file.write(msg + u'\n')


class AnsibleDockerClient(Client):

    def __init__(self, argument_spec=None, supports_check_mode=False, mutually_exclusive=None,
                 required_together=None, required_if=None):

        merged_arg_spec = dict()
        merged_arg_spec.update(DOCKER_COMMON_ARGS)
        if argument_spec:
            merged_arg_spec.update(argument_spec)
            self.arg_spec = merged_arg_spec

        mutually_exclusive_params = []
        mutually_exclusive_params += DOCKER_MUTUALLY_EXCLUSIVE
        if mutually_exclusive:
            mutually_exclusive_params += mutually_exclusive

        required_together_params = []
        required_together_params += DOCKER_REQUIRED_TOGETHER
        if required_together:
            required_together_params += required_together

        self.module = AnsibleModule(
            argument_spec=merged_arg_spec,
            supports_check_mode=supports_check_mode,
            mutually_exclusive=mutually_exclusive_params,
            required_together=required_together_params,
            required_if=required_if)

        if HAS_DOCKER_MODELS and HAS_DOCKER_SSLADAPTER:
            self.fail("Cannot have both the docker-py and docker python modules installed together as they use the same namespace and "
                      "cause a corrupt installation. Please uninstall both packages, and re-install only the docker-py or docker python "
                      "module. It is recommended to install the docker module if no support for Python 2.6 is required.")

        if not HAS_DOCKER_PY:
            self.fail("Failed to import docker or docker-py - %s. Try `pip install docker` or `pip install docker-py` (Python 2.6)" % HAS_DOCKER_ERROR)

        if LooseVersion(docker_version) < LooseVersion(MIN_DOCKER_VERSION):
            self.fail("Error: docker / docker-py version is %s. Minimum version required is %s." % (docker_version,
                                                                                                    MIN_DOCKER_VERSION))

        self.debug = self.module.params.get('debug')
        self.check_mode = self.module.check_mode
        self._connect_params = self._get_connect_params()

        try:
            super(AnsibleDockerClient, self).__init__(**self._connect_params)
        except APIError as exc:
            self.fail("Docker API error: %s" % exc)
        except Exception as exc:
            self.fail("Error connecting: %s" % exc)

    def log(self, msg, pretty_print=False):
        pass
        # if self.debug:
        #     log_file = open('docker.log', 'a')
        #     if pretty_print:
        #         log_file.write(json.dumps(msg, sort_keys=True, indent=4, separators=(',', ': ')))
        #         log_file.write(u'\n')
        #     else:
        #         log_file.write(msg + u'\n')

    def fail(self, msg):
        self.module.fail_json(msg=msg)

    @staticmethod
    def _get_value(param_name, param_value, env_variable, default_value):
        if param_value is not None:
            # take module parameter value
            if param_value in BOOLEANS_TRUE:
                return True
            if param_value in BOOLEANS_FALSE:
                return False
            return param_value

        if env_variable is not None:
            env_value = os.environ.get(env_variable)
            if env_value is not None:
                # take the env variable value
                if param_name == 'cert_path':
                    return os.path.join(env_value, 'cert.pem')
                if param_name == 'cacert_path':
                    return os.path.join(env_value, 'ca.pem')
                if param_name == 'key_path':
                    return os.path.join(env_value, 'key.pem')
                if env_value in BOOLEANS_TRUE:
                    return True
                if env_value in BOOLEANS_FALSE:
                    return False
                return env_value

        # take the default
        return default_value

    @property
    def auth_params(self):
        # Get authentication credentials.
        # Precedence: module parameters-> environment variables-> defaults.

        self.log('Getting credentials')

        params = dict()
        for key in DOCKER_COMMON_ARGS:
            params[key] = self.module.params.get(key)

        if self.module.params.get('use_tls'):
            # support use_tls option in docker_image.py. This will be deprecated.
            use_tls = self.module.params.get('use_tls')
            if use_tls == 'encrypt':
                params['tls'] = True
            if use_tls == 'verify':
                params['tls_verify'] = True

        result = dict(
            docker_host=self._get_value('docker_host', params['docker_host'], 'DOCKER_HOST',
                                        DEFAULT_DOCKER_HOST),
            tls_hostname=self._get_value('tls_hostname', params['tls_hostname'],
                                         'DOCKER_TLS_HOSTNAME', 'localhost'),
            api_version=self._get_value('api_version', params['api_version'], 'DOCKER_API_VERSION',
                                        'auto'),
            cacert_path=self._get_value('cacert_path', params['cacert_path'], 'DOCKER_CERT_PATH', None),
            cert_path=self._get_value('cert_path', params['cert_path'], 'DOCKER_CERT_PATH', None),
            key_path=self._get_value('key_path', params['key_path'], 'DOCKER_CERT_PATH', None),
            ssl_version=self._get_value('ssl_version', params['ssl_version'], 'DOCKER_SSL_VERSION', None),
            tls=self._get_value('tls', params['tls'], 'DOCKER_TLS', DEFAULT_TLS),
            tls_verify=self._get_value('tls_verfy', params['tls_verify'], 'DOCKER_TLS_VERIFY',
                                       DEFAULT_TLS_VERIFY),
            timeout=self._get_value('timeout', params['timeout'], 'DOCKER_TIMEOUT',
                                    DEFAULT_TIMEOUT_SECONDS),
        )

        if result['tls_hostname'] is None:
            # get default machine name from the url
            parsed_url = urlparse(result['docker_host'])
            if ':' in parsed_url.netloc:
                result['tls_hostname'] = parsed_url.netloc[:parsed_url.netloc.rindex(':')]
            else:
                result['tls_hostname'] = parsed_url

        return result

    def _get_tls_config(self, **kwargs):
        self.log("get_tls_config:")
        for key in kwargs:
            self.log("  %s: %s" % (key, kwargs[key]))
        try:
            tls_config = TLSConfig(**kwargs)
            return tls_config
        except TLSParameterError as exc:
            self.fail("TLS config error: %s" % exc)

    def _get_connect_params(self):
        auth = self.auth_params

        self.log("connection params:")
        for key in auth:
            self.log("  %s: %s" % (key, auth[key]))

        if auth['tls'] or auth['tls_verify']:
            auth['docker_host'] = auth['docker_host'].replace('tcp://', 'https://')

        if auth['tls'] and auth['cert_path'] and auth['key_path']:
            # TLS with certs and no host verification
            tls_config = self._get_tls_config(client_cert=(auth['cert_path'], auth['key_path']),
                                              verify=False,
                                              ssl_version=auth['ssl_version'])
            return dict(base_url=auth['docker_host'],
                        tls=tls_config,
                        version=auth['api_version'],
                        timeout=auth['timeout'])

        if auth['tls']:
            # TLS with no certs and not host verification
            tls_config = self._get_tls_config(verify=False,
                                              ssl_version=auth['ssl_version'])
            return dict(base_url=auth['docker_host'],
                        tls=tls_config,
                        version=auth['api_version'],
                        timeout=auth['timeout'])

        if auth['tls_verify'] and auth['cert_path'] and auth['key_path']:
            # TLS with certs and host verification
            if auth['cacert_path']:
                tls_config = self._get_tls_config(client_cert=(auth['cert_path'], auth['key_path']),
                                                  ca_cert=auth['cacert_path'],
                                                  verify=True,
                                                  assert_hostname=auth['tls_hostname'],
                                                  ssl_version=auth['ssl_version'])
            else:
                tls_config = self._get_tls_config(client_cert=(auth['cert_path'], auth['key_path']),
                                                  verify=True,
                                                  assert_hostname=auth['tls_hostname'],
                                                  ssl_version=auth['ssl_version'])

            return dict(base_url=auth['docker_host'],
                        tls=tls_config,
                        version=auth['api_version'],
                        timeout=auth['timeout'])

        if auth['tls_verify'] and auth['cacert_path']:
            # TLS with cacert only
            tls_config = self._get_tls_config(ca_cert=auth['cacert_path'],
                                              assert_hostname=auth['tls_hostname'],
                                              verify=True,
                                              ssl_version=auth['ssl_version'])
            return dict(base_url=auth['docker_host'],
                        tls=tls_config,
                        version=auth['api_version'],
                        timeout=auth['timeout'])

        if auth['tls_verify']:
            # TLS with verify and no certs
            tls_config = self._get_tls_config(verify=True,
                                              assert_hostname=auth['tls_hostname'],
                                              ssl_version=auth['ssl_version'])
            return dict(base_url=auth['docker_host'],
                        tls=tls_config,
                        version=auth['api_version'],
                        timeout=auth['timeout'])
        # No TLS
        return dict(base_url=auth['docker_host'],
                    version=auth['api_version'],
                    timeout=auth['timeout'])

    def _handle_ssl_error(self, error):
        match = re.match(r"hostname.*doesn\'t match (\'.*\')", str(error))
        if match:
            self.fail("You asked for verification that Docker host name matches %s. The actual hostname is %s. "
                      "Most likely you need to set DOCKER_TLS_HOSTNAME or pass tls_hostname with a value of %s. "
                      "You may also use TLS without verification by setting the tls parameter to true."
                      % (self.auth_params['tls_hostname'], match.group(1), match.group(1)))
        self.fail("SSL Exception: %s" % (error))

    def get_container(self, name=None):
        '''
        Lookup a container and return the inspection results.
        '''
        if name is None:
            return None

        search_name = name
        if not name.startswith('/'):
            search_name = '/' + name

        result = None
        try:
            for container in self.containers(all=True):
                self.log("testing container: %s" % (container['Names']))
                if isinstance(container['Names'], list) and search_name in container['Names']:
                    result = container
                    break
                if container['Id'].startswith(name):
                    result = container
                    break
                if container['Id'] == name:
                    result = container
                    break
        except SSLError as exc:
            self._handle_ssl_error(exc)
        except Exception as exc:
            self.fail("Error retrieving container list: %s" % exc)

        if result is not None:
            try:
                self.log("Inspecting container Id %s" % result['Id'])
                result = self.inspect_container(container=result['Id'])
                self.log("Completed container inspection")
            except Exception as exc:
                self.fail("Error inspecting container: %s" % exc)

        return result

    def find_image(self, name, tag):
        '''
        Lookup an image and return the inspection results.
        '''
        if not name:
            return None

        self.log("Find image %s:%s" % (name, tag))
        images = self._image_lookup(name, tag)
        if len(images) == 0:
            # In API <= 1.20 seeing 'docker.io/<name>' as the name of images pulled from docker hub
            registry, repo_name = auth.resolve_repository_name(name)
            if registry == 'docker.io':
                # the name does not contain a registry, so let's see if docker.io works
                lookup = "docker.io/%s" % name
                self.log("Check for docker.io image: %s" % lookup)
                images = self._image_lookup(lookup, tag)

        if len(images) > 1:
            self.fail("Registry returned more than one result for %s:%s" % (name, tag))

        if len(images) == 1:
            try:
                inspection = self.inspect_image(images[0]['Id'])
            except Exception as exc:
                self.fail("Error inspecting image %s:%s - %s" % (name, tag, str(exc)))
            return inspection

        self.log("Image %s:%s not found." % (name, tag))
        return None

    def _image_lookup(self, name, tag):
        '''
        Including a tag in the name parameter sent to the docker-py images method does not
        work consistently. Instead, get the result set for name and manually check if the tag
        exists.
        '''
        try:
            response = self.images(name=name)
        except Exception as exc:
            self.fail("Error searching for image %s - %s" % (name, str(exc)))
        images = response
        if tag:
            lookup = "%s:%s" % (name, tag)
            images = []
            for image in response:
                tags = image.get('RepoTags')
                if tags and lookup in tags:
                    images = [image]
                    break
        return images

    def pull_image(self, name, tag="latest"):
        '''
        Pull an image
        '''
        self.log("Pulling image %s:%s" % (name, tag))
        old_tag = self.find_image(name, tag)
        try:
            for line in self.pull(name, tag=tag, stream=True, decode=True):
                self.log(line, pretty_print=True)
                if line.get('error'):
                    if line.get('errorDetail'):
                        error_detail = line.get('errorDetail')
                        self.fail("Error pulling %s - code: %s message: %s" % (name,
                                                                               error_detail.get('code'),
                                                                               error_detail.get('message')))
                    else:
                        self.fail("Error pulling %s - %s" % (name, line.get('error')))
        except Exception as exc:
            self.fail("Error pulling image %s:%s - %s" % (name, tag, str(exc)))

        new_tag = self.find_image(name, tag)

        return new_tag, old_tag == new_tag
