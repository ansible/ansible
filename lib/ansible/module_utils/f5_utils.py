#
# Copyright 2016 F5 Networks Inc.
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


# Legacy

try:
    import bigsuds
    bigsuds_found = True
except ImportError:
    bigsuds_found = False


from ansible.module_utils.basic import env_fallback


def f5_argument_spec():
    return dict(
        server=dict(
            type='str',
            required=True,
            fallback=(env_fallback, ['F5_SERVER'])
        ),
        user=dict(
            type='str',
            required=True,
            fallback=(env_fallback, ['F5_USER'])
        ),
        password=dict(
            type='str',
            aliases=['pass', 'pwd'],
            required=True,
            no_log=True,
            fallback=(env_fallback, ['F5_PASSWORD'])
        ),
        validate_certs=dict(
            default='yes',
            type='bool',
            fallback=(env_fallback, ['F5_VALIDATE_CERTS'])
        ),
        server_port=dict(
            type='int',
            default=443,
            fallback=(env_fallback, ['F5_SERVER_PORT'])
        ),
        state=dict(
            type='str',
            default='present',
            choices=['present', 'absent']
        ),
        partition=dict(
            type='str',
            default='Common',
            fallback=(env_fallback, ['F5_PARTITION'])
        )
    )


def f5_parse_arguments(module):
    if not bigsuds_found:
        module.fail_json(msg="the python bigsuds module is required")

    if module.params['validate_certs']:
        import ssl
        if not hasattr(ssl, 'SSLContext'):
            module.fail_json(
                msg="bigsuds does not support verifying certificates with python < 2.7.9."
                    "Either update python or set validate_certs=False on the task'")

    return (
        module.params['server'],
        module.params['user'],
        module.params['password'],
        module.params['state'],
        module.params['partition'],
        module.params['validate_certs'],
        module.params['server_port']
    )


def bigip_api(bigip, user, password, validate_certs, port=443):
    try:
        if bigsuds.__version__ >= '1.0.4':
            api = bigsuds.BIGIP(hostname=bigip, username=user, password=password, verify=validate_certs, port=port)
        elif bigsuds.__version__ == '1.0.3':
            api = bigsuds.BIGIP(hostname=bigip, username=user, password=password, verify=validate_certs)
        else:
            api = bigsuds.BIGIP(hostname=bigip, username=user, password=password)
    except TypeError:
        # bigsuds < 1.0.3, no verify param
        if validate_certs:
            # Note: verified we have SSLContext when we parsed params
            api = bigsuds.BIGIP(hostname=bigip, username=user, password=password)
        else:
            import ssl
            if hasattr(ssl, 'SSLContext'):
                # Really, you should never do this.  It disables certificate
                # verification *globally*.  But since older bigip libraries
                # don't give us a way to toggle verification we need to
                # disable it at the global level.
                # From https://www.python.org/dev/peps/pep-0476/#id29
                ssl._create_default_https_context = ssl._create_unverified_context
            api = bigsuds.BIGIP(hostname=bigip, username=user, password=password)

    return api


# Fully Qualified name (with the partition)
def fq_name(partition, name):
    if name is not None and not name.startswith('/'):
        return '/%s/%s' % (partition, name)
    return name


# Fully Qualified name (with partition) for a list
def fq_list_names(partition, list_names):
    if list_names is None:
        return None
    return map(lambda x: fq_name(partition, x), list_names)


# New style

from abc import ABCMeta, abstractproperty
from collections import defaultdict

try:
    from f5.bigip import ManagementRoot as BigIpMgmt
    from f5.bigip.contexts import TransactionContextManager as BigIpTxContext

    from f5.bigiq import ManagementRoot as BigIqMgmt

    from f5.iworkflow import ManagementRoot as iWorkflowMgmt
    from icontrol.exceptions import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems, with_metaclass


F5_COMMON_ARGS = dict(
    server=dict(
        type='str',
        required=True,
        fallback=(env_fallback, ['F5_SERVER'])
    ),
    user=dict(
        type='str',
        required=True,
        fallback=(env_fallback, ['F5_USER'])
    ),
    password=dict(
        type='str',
        aliases=['pass', 'pwd'],
        required=True,
        no_log=True,
        fallback=(env_fallback, ['F5_PASSWORD'])
    ),
    validate_certs=dict(
        default='yes',
        type='bool',
        fallback=(env_fallback, ['F5_VALIDATE_CERTS'])
    ),
    server_port=dict(
        type='int',
        default=443,
        fallback=(env_fallback, ['F5_SERVER_PORT'])
    ),
    state=dict(
        type='str',
        default='present',
        choices=['present', 'absent']
    ),
    partition=dict(
        type='str',
        default='Common',
        fallback=(env_fallback, ['F5_PARTITION'])
    )
)


class AnsibleF5Client(object):
    def __init__(self, argument_spec=None, supports_check_mode=False,
                 mutually_exclusive=None, required_together=None,
                 required_if=None, required_one_of=None, add_file_common_args=False,
                 f5_product_name='bigip'):

        self.f5_product_name = f5_product_name

        merged_arg_spec = dict()
        merged_arg_spec.update(F5_COMMON_ARGS)
        if argument_spec:
            merged_arg_spec.update(argument_spec)
            self.arg_spec = merged_arg_spec

        mutually_exclusive_params = []
        if mutually_exclusive:
            mutually_exclusive_params += mutually_exclusive

        required_together_params = []
        if required_together:
            required_together_params += required_together

        self.module = AnsibleModule(
            argument_spec=merged_arg_spec,
            supports_check_mode=supports_check_mode,
            mutually_exclusive=mutually_exclusive_params,
            required_together=required_together_params,
            required_if=required_if,
            required_one_of=required_one_of,
            add_file_common_args=add_file_common_args
        )

        self.check_mode = self.module.check_mode
        self._connect_params = self._get_connect_params()

        try:
            self.api = self._get_mgmt_root(
                f5_product_name, **self._connect_params
            )
        except iControlUnexpectedHTTPError as exc:
            self.fail(str(exc))

    def fail(self, msg):
        self.module.fail_json(msg=msg)

    def _get_connect_params(self):
        params = dict(
            user=self.module.params['user'],
            password=self.module.params['password'],
            server=self.module.params['server'],
            server_port=self.module.params['server_port'],
            validate_certs=self.module.params['validate_certs']
        )
        return params

    def _get_mgmt_root(self, type, **kwargs):
        if type == 'bigip':
            return BigIpMgmt(
                kwargs['server'],
                kwargs['user'],
                kwargs['password'],
                port=kwargs['server_port'],
                token='tmos'
            )
        elif type == 'iworkflow':
            return iWorkflowMgmt(
                kwargs['server'],
                kwargs['user'],
                kwargs['password'],
                port=kwargs['server_port'],
                token='local'
            )
        elif type == 'bigiq':
            return BigIqMgmt(
                kwargs['server'],
                kwargs['user'],
                kwargs['password'],
                port=kwargs['server_port'],
                token='local'
            )

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
        self.api = self._get_mgmt_root(
            self.f5_product_name, **self._connect_params
        )


class AnsibleF5Parameters(object):
    def __init__(self, params=None):
        self._values = defaultdict(lambda: None)
        if params:
            for k, v in iteritems(params):
                if self.api_map is not None and k in self.api_map:
                    dict_to_use = self.api_map
                    map_key = self.api_map[k]
                else:
                    dict_to_use = self._values
                    map_key = k

                # Handle weird API parameters like `dns.proxy.__iter__` by
                # using a map provided by the module developer
                class_attr = getattr(type(self), map_key, None)
                if isinstance(class_attr, property):
                    # There is a mapped value for the api_map key
                    if class_attr.fset is None:
                        # If the mapped value does not have an associated setter
                        self._values[map_key] = v
                    else:
                        # The mapped value has a setter
                        setattr(self, map_key, v)
                else:
                    # If the mapped value is not a @property
                    self._values[map_key] = v

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
