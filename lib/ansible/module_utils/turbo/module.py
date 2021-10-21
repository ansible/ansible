# Copyright (c) 2021 Red Hat
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
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
#
import json
import os
import os.path
import sys
import tempfile

import ansible.module_utils.basic
from .exceptions import (
    EmbeddedModuleSuccess,
    EmbeddedModuleFailure,
)
import ansible.module_utils.turbo.common

if False:  # pylint: disable=using-constant-test
    from .server import please_include_me

    # This is a trick to be sure server.py is embedded in the Ansiblez
    # zip archive.🥷
    please_include_me


def get_collection_name_from_path():
    module_path = ansible.module_utils.basic.get_module_path()

    ansiblez = module_path.split("/")[-3]
    if ansiblez.startswith("ansible_") and ansiblez.endswith(".zip"):
        return ".".join(ansiblez[8:].split(".")[:2])


def expand_argument_specs_aliases(argument_spec):
    """Returns a dict of accepted argument that includes the aliases"""
    expanded_argument_specs = {}
    for k, v in argument_spec.items():
        for alias in [k] + v.get("aliases", []):
            expanded_argument_specs[alias] = v
    return expanded_argument_specs


def prepare_args(argument_specs, params):
    """Take argument_spec and the user params and prepare the final argument structure."""

    def _keep_value(v, argument_specs, key, subkey=None):
        if v is None:  # cannot be a valide parameter
            return False
        if key not in argument_specs:  # should never happen
            return
        if not subkey:  # level 1 parameter
            return v != argument_specs[key].get("default")
        elif subkey not in argument_specs[key]:  # Freeform
            return True
        elif isinstance(argument_specs[key][subkey], dict):
            return v != argument_specs[key][subkey].get("default")
        else:  # should never happen
            return True

    def _is_an_alias(k):
        aliases = argument_specs[k].get("aliases")
        return aliases and k in aliases

    new_params = {}
    for k, v in params.items():
        if not _keep_value(v, argument_specs, k):
            continue

        if _is_an_alias(k):
            continue

        if isinstance(v, dict):
            new_params[k] = {
                i: j for i, j in v.items() if _keep_value(j, argument_specs, k, i)
            }
        else:
            new_params[k] = v
    args = {"ANSIBLE_MODULE_ARGS": new_params}
    return args


class AnsibleTurboModule(ansible.module_utils.basic.AnsibleModule):
    embedded_in_server = False
    collection_name = None

    def __init__(self, *args, **kwargs):
        self.embedded_in_server = sys.argv[0].endswith("/server.py")
        self.collection_name = (
            AnsibleTurboModule.collection_name or get_collection_name_from_path()
        )
        ansible.module_utils.basic.AnsibleModule.__init__(
            self, *args, bypass_checks=not self.embedded_in_server, **kwargs
        )
        self._running = None
        if not self.embedded_in_server:
            self.run_on_daemon()

    def socket_path(self):
        if self._remote_tmp is None:
            abs_remote_tmp = tempfile.gettempdir()
        else:
            abs_remote_tmp = os.path.expanduser(os.path.expandvars(self._remote_tmp))
        return os.path.join(abs_remote_tmp, f"turbo_mode.{self.collection_name}.socket")

    def init_args(self):
        argument_specs = expand_argument_specs_aliases(self.argument_spec)
        args = prepare_args(argument_specs, self.params)
        for k in ansible.module_utils.basic.PASS_VARS:
            attribute = ansible.module_utils.basic.PASS_VARS[k][0]
            if not hasattr(self, attribute):
                continue
            v = getattr(self, attribute)
            if isinstance(v, int) or isinstance(v, bool) or isinstance(v, str):
                args["ANSIBLE_MODULE_ARGS"][f"_ansible_{k}"] = v
        return args

    def run_on_daemon(self):
        result = dict(changed=False, original_message="", message="")
        ttl = os.environ.get("ANSIBLE_TURBO_LOOKUP_TTL", None)
        with ansible.module_utils.turbo.common.connect(
            socket_path=self.socket_path(), ttl=ttl
        ) as turbo_socket:
            ansiblez_path = sys.path[0]
            args = self.init_args()
            data = [
                ansiblez_path,
                json.dumps(args),
                dict(os.environ),
            ]
            content = json.dumps(data).encode()
            result = turbo_socket.communicate(content)
        self.exit_json(**result)

    def exit_json(self, **kwargs):
        if not self.embedded_in_server:
            super().exit_json(**kwargs)
        else:
            self.do_cleanup_files()
            raise EmbeddedModuleSuccess(**kwargs)

    def fail_json(self, *args, **kwargs):
        if not self.embedded_in_server:
            super().fail_json(**kwargs)
        else:
            self.do_cleanup_files()
            raise EmbeddedModuleFailure(*args, **kwargs)
