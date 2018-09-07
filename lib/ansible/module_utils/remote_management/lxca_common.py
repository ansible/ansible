# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by
# Ansible still belong to the author of the module, and may assign their
# own license to the complete work.
#
# Copyright (C) 2017 Lenovo, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Contains LXCA common class
# Lenovo xClarity Administrator (LXCA)

import abc
import traceback
try:
    from pylxca import connect
    HAS_PYLXCA = True
except Exception:
    HAS_PYLXCA = False

from ansible.module_utils import six
from ansible.module_utils.basic import AnsibleModule

LXCA_COMMON_ARGS = dict(
    login_user=dict(default=None, required=True),
    login_password=dict(default=None, required=True, no_log=True),
    auth_url=dict(default=None, required=True),
    noverify=dict(default=True)
)


def setup_module_object(input_arg_spec):
    """
    this function merge argument spec and create ansible module object
    :return:
    """
    args_spec = dict(LXCA_COMMON_ARGS)
    args_spec.update(input_arg_spec)
    module = AnsibleModule(argument_spec=args_spec, supports_check_mode=False)

    return module


def setup_conn(module):
    """
    this function create connection to LXCA
    :param module:
    :return:  lxca connection
    """
    lxca_con = None
    try:
        lxca_con = connect(module.params['auth_url'],
                           module.params['login_user'],
                           module.params['login_password'],
                           module.params['noverify'], )
    except Exception as exception:
        error_msg = '; '.join((e) for e in exception.args)
        module.fail_json(msg=error_msg, exception=traceback.format_exc())
    return lxca_con


@six.add_metaclass(abc.ABCMeta)
class LXCAModuleBase(object):
    PYLXCA_REQUIRED = 'Lenovo xClarity Administrator Python Client (pylxca) is required for this module.'

    LXCA_COMMON_ARGS = dict(
        login_user=dict(default=None, required=True),
        login_password=dict(default=None, required=True, no_log=True),
        auth_url=dict(default=None, required=True),
        noverify=dict(default=True)
    )


    lxca_con = None

    def __init__(self, input_args_spec=None):
        """
        PylxcaModuleBase constructor.

        :arg dict additional_arg_spec: Additional argument spec definition.
        """
        args_spec = dict(self.LXCA_COMMON_ARGS)
        args_spec.update(input_args_spec)

        self.module = AnsibleModule(argument_spec=args_spec, supports_check_mode=False)

        self._has_pylxca()
        self._connect_lxca()

    def _has_pylxca(self):
        if not HAS_PYLXCA:
            self.module.fail_json(msg=self.PYLXCA_REQUIRED)

    def _connect_lxca(self):
        try:
            self.lxca_con = connect(self.module.params['auth_url'],
                                    self.module.params['login_user'],
                                    self.module.params['login_password'],
                                    self.module.params['noverify'],)
        except Exception as exception:
            error_msg = '; '.join((e) for e in exception.args)
            self.module.fail_json(msg=error_msg, exception=traceback.format_exc())

    @abc.abstractmethod
    def execute_module(self):
        """
        Abstract method, this must be implemented by LXCA modules

        :return: dict: of (changed, msg, result).
        """
        pass

    def run(self):
        """
        Common implementation of the Pyxlca run modules.

        It calls the inheritor 'execute_module' function and sends the return to the Ansible.


        """
        try:
            result = self.execute_module()

            if "changed" not in result:
                result['changed'] = False

            self.module.exit_json(**result)

        except Exception as exception:
            error_msg = '; '.join(e for e in exception.args)
            self.module.fail_json(msg=error_msg, exception=traceback.format_exc())
