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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import os
import platform
import re
import sys
from datetime import timedelta
from distutils.version import LooseVersion


from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible.module_utils.common._collections_compat import Mapping, Sequence
from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE, BOOLEANS_FALSE

HAS_DOCKER_PY = True
HAS_DOCKER_PY_2 = False
HAS_DOCKER_PY_3 = False
HAS_DOCKER_ERROR = None

try:
    from requests.exceptions import SSLError
    from docker import __version__ as docker_version
    from docker.errors import APIError, NotFound, TLSParameterError
    from docker.tls import TLSConfig
    from docker import auth

    if LooseVersion(docker_version) >= LooseVersion('3.0.0'):
        HAS_DOCKER_PY_3 = True
        from docker import APIClient as Client
    elif LooseVersion(docker_version) >= LooseVersion('2.0.0'):
        HAS_DOCKER_PY_2 = True
        from docker import APIClient as Client
    else:
        from docker import Client

except ImportError as exc:
    HAS_DOCKER_ERROR = str(exc)
    HAS_DOCKER_PY = False


# The next 2 imports ``docker.models`` and ``docker.ssladapter`` are used
# to ensure the user does not have both ``docker`` and ``docker-py`` modules
# installed, as they utilize the same namespace are are incompatible
try:
    # docker (Docker SDK for Python >= 2.0.0)
    import docker.models  # noqa: F401
    HAS_DOCKER_MODELS = True
except ImportError:
    HAS_DOCKER_MODELS = False

try:
    # docker-py (Docker SDK for Python < 2.0.0)
    import docker.ssladapter  # noqa: F401
    HAS_DOCKER_SSLADAPTER = True
except ImportError:
    HAS_DOCKER_SSLADAPTER = False


try:
    from requests.exceptions import RequestException
except ImportError:
    # Either docker-py is no longer using requests, or docker-py isn't around either,
    # or docker-py's dependency requests is missing. In any case, define an exception
    # class RequestException so that our code doesn't break.
    class RequestException(Exception):
        pass


DEFAULT_DOCKER_HOST = 'unix://var/run/docker.sock'
DEFAULT_TLS = False
DEFAULT_TLS_VERIFY = False
DEFAULT_TLS_HOSTNAME = 'localhost'
MIN_DOCKER_VERSION = "1.8.0"
DEFAULT_TIMEOUT_SECONDS = 60

DOCKER_COMMON_ARGS = dict(
    docker_host=dict(type='str', default=DEFAULT_DOCKER_HOST, fallback=(env_fallback, ['DOCKER_HOST']), aliases=['docker_url']),
    tls_hostname=dict(type='str', default=DEFAULT_TLS_HOSTNAME, fallback=(env_fallback, ['DOCKER_TLS_HOSTNAME'])),
    api_version=dict(type='str', default='auto', fallback=(env_fallback, ['DOCKER_API_VERSION']), aliases=['docker_api_version']),
    timeout=dict(type='int', default=DEFAULT_TIMEOUT_SECONDS, fallback=(env_fallback, ['DOCKER_TIMEOUT'])),
    ca_cert=dict(type='path', aliases=['tls_ca_cert', 'cacert_path']),
    client_cert=dict(type='path', aliases=['tls_client_cert', 'cert_path']),
    client_key=dict(type='path', aliases=['tls_client_key', 'key_path']),
    ssl_version=dict(type='str', fallback=(env_fallback, ['DOCKER_SSL_VERSION'])),
    tls=dict(type='bool', default=DEFAULT_TLS, fallback=(env_fallback, ['DOCKER_TLS'])),
    validate_certs=dict(type='bool', default=DEFAULT_TLS_VERIFY, fallback=(env_fallback, ['DOCKER_TLS_VERIFY']), aliases=['tls_verify']),
    debug=dict(type='bool', default=False)
)

DOCKER_MUTUALLY_EXCLUSIVE = []

DOCKER_REQUIRED_TOGETHER = [
    ['client_cert', 'client_key']
]

DEFAULT_DOCKER_REGISTRY = 'https://index.docker.io/v1/'
EMAIL_REGEX = r'[^@]+@[^@]+\.[^@]+'
BYTE_SUFFIXES = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


if not HAS_DOCKER_PY:
    docker_version = None

    # No Docker SDK for Python. Create a place holder client to allow
    # instantiation of AnsibleModule and proper error handing
    class Client(object):  # noqa: F811
        def __init__(self, **kwargs):
            pass

    class APIError(Exception):  # noqa: F811
        pass

    class NotFound(Exception):  # noqa: F811
        pass


def is_image_name_id(name):
    """Check whether the given image name is in fact an image ID (hash)."""
    if re.match('^sha256:[0-9a-fA-F]{64}$', name):
        return True
    return False


def is_valid_tag(tag, allow_empty=False):
    """Check whether the given string is a valid docker tag name."""
    if not tag:
        return allow_empty
    # See here ("Extended description") for a definition what tags can be:
    # https://docs.docker.com/engine/reference/commandline/tag/
    return bool(re.match('^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$', tag))


def sanitize_result(data):
    """Sanitize data object for return to Ansible.

    When the data object contains types such as docker.types.containers.HostConfig,
    Ansible will fail when these are returned via exit_json or fail_json.
    HostConfig is derived from dict, but its constructor requires additional
    arguments. This function sanitizes data structures by recursively converting
    everything derived from dict to dict and everything derived from list (and tuple)
    to a list.
    """
    if isinstance(data, dict):
        return dict((k, sanitize_result(v)) for k, v in data.items())
    elif isinstance(data, (list, tuple)):
        return [sanitize_result(v) for v in data]
    else:
        return data


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


def update_tls_hostname(result):
    if result['tls_hostname'] is None:
        # get default machine name from the url
        parsed_url = urlparse(result['docker_host'])
        if ':' in parsed_url.netloc:
            result['tls_hostname'] = parsed_url.netloc[:parsed_url.netloc.rindex(':')]
        else:
            result['tls_hostname'] = parsed_url


def _get_tls_config(fail_function, **kwargs):
    try:
        tls_config = TLSConfig(**kwargs)
        return tls_config
    except TLSParameterError as exc:
        fail_function("TLS config error: %s" % exc)


def get_connect_params(auth, fail_function):
    if auth['tls'] or auth['tls_verify']:
        auth['docker_host'] = auth['docker_host'].replace('tcp://', 'https://')

    if auth['tls_verify'] and auth['cert_path'] and auth['key_path']:
        # TLS with certs and host verification
        if auth['cacert_path']:
            tls_config = _get_tls_config(client_cert=(auth['cert_path'], auth['key_path']),
                                         ca_cert=auth['cacert_path'],
                                         verify=True,
                                         assert_hostname=auth['tls_hostname'],
                                         ssl_version=auth['ssl_version'],
                                         fail_function=fail_function)
        else:
            tls_config = _get_tls_config(client_cert=(auth['cert_path'], auth['key_path']),
                                         verify=True,
                                         assert_hostname=auth['tls_hostname'],
                                         ssl_version=auth['ssl_version'],
                                         fail_function=fail_function)

        return dict(base_url=auth['docker_host'],
                    tls=tls_config,
                    version=auth['api_version'],
                    timeout=auth['timeout'])

    if auth['tls_verify'] and auth['cacert_path']:
        # TLS with cacert only
        tls_config = _get_tls_config(ca_cert=auth['cacert_path'],
                                     assert_hostname=auth['tls_hostname'],
                                     verify=True,
                                     ssl_version=auth['ssl_version'],
                                     fail_function=fail_function)
        return dict(base_url=auth['docker_host'],
                    tls=tls_config,
                    version=auth['api_version'],
                    timeout=auth['timeout'])

    if auth['tls_verify']:
        # TLS with verify and no certs
        tls_config = _get_tls_config(verify=True,
                                     assert_hostname=auth['tls_hostname'],
                                     ssl_version=auth['ssl_version'],
                                     fail_function=fail_function)
        return dict(base_url=auth['docker_host'],
                    tls=tls_config,
                    version=auth['api_version'],
                    timeout=auth['timeout'])

    if auth['tls'] and auth['cert_path'] and auth['key_path']:
        # TLS with certs and no host verification
        tls_config = _get_tls_config(client_cert=(auth['cert_path'], auth['key_path']),
                                     verify=False,
                                     ssl_version=auth['ssl_version'],
                                     fail_function=fail_function)
        return dict(base_url=auth['docker_host'],
                    tls=tls_config,
                    version=auth['api_version'],
                    timeout=auth['timeout'])

    if auth['tls']:
        # TLS with no certs and not host verification
        tls_config = _get_tls_config(verify=False,
                                     ssl_version=auth['ssl_version'],
                                     fail_function=fail_function)
        return dict(base_url=auth['docker_host'],
                    tls=tls_config,
                    version=auth['api_version'],
                    timeout=auth['timeout'])

    # No TLS
    return dict(base_url=auth['docker_host'],
                version=auth['api_version'],
                timeout=auth['timeout'])


DOCKERPYUPGRADE_SWITCH_TO_DOCKER = "Try `pip uninstall docker-py` followed by `pip install docker`."
DOCKERPYUPGRADE_UPGRADE_DOCKER = "Use `pip install --upgrade docker` to upgrade."
DOCKERPYUPGRADE_RECOMMEND_DOCKER = ("Use `pip install --upgrade docker-py` to upgrade. "
                                    "Hint: if you do not need Python 2.6 support, try "
                                    "`pip uninstall docker-py` instead, followed by `pip install docker`.")


class AnsibleDockerClient(Client):

    def __init__(self, argument_spec=None, supports_check_mode=False, mutually_exclusive=None,
                 required_together=None, required_if=None, min_docker_version=MIN_DOCKER_VERSION,
                 min_docker_api_version=None, option_minimal_versions=None,
                 option_minimal_versions_ignore_params=None, fail_results=None):

        # Modules can put information in here which will always be returned
        # in case client.fail() is called.
        self.fail_results = fail_results or {}

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

        NEEDS_DOCKER_PY2 = (LooseVersion(min_docker_version) >= LooseVersion('2.0.0'))

        self.docker_py_version = LooseVersion(docker_version)

        if HAS_DOCKER_MODELS and HAS_DOCKER_SSLADAPTER:
            self.fail("Cannot have both the docker-py and docker python modules (old and new version of Docker "
                      "SDK for Python) installed together as they use the same namespace and cause a corrupt "
                      "installation. Please uninstall both packages, and re-install only the docker-py or docker "
                      "python module (for %s's Python %s). It is recommended to install the docker module if no "
                      "support for Python 2.6 is required. Please note that simply uninstalling one of the modules "
                      "can leave the other module in a broken state." % (platform.node(), sys.executable))

        if not HAS_DOCKER_PY:
            if NEEDS_DOCKER_PY2:
                msg = missing_required_lib("Docker SDK for Python: docker")
                msg = msg + ", for example via `pip install docker`. The error was: %s"
            else:
                msg = missing_required_lib("Docker SDK for Python: docker (Python >= 2.7) or docker-py (Python 2.6)")
                msg = msg + ", for example via `pip install docker` or `pip install docker-py` (Python 2.6). The error was: %s"
            self.fail(msg % HAS_DOCKER_ERROR)

        if self.docker_py_version < LooseVersion(min_docker_version):
            msg = "Error: Docker SDK for Python version is %s (%s's Python %s). Minimum version required is %s."
            if not NEEDS_DOCKER_PY2:
                # The minimal required version is < 2.0 (and the current version as well).
                # Advertise docker (instead of docker-py) for non-Python-2.6 users.
                msg += DOCKERPYUPGRADE_RECOMMEND_DOCKER
            elif docker_version < LooseVersion('2.0'):
                msg += DOCKERPYUPGRADE_SWITCH_TO_DOCKER
            else:
                msg += DOCKERPYUPGRADE_UPGRADE_DOCKER
            self.fail(msg % (docker_version, platform.node(), sys.executable, min_docker_version))

        self.debug = self.module.params.get('debug')
        self.check_mode = self.module.check_mode
        self._connect_params = get_connect_params(self.auth_params, fail_function=self.fail)

        try:
            super(AnsibleDockerClient, self).__init__(**self._connect_params)
            self.docker_api_version_str = self.version()['ApiVersion']
        except APIError as exc:
            self.fail("Docker API error: %s" % exc)
        except Exception as exc:
            self.fail("Error connecting: %s" % exc)

        self.docker_api_version = LooseVersion(self.docker_api_version_str)
        if min_docker_api_version is not None:
            if self.docker_api_version < LooseVersion(min_docker_api_version):
                self.fail('Docker API version is %s. Minimum version required is %s.' % (self.docker_api_version_str, min_docker_api_version))

        if option_minimal_versions is not None:
            self._get_minimal_versions(option_minimal_versions, option_minimal_versions_ignore_params)

    def log(self, msg, pretty_print=False):
        pass
        # if self.debug:
        #     log_file = open('docker.log', 'a')
        #     if pretty_print:
        #         log_file.write(json.dumps(msg, sort_keys=True, indent=4, separators=(',', ': ')))
        #         log_file.write(u'\n')
        #     else:
        #         log_file.write(msg + u'\n')

    def fail(self, msg, **kwargs):
        self.fail_results.update(kwargs)
        self.module.fail_json(msg=msg, **sanitize_result(self.fail_results))

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
                params['validate_certs'] = True

        result = dict(
            docker_host=self._get_value('docker_host', params['docker_host'], 'DOCKER_HOST',
                                        DEFAULT_DOCKER_HOST),
            tls_hostname=self._get_value('tls_hostname', params['tls_hostname'],
                                         'DOCKER_TLS_HOSTNAME', DEFAULT_TLS_HOSTNAME),
            api_version=self._get_value('api_version', params['api_version'], 'DOCKER_API_VERSION',
                                        'auto'),
            cacert_path=self._get_value('cacert_path', params['ca_cert'], 'DOCKER_CERT_PATH', None),
            cert_path=self._get_value('cert_path', params['client_cert'], 'DOCKER_CERT_PATH', None),
            key_path=self._get_value('key_path', params['client_key'], 'DOCKER_CERT_PATH', None),
            ssl_version=self._get_value('ssl_version', params['ssl_version'], 'DOCKER_SSL_VERSION', None),
            tls=self._get_value('tls', params['tls'], 'DOCKER_TLS', DEFAULT_TLS),
            tls_verify=self._get_value('tls_verfy', params['validate_certs'], 'DOCKER_TLS_VERIFY',
                                       DEFAULT_TLS_VERIFY),
            timeout=self._get_value('timeout', params['timeout'], 'DOCKER_TIMEOUT',
                                    DEFAULT_TIMEOUT_SECONDS),
        )

        update_tls_hostname(result)

        return result

    def _handle_ssl_error(self, error):
        match = re.match(r"hostname.*doesn\'t match (\'.*\')", str(error))
        if match:
            self.fail("You asked for verification that Docker daemons certificate's hostname matches %s. "
                      "The actual certificate's hostname is %s. Most likely you need to set DOCKER_TLS_HOSTNAME "
                      "or pass `tls_hostname` with a value of %s. You may also use TLS without verification by "
                      "setting the `tls` parameter to true."
                      % (self.auth_params['tls_hostname'], match.group(1), match.group(1)))
        self.fail("SSL Exception: %s" % (error))

    def _get_minimal_versions(self, option_minimal_versions, ignore_params=None):
        self.option_minimal_versions = dict()
        for option in self.module.argument_spec:
            if ignore_params is not None:
                if option in ignore_params:
                    continue
            self.option_minimal_versions[option] = dict()
        self.option_minimal_versions.update(option_minimal_versions)

        for option, data in self.option_minimal_versions.items():
            # Test whether option is supported, and store result
            support_docker_py = True
            support_docker_api = True
            if 'docker_py_version' in data:
                support_docker_py = self.docker_py_version >= LooseVersion(data['docker_py_version'])
            if 'docker_api_version' in data:
                support_docker_api = self.docker_api_version >= LooseVersion(data['docker_api_version'])
            data['supported'] = support_docker_py and support_docker_api
            # Fail if option is not supported but used
            if not data['supported']:
                # Test whether option is specified
                if 'detect_usage' in data:
                    used = data['detect_usage'](self)
                else:
                    used = self.module.params.get(option) is not None
                    if used and 'default' in self.module.argument_spec[option]:
                        used = self.module.params[option] != self.module.argument_spec[option]['default']
                if used:
                    # If the option is used, compose error message.
                    if 'usage_msg' in data:
                        usg = data['usage_msg']
                    else:
                        usg = 'set %s option' % (option, )
                    if not support_docker_api:
                        msg = 'Docker API version is %s. Minimum version required is %s to %s.'
                        msg = msg % (self.docker_api_version_str, data['docker_api_version'], usg)
                    elif not support_docker_py:
                        msg = "Docker SDK for Python version is %s (%s's Python %s). Minimum version required is %s to %s. "
                        if LooseVersion(data['docker_py_version']) < LooseVersion('2.0.0'):
                            msg += DOCKERPYUPGRADE_RECOMMEND_DOCKER
                        elif self.docker_py_version < LooseVersion('2.0.0'):
                            msg += DOCKERPYUPGRADE_SWITCH_TO_DOCKER
                        else:
                            msg += DOCKERPYUPGRADE_UPGRADE_DOCKER
                        msg = msg % (docker_version, platform.node(), sys.executable, data['docker_py_version'], usg)
                    else:
                        # should not happen
                        msg = 'Cannot %s with your configuration.' % (usg, )
                    self.fail(msg)

    def get_container_by_id(self, container_id):
        try:
            self.log("Inspecting container Id %s" % container_id)
            result = self.inspect_container(container=container_id)
            self.log("Completed container inspection")
            return result
        except NotFound as dummy:
            return None
        except Exception as exc:
            self.fail("Error inspecting container: %s" % exc)

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

        if result is None:
            return None

        return self.get_container_by_id(result['Id'])

    def get_network(self, name=None, network_id=None):
        '''
        Lookup a network and return the inspection results.
        '''
        if name is None and network_id is None:
            return None

        result = None

        if network_id is None:
            try:
                for network in self.networks():
                    self.log("testing network: %s" % (network['Name']))
                    if name == network['Name']:
                        result = network
                        break
                    if network['Id'].startswith(name):
                        result = network
                        break
            except SSLError as exc:
                self._handle_ssl_error(exc)
            except Exception as exc:
                self.fail("Error retrieving network list: %s" % exc)

        if result is not None:
            network_id = result['Id']

        if network_id is not None:
            try:
                self.log("Inspecting network Id %s" % network_id)
                result = self.inspect_network(network_id)
                self.log("Completed network inspection")
            except NotFound as dummy:
                return None
            except Exception as exc:
                self.fail("Error inspecting network: %s" % exc)

        return result

    def find_image(self, name, tag):
        '''
        Lookup an image (by name and tag) and return the inspection results.
        '''
        if not name:
            return None

        self.log("Find image %s:%s" % (name, tag))
        images = self._image_lookup(name, tag)
        if not images:
            # In API <= 1.20 seeing 'docker.io/<name>' as the name of images pulled from docker hub
            registry, repo_name = auth.resolve_repository_name(name)
            if registry == 'docker.io':
                # If docker.io is explicitly there in name, the image
                # isn't found in some cases (#41509)
                self.log("Check for docker.io image: %s" % repo_name)
                images = self._image_lookup(repo_name, tag)
                if not images and repo_name.startswith('library/'):
                    # Sometimes library/xxx images are not found
                    lookup = repo_name[len('library/'):]
                    self.log("Check for docker.io image: %s" % lookup)
                    images = self._image_lookup(lookup, tag)
                if not images:
                    # Last case: if docker.io wasn't there, it can be that
                    # the image wasn't found either (#15586)
                    lookup = "%s/%s" % (registry, repo_name)
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

    def find_image_by_id(self, image_id):
        '''
        Lookup an image (by ID) and return the inspection results.
        '''
        if not image_id:
            return None

        self.log("Find image %s (by ID)" % image_id)
        try:
            inspection = self.inspect_image(image_id)
        except Exception as exc:
            self.fail("Error inspecting image ID %s - %s" % (image_id, str(exc)))
        return inspection

    def _image_lookup(self, name, tag):
        '''
        Including a tag in the name parameter sent to the Docker SDK for Python images method
        does not work consistently. Instead, get the result set for name and manually check
        if the tag exists.
        '''
        try:
            response = self.images(name=name)
        except Exception as exc:
            self.fail("Error searching for image %s - %s" % (name, str(exc)))
        images = response
        if tag:
            lookup = "%s:%s" % (name, tag)
            lookup_digest = "%s@%s" % (name, tag)
            images = []
            for image in response:
                tags = image.get('RepoTags')
                digests = image.get('RepoDigests')
                if (tags and lookup in tags) or (digests and lookup_digest in digests):
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

    def report_warnings(self, result, warnings_key=None):
        '''
        Checks result of client operation for warnings, and if present, outputs them.

        warnings_key should be a list of keys used to crawl the result dictionary.
        For example, if warnings_key == ['a', 'b'], the function will consider
        result['a']['b'] if these keys exist. If the result is a non-empty string, it
        will be reported as a warning. If the result is a list, every entry will be
        reported as a warning.

        In most cases (if warnings are returned at all), warnings_key should be
        ['Warnings'] or ['Warning']. The default value (if not specified) is ['Warnings'].
        '''
        if warnings_key is None:
            warnings_key = ['Warnings']
        for key in warnings_key:
            if not isinstance(result, Mapping):
                return
            result = result.get(key)
        if isinstance(result, Sequence):
            for warning in result:
                self.module.warn('Docker warning: {0}'.format(warning))
        elif isinstance(result, string_types) and result:
            self.module.warn('Docker warning: {0}'.format(result))

    def inspect_distribution(self, image, **kwargs):
        '''
        Get image digest by directly calling the Docker API when running Docker SDK < 4.0.0
        since prior versions did not support accessing private repositories.
        '''
        if self.docker_py_version < LooseVersion('4.0.0'):
            registry = auth.resolve_repository_name(image)[0]
            header = auth.get_config_header(self, registry)
            if header:
                return self._result(self._get(
                    self._url('/distribution/{0}/json', image),
                    headers={'X-Registry-Auth': header}
                ), json=True)
        return super(AnsibleDockerClient, self).inspect_distribution(image, **kwargs)


def compare_dict_allow_more_present(av, bv):
    '''
    Compare two dictionaries for whether every entry of the first is in the second.
    '''
    for key, value in av.items():
        if key not in bv:
            return False
        if bv[key] != value:
            return False
    return True


def compare_generic(a, b, method, datatype):
    '''
    Compare values a and b as described by method and datatype.

    Returns ``True`` if the values compare equal, and ``False`` if not.

    ``a`` is usually the module's parameter, while ``b`` is a property
    of the current object. ``a`` must not be ``None`` (except for
    ``datatype == 'value'``).

    Valid values for ``method`` are:
    - ``ignore`` (always compare as equal);
    - ``strict`` (only compare if really equal)
    - ``allow_more_present`` (allow b to have elements which a does not have).

    Valid values for ``datatype`` are:
    - ``value``: for simple values (strings, numbers, ...);
    - ``list``: for ``list``s or ``tuple``s where order matters;
    - ``set``: for ``list``s, ``tuple``s or ``set``s where order does not
      matter;
    - ``set(dict)``: for ``list``s, ``tuple``s or ``sets`` where order does
      not matter and which contain ``dict``s; ``allow_more_present`` is used
      for the ``dict``s, and these are assumed to be dictionaries of values;
    - ``dict``: for dictionaries of values.
    '''
    if method == 'ignore':
        return True
    # If a or b is None:
    if a is None or b is None:
        # If both are None: equality
        if a == b:
            return True
        # Otherwise, not equal for values, and equal
        # if the other is empty for set/list/dict
        if datatype == 'value':
            return False
        # For allow_more_present, allow a to be None
        if method == 'allow_more_present' and a is None:
            return True
        # Otherwise, the iterable object which is not None must have length 0
        return len(b if a is None else a) == 0
    # Do proper comparison (both objects not None)
    if datatype == 'value':
        return a == b
    elif datatype == 'list':
        if method == 'strict':
            return a == b
        else:
            i = 0
            for v in a:
                while i < len(b) and b[i] != v:
                    i += 1
                if i == len(b):
                    return False
                i += 1
            return True
    elif datatype == 'dict':
        if method == 'strict':
            return a == b
        else:
            return compare_dict_allow_more_present(a, b)
    elif datatype == 'set':
        set_a = set(a)
        set_b = set(b)
        if method == 'strict':
            return set_a == set_b
        else:
            return set_b >= set_a
    elif datatype == 'set(dict)':
        for av in a:
            found = False
            for bv in b:
                if compare_dict_allow_more_present(av, bv):
                    found = True
                    break
            if not found:
                return False
        if method == 'strict':
            # If we would know that both a and b do not contain duplicates,
            # we could simply compare len(a) to len(b) to finish this test.
            # We can assume that b has no duplicates (as it is returned by
            # docker), but we don't know for a.
            for bv in b:
                found = False
                for av in a:
                    if compare_dict_allow_more_present(av, bv):
                        found = True
                        break
                if not found:
                    return False
        return True


class DifferenceTracker(object):
    def __init__(self):
        self._diff = []

    def add(self, name, parameter=None, active=None):
        self._diff.append(dict(
            name=name,
            parameter=parameter,
            active=active,
        ))

    def merge(self, other_tracker):
        self._diff.extend(other_tracker._diff)

    @property
    def empty(self):
        return len(self._diff) == 0

    def get_before_after(self):
        '''
        Return texts ``before`` and ``after``.
        '''
        before = dict()
        after = dict()
        for item in self._diff:
            before[item['name']] = item['active']
            after[item['name']] = item['parameter']
        return before, after

    def has_difference_for(self, name):
        '''
        Returns a boolean if a difference exists for name
        '''
        return any(diff for diff in self._diff if diff['name'] == name)

    def get_legacy_docker_container_diffs(self):
        '''
        Return differences in the docker_container legacy format.
        '''
        result = []
        for entry in self._diff:
            item = dict()
            item[entry['name']] = dict(
                parameter=entry['parameter'],
                container=entry['active'],
            )
            result.append(item)
        return result

    def get_legacy_docker_diffs(self):
        '''
        Return differences in the docker_container legacy format.
        '''
        result = [entry['name'] for entry in self._diff]
        return result


def clean_dict_booleans_for_docker_api(data):
    '''
    Go doesn't like Python booleans 'True' or 'False', while Ansible is just
    fine with them in YAML. As such, they need to be converted in cases where
    we pass dictionaries to the Docker API (e.g. docker_network's
    driver_options and docker_prune's filters).
    '''
    result = dict()
    if data is not None:
        for k, v in data.items():
            if v is True:
                v = 'true'
            elif v is False:
                v = 'false'
            else:
                v = str(v)
            result[str(k)] = v
    return result


def convert_duration_to_nanosecond(time_str):
    """
    Return time duration in nanosecond.
    """
    if not isinstance(time_str, str):
        raise ValueError('Missing unit in duration - %s' % time_str)

    regex = re.compile(
        r'^(((?P<hours>\d+)h)?'
        r'((?P<minutes>\d+)m(?!s))?'
        r'((?P<seconds>\d+)s)?'
        r'((?P<milliseconds>\d+)ms)?'
        r'((?P<microseconds>\d+)us)?)$'
    )
    parts = regex.match(time_str)

    if not parts:
        raise ValueError('Invalid time duration - %s' % time_str)

    parts = parts.groupdict()
    time_params = {}
    for (name, value) in parts.items():
        if value:
            time_params[name] = int(value)

    delta = timedelta(**time_params)
    time_in_nanoseconds = (
        delta.microseconds + (delta.seconds + delta.days * 24 * 3600) * 10 ** 6
    ) * 10 ** 3

    return time_in_nanoseconds


def parse_healthcheck(healthcheck):
    """
    Return dictionary of healthcheck parameters and boolean if
    healthcheck defined in image was requested to be disabled.
    """
    if (not healthcheck) or (not healthcheck.get('test')):
        return None, None

    result = dict()

    # All supported healthcheck parameters
    options = dict(
        test='test',
        interval='interval',
        timeout='timeout',
        start_period='start_period',
        retries='retries'
    )

    duration_options = ['interval', 'timeout', 'start_period']

    for (key, value) in options.items():
        if value in healthcheck:
            if healthcheck.get(value) is None:
                # due to recursive argument_spec, all keys are always present
                # (but have default value None if not specified)
                continue
            if value in duration_options:
                time = convert_duration_to_nanosecond(healthcheck.get(value))
                if time:
                    result[key] = time
            elif healthcheck.get(value):
                result[key] = healthcheck.get(value)
                if key == 'test':
                    if isinstance(result[key], (tuple, list)):
                        result[key] = [str(e) for e in result[key]]
                    else:
                        result[key] = ['CMD-SHELL', str(result[key])]
                elif key == 'retries':
                    try:
                        result[key] = int(result[key])
                    except ValueError:
                        raise ValueError(
                            'Cannot parse number of retries for healthcheck. '
                            'Expected an integer, got "{0}".'.format(result[key])
                        )

    if result['test'] == ['NONE']:
        # If the user explicitly disables the healthcheck, return None
        # as the healthcheck object, and set disable_healthcheck to True
        return None, True

    return result, False


def omit_none_from_dict(d):
    """
    Return a copy of the dictionary with all keys with value None omitted.
    """
    return dict((k, v) for (k, v) in d.items() if v is not None)
