# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import copy
import os
import re
import datetime

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.connection import exec_command
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.six import iteritems
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE
from ansible.module_utils.parsing.convert_bool import BOOLEANS_FALSE
from collections import defaultdict


MANAGED_BY_ANNOTATION_VERSION = 'f5-ansible.version'
MANAGED_BY_ANNOTATION_MODIFIED = 'f5-ansible.last_modified'


f5_provider_spec = {
    'server': dict(
        fallback=(env_fallback, ['F5_SERVER'])
    ),
    'server_port': dict(
        type='int',
        default=443,
        fallback=(env_fallback, ['F5_SERVER_PORT'])
    ),
    'user': dict(
        fallback=(env_fallback, ['F5_USER', 'ANSIBLE_NET_USERNAME'])
    ),
    'password': dict(
        no_log=True,
        aliases=['pass', 'pwd'],
        fallback=(env_fallback, ['F5_PASSWORD', 'ANSIBLE_NET_PASSWORD'])
    ),
    'ssh_keyfile': dict(
        type='path'
    ),
    'validate_certs': dict(
        type='bool',
        default='yes',
        fallback=(env_fallback, ['F5_VALIDATE_CERTS'])
    ),
    'transport': dict(
        choices=['cli', 'rest'],
        default='rest'
    ),
    'timeout': dict(type='int'),
    'auth_provider': dict(),
}

f5_argument_spec = {
    'provider': dict(type='dict', options=f5_provider_spec),
}


def get_provider_argspec():
    return f5_provider_spec


def load_params(params):
    provider = params.get('provider') or dict()
    for key, value in iteritems(provider):
        if key in f5_argument_spec:
            if params.get(key) is None and value is not None:
                params[key] = value


def is_empty_list(seq):
    if len(seq) == 1:
        if seq[0] == '' or seq[0] == 'none':
            return True
    return False


def fq_name(partition, value, sub_path=''):
    """Returns a 'Fully Qualified' name

    A BIG-IP expects most names of resources to be in a fully-qualified
    form. This means that both the simple name, and the partition need
    to be combined.

    The Ansible modules, however, can accept (as names for several
    resources) their name in the FQ format. This becomes an issue when
    the FQ name and the partition are both specified as separate values.

    Consider the following examples.

        # Name not FQ
        name: foo
        partition: Common

        # Name FQ
        name: /Common/foo
        partition: Common

    This method will rectify the above situation and will, in both cases,
    return the following for name.

        /Common/foo

    Args:
        partition (string): The partition that you would want attached to
            the name if the name has no partition.
        value (string): The name that you want to attach a partition to.
            This value will be returned unchanged if it has a partition
            attached to it already.
        sub_path (string): The sub path element. If defined the sub_path
            will be inserted between partition and value.
            This will also work on FQ names.
    Returns:
        string: The fully qualified name, given the input parameters.
    """
    if value is not None and sub_path == '':
        try:
            int(value)
            return '/{0}/{1}'.format(partition, value)
        except (ValueError, TypeError):
            if not value.startswith('/'):
                return '/{0}/{1}'.format(partition, value)
    if value is not None and sub_path != '':
        try:
            int(value)
            return '/{0}/{1}/{2}'.format(partition, sub_path, value)
        except (ValueError, TypeError):
            if value.startswith('/'):
                dummy, partition, name = value.split('/')
                return '/{0}/{1}/{2}'.format(partition, sub_path, name)
            if not value.startswith('/'):
                return '/{0}/{1}/{2}'.format(partition, sub_path, value)
    return value


# Fully Qualified name (with partition) for a list
def fq_list_names(partition, list_names):
    if list_names is None:
        return None
    return map(lambda x: fq_name(partition, x), list_names)


def to_commands(module, commands):
    spec = {
        'command': dict(key=True),
        'prompt': dict(),
        'answer': dict()
    }
    transform = ComplexList(spec, module)
    return transform(commands)


def run_commands(module, commands, check_rc=True):
    responses = list()
    commands = to_commands(module, to_list(commands))
    for cmd in commands:
        cmd = module.jsonify(cmd)
        rc, out, err = exec_command(module, cmd)
        if check_rc and rc != 0:
            raise F5ModuleError(to_text(err, errors='surrogate_then_replace'))
        result = to_text(out, errors='surrogate_then_replace')
        responses.append(result)
    return responses


def flatten_boolean(value):
    truthy = list(BOOLEANS_TRUE) + ['enabled', 'True', 'true']
    falsey = list(BOOLEANS_FALSE) + ['disabled', 'False', 'false']
    if value is None:
        return None
    elif value in truthy:
        return 'yes'
    elif value in falsey:
        return 'no'


def is_cli(module):
    transport = module.params['transport']
    provider_transport = (module.params['provider'] or {}).get('transport')
    result = 'cli' in (transport, provider_transport)
    return result


def is_valid_hostname(host):
    """Reasonable attempt at validating a hostname

    Compiled from various paragraphs outlined here
    https://tools.ietf.org/html/rfc3696#section-2
    https://tools.ietf.org/html/rfc1123

    Notably,
    * Host software MUST handle host names of up to 63 characters and
      SHOULD handle host names of up to 255 characters.
    * The "LDH rule", after the characters that it permits. (letters, digits, hyphen)
    * If the hyphen is used, it is not permitted to appear at
      either the beginning or end of a label

    :param host:
    :return:
    """
    if len(host) > 255:
        return False
    host = host.rstrip(".")
    allowed = re.compile(r'(?!-)[A-Z0-9-]{1,63}(?<!-)$', re.IGNORECASE)
    result = all(allowed.match(x) for x in host.split("."))
    return result


def is_valid_fqdn(host):
    """Reasonable attempt at validating a hostname

    Compiled from various paragraphs outlined here
    https://tools.ietf.org/html/rfc3696#section-2
    https://tools.ietf.org/html/rfc1123

    Notably,
    * Host software MUST handle host names of up to 63 characters and
      SHOULD handle host names of up to 255 characters.
    * The "LDH rule", after the characters that it permits. (letters, digits, hyphen)
    * If the hyphen is used, it is not permitted to appear at
      either the beginning or end of a label

    :param host:
    :return:
    """
    if len(host) > 255:
        return False
    host = host.rstrip(".")
    allowed = re.compile(r'(?!-)[A-Z0-9-]{1,63}(?<!-)$', re.IGNORECASE)
    result = all(allowed.match(x) for x in host.split("."))
    if result:
        parts = host.split('.')
        if len(parts) > 1:
            return True
    return False


def transform_name(partition='', name='', sub_path=''):
    if partition != '':
        if name.startswith(partition + '/'):
            name = name.replace(partition + '/', '')
        if name.startswith('/' + partition + '/'):
            name = name.replace('/' + partition + '/', '')

    if name:
        name = name.replace('/', '~')
        name = name.replace('%', '%25')

    if partition:
        partition = partition.replace('/', '~')
        if not partition.startswith('~'):
            partition = '~' + partition
    else:
        if sub_path:
            raise F5ModuleError(
                'When giving the subPath component include partition as well.'
            )

    if sub_path and partition:
        sub_path = '~' + sub_path

    if name and partition:
        name = '~' + name

    result = partition + sub_path + name
    return result


def is_ansible_debug(module):
    if module._debug and module._verbosity >= 4:
        return True
    return False


def is_uuid(uuid=None):
    """Check to see if value is an F5 UUID

    UUIDs are used in BIG-IQ and in select areas of BIG-IP (notably ASM). This method
    will check to see if the provided value matches a UUID as known by these products.

    Args:
        uuid (string): The value to check for UUID-ness

    Returns:
        bool:
    """
    if uuid is None:
        return False
    pattern = r'[A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12}'
    if re.match(pattern, uuid):
        return True
    return False


def on_bigip():
    if os.path.exists('/usr/bin/tmsh'):
        return True
    return False


def mark_managed_by(ansible_version, params):
    metadata = []
    result = copy.deepcopy(params)
    found1 = False
    found2 = False
    mark1 = dict(
        name=MANAGED_BY_ANNOTATION_VERSION,
        value=ansible_version,
        persist='true'
    )
    mark2 = dict(
        name=MANAGED_BY_ANNOTATION_MODIFIED,
        value=str(datetime.datetime.utcnow()),
        persist='true'
    )

    if 'metadata' not in result:
        result['metadata'] = [mark1, mark2]
        return result

    for x in params['metadata']:
        if x['name'] == MANAGED_BY_ANNOTATION_VERSION:
            found1 = True
            metadata.append(mark1)
        if x['name'] == MANAGED_BY_ANNOTATION_MODIFIED:
            found2 = True
            metadata.append(mark1)
        else:
            metadata.append(x)
    if not found1:
        metadata.append(mark1)
    if not found2:
        metadata.append(mark2)

    result['metadata'] = metadata
    return result


def only_has_managed_metadata(metadata):
    managed = [
        MANAGED_BY_ANNOTATION_MODIFIED,
        MANAGED_BY_ANNOTATION_VERSION,
    ]

    for x in metadata:
        if x['name'] not in managed:
            return False
    return True


class Noop(object):
    """Represent no-operation required

    This class is used in the Difference engine to specify when an attribute
    has not changed. Difference attributes may return an instance of this
    class as a means to indicate when the attribute has not changed.

    The Noop object allows attributes to be set to None when sending updates
    to the API. `None` is technically a valid value in some cases (it indicates
    that the attribute should be removed from the resource).
    """
    pass


class F5BaseClient(object):
    def __init__(self, *args, **kwargs):
        self.params = kwargs
        self.module = kwargs.get('module', None)
        load_params(self.params)
        self._client = None

    @property
    def api(self):
        raise F5ModuleError("Management root must be used from the concrete product classes.")

    def reconnect(self):
        """Attempts to reconnect to a device

        The existing token from a ManagementRoot can become invalid if you,
        for example, upgrade the device (such as is done in the *_software
        module.

        This method can be used to reconnect to a remote device without
        having to re-instantiate the ArgumentSpec and AnsibleF5Client classes
        it will use the same values that were initially provided to those
        classes

        :return:
        :raises iControlUnexpectedHTTPError
        """
        self._client = None

    @staticmethod
    def validate_params(key, store):
        if key in store and store[key] is not None:
            return True
        else:
            return False

    def merge_provider_params(self):
        result = dict()
        provider = self.params.get('provider', None)
        if not provider:
            provider = {}

        self.merge_provider_server_param(result, provider)
        self.merge_provider_server_port_param(result, provider)
        self.merge_provider_validate_certs_param(result, provider)
        self.merge_provider_auth_provider_param(result, provider)
        self.merge_provider_user_param(result, provider)
        self.merge_provider_password_param(result, provider)

        return result

    def merge_provider_server_param(self, result, provider):
        if self.validate_params('server', provider):
            result['server'] = provider['server']
        elif self.validate_params('F5_SERVER', os.environ):
            result['server'] = os.environ['F5_SERVER']
        else:
            raise F5ModuleError('Server parameter cannot be None or missing, please provide a valid value')

    def merge_provider_server_port_param(self, result, provider):
        if self.validate_params('server_port', provider):
            result['server_port'] = provider['server_port']
        elif self.validate_params('F5_SERVER_PORT', os.environ):
            result['server_port'] = os.environ['F5_SERVER_PORT']
        else:
            result['server_port'] = 443

    def merge_provider_validate_certs_param(self, result, provider):
        if self.validate_params('validate_certs', provider):
            result['validate_certs'] = provider['validate_certs']
        elif self.validate_params('F5_VALIDATE_CERTS', os.environ):
            result['validate_certs'] = os.environ['F5_VALIDATE_CERTS']
        else:
            result['validate_certs'] = True
        if result['validate_certs'] in BOOLEANS_TRUE:
            result['validate_certs'] = True
        else:
            result['validate_certs'] = False

    def merge_provider_auth_provider_param(self, result, provider):
        if self.validate_params('auth_provider', provider):
            result['auth_provider'] = provider['auth_provider']
        elif self.validate_params('F5_AUTH_PROVIDER', os.environ):
            result['auth_provider'] = os.environ['F5_AUTH_PROVIDER']
        else:
            result['auth_provider'] = None

        # Handle a specific case of the user specifying ``|default(omit)``
        # as the value to the auth_provider.
        #
        # In this case, Ansible will inject the omit-placeholder value
        # and the module params incorrectly interpret this. This case
        # can occur when specifying ``|default(omit)`` for a variable
        # value defined in the ``environment`` section of a Play.
        #
        # An example of the omit placeholder is shown below.
        #
        #  __omit_place_holder__11bd71a2840bff144594b9cc2149db814256f253
        #
        if result['auth_provider'] is not None and '__omit_place_holder__' in result['auth_provider']:
            result['auth_provider'] = None

    def merge_provider_user_param(self, result, provider):
        if self.validate_params('user', provider):
            result['user'] = provider['user']
        elif self.validate_params('F5_USER', os.environ):
            result['user'] = os.environ.get('F5_USER')
        elif self.validate_params('ANSIBLE_NET_USERNAME', os.environ):
            result['user'] = os.environ.get('ANSIBLE_NET_USERNAME')
        else:
            result['user'] = None

    def merge_provider_password_param(self, result, provider):
        if self.validate_params('password', provider):
            result['password'] = provider['password']
        elif self.validate_params('F5_PASSWORD', os.environ):
            result['password'] = os.environ.get('F5_PASSWORD')
        elif self.validate_params('ANSIBLE_NET_PASSWORD', os.environ):
            result['password'] = os.environ.get('ANSIBLE_NET_PASSWORD')
        else:
            result['password'] = None


class AnsibleF5Parameters(object):
    def __init__(self, *args, **kwargs):
        self._values = defaultdict(lambda: None)
        self._values['__warnings'] = []
        self.client = kwargs.pop('client', None)
        self._module = kwargs.pop('module', None)
        self._params = {}

        params = kwargs.pop('params', None)
        if params:
            self.update(params=params)
            self._params.update(params)

    def update(self, params=None):
        if params:
            self._params.update(params)
            for k, v in iteritems(params):
                # Adding this here because ``username`` is a connection parameter
                # and in cases where it is also an API parameter, we run the risk
                # of overriding the specified parameter with the connection parameter.
                #
                # Since this is a problem, and since "username" is never a valid
                # parameter outside its usage in connection params (where we do not
                # use the ApiParameter or ModuleParameters classes) it is safe to
                # skip over it if it is provided.
                if k == 'password':
                    continue
                if self.api_map is not None and k in self.api_map:
                    map_key = self.api_map[k]
                else:
                    map_key = k

                # Handle weird API parameters like `dns.proxy.__iter__` by
                # using a map provided by the module developer
                class_attr = getattr(type(self), map_key, None)
                if isinstance(class_attr, property):
                    # There is a mapped value for the api_map key
                    if class_attr.fset is None:
                        # If the mapped value does not have
                        # an associated setter
                        self._values[map_key] = v
                    else:
                        # The mapped value has a setter
                        setattr(self, map_key, v)
                else:
                    # If the mapped value is not a @property
                    self._values[map_key] = v

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if self.api_map is not None and api_attribute in self.api_map:
                result[api_attribute] = getattr(self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result

    def __getattr__(self, item):
        # Ensures that properties that weren't defined, and therefore stashed
        # in the `_values` dict, will be retrievable.
        return self._values[item]

    @property
    def partition(self):
        if self._values['partition'] is None:
            return 'Common'
        return self._values['partition'].strip('/')

    @partition.setter
    def partition(self, value):
        self._values['partition'] = value

    def _filter_params(self, params):
        return dict((k, v) for k, v in iteritems(params) if v is not None)


class F5ModuleError(Exception):
    pass
