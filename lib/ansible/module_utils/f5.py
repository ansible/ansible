# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Etienne Carrière <etienne.carriere@gmail.com>,2015
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

try:
    import bigsuds
    bigsuds_found = True
except ImportError:
    bigsuds_found = False


try:
    from f5.bigip import ManagementRoot as BigIpMgmt
    from f5.bigiq import ManagementRoot as BigIqMgmt
    from f5.iworkflow import ManagementRoot as iWorkflowMgmt
    from icontrol.session import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False


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
            required=False,
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
            module.fail_json(msg='bigsuds does not support verifying certificates with python < 2.7.9.  Either update python or set validate_certs=False on the task')

    return (module.params['server'],module.params['user'],module.params['password'],module.params['state'],module.params['partition'],module.params['validate_certs'],module.params['server_port'])


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
def fq_name(partition,name):
    if name is not None and not name.startswith('/'):
        return '/%s/%s' % (partition,name)
    return name


# Fully Qualified name (with partition) for a list
def fq_list_names(partition,list_names):
    if list_names is None:
        return None
    return map(lambda x: fq_name(partition,x),list_names)


class AnsibleF5Client(object):
    def __init__(self, argument_spec=None, supports_check_mode=False,
                 mutually_exclusive=None, required_together=None,
                 required_if=None, f5_product_name='bigip'):

        merged_arg_spec = dict()
        common_args = f5_argument_spec()
        merged_arg_spec.update(common_args)
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
            required_if=required_if
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


class F5ModuleError(Exception):
    pass
