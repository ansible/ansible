#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2017 F5 Networks Inc.
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

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.0'
}

DOCUMENTATION = '''
---
module: bigip_config
short_description: Manage BIG-IP configuration sections.
description:
  - Manages a BIG-IP configuration by allowing TMSH commands that
    modify running configuration, or merge SCF formatted files into
    the running configuration. Additionally, this module is of
    significant importance because it allows you to save your running
    configuration to disk. Since the F5 module only manipulate running
    configuration, it is important that you utilize this module to save
    that running config.
version_added: "2.4"
options:
  save:
    description:
      - The C(save) argument instructs the module to save the
        running-config to startup-config. This operation is performed
        after any changes are made to the current running config. If
        no changes are made, the configuration is still saved to the
        startup config. This option will always cause the module to
        return changed.
    choices:
      - yes
      - no
    default: no
  reset:
    description:
      - Loads the default configuration on the device. If this option
        is specified, the default configuration will be loaded before
        any commands or other provided configuration is run.
    choices:
      - yes
      - no
    default: no
  merge_content:
    description:
      - Loads the specified configuration that you want to merge into
        the running configuration. This is equivalent to using the
        C(tmsh) command C(load sys config from-terminal merge). If
        you need to read configuration from a file or template, use
        Ansible's C(file) or C(template) lookup plugins respectively.
  verify:
    description:
      - Validates the specified configuration to see whether they are
        valid to replace the running configuration. The running
        configuration will not be changed.
    choices:
      - yes
      - no
    default: yes
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
requirements:
  - f5-sdk >= 2.2.3
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Save the running configuration of the BIG-IP
  bigip_config:
    save: yes
    server: "lb.mydomain.com"
    password: "secret"
    user: "admin"
    validate_certs: "no"
  delegate_to: localhost

- name: Reset the BIG-IP configuration, for example, to RMA the device
  bigip_config:
    reset: yes
    save: yes
    server: "lb.mydomain.com"
    password: "secret"
    user: "admin"
    validate_certs: "no"
  delegate_to: localhost

- name: Load an SCF configuration
  bigip_config:
    merge_content: "{{ lookup('file', '/path/to/config.scf') }}"
    server: "lb.mydomain.com"
    password: "secret"
    user: "admin"
    validate_certs: "no"
  delegate_to: localhost
'''

RETURN = '''
stdout:
    description: The set of responses from the options
    returned: always
    type: list
    sample: ['...', '...']

stdout_lines:
    description: The value of stdout split into a list
    returned: always
    type: list
    sample: [['...', '...'], ['...'], ['...']]
'''

import os
import tempfile

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from ansible.module_utils.f5_utils import (
    AnsibleF5Client,
    AnsibleF5Parameters,
    HAS_F5SDK,
    F5ModuleError,
    iControlUnexpectedHTTPError,
    iteritems,
    defaultdict
)


class Parameters(AnsibleF5Parameters):
    returnables = ['stdout', 'stdout_lines']

    def __init__(self, params=None):
        self._values = defaultdict(lambda: None)
        if params:
            self.update(params)

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result

    def update(self, params=None):
        if params:
            for k, v in iteritems(params):
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
                        # If the mapped value does not have an associated setter
                        self._values[map_key] = v
                    else:
                        # The mapped value has a setter
                        setattr(self, map_key, v)
                else:
                    # If the mapped value is not a @property
                    self._values[map_key] = v


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.want = Parameters(self.client.module.params)
        self.changes = Parameters()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Parameters(changed)

    def _to_lines(self, stdout):
        lines = list()
        for item in stdout:
            if isinstance(item, str):
                item = str(item).split('\n')
            lines.append(item)
        return lines

    def exec_module(self):
        result = dict()

        try:
            self.execute()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        result.update(**self.changes.to_return())
        result.update(dict(changed=True))
        return result

    def execute(self):
        responses = []
        if self.want.reset:
            response = self.reset()
            responses.append(response)

        if self.want.merge_content:
            if self.want.verify:
                response = self.merge(verify=True)
                responses.append(response)
            else:
                response = self.merge(verify=False)
                responses.append(response)

        if self.want.save:
            response = self.save()
            responses.append(response)

        self.changes = Parameters({
            'stdout': responses,
            'stdout_lines': self._to_lines(responses)
        })

    def reset(self):
        if self.client.check_mode:
            return True
        return self.reset_device()

    def reset_device(self):
        command = 'tmsh load sys config default'
        output = self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "{0}"'.format(command)
        )
        if hasattr(output, 'commandResult'):
            return str(output.commandResult)
        return None

    def merge(self, verify=True):
        temp_name = next(tempfile._get_candidate_names())
        remote_path = "/var/config/rest/downloads/{0}".format(temp_name)
        temp_path = '/tmp/' + temp_name

        if self.client.check_mode:
            return True

        self.upload_to_device(temp_name)
        self.move_on_device(remote_path)
        response = self.merge_on_device(
            remote_path=temp_path, verify=verify
        )
        self.remove_temporary_file(remote_path=temp_path)
        return response

    def merge_on_device(self, remote_path, verify=True):
        result = None

        command = 'tmsh load sys config file {0} merge'.format(
            remote_path
        )
        if verify:
            command += ' verify'

        output = self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "{0}"'.format(command)
        )
        if hasattr(output, 'commandResult'):
            result = str(output.commandResult)
        return result

    def remove_temporary_file(self, remote_path):
        self.client.api.tm.util.unix_rm.exec_cmd(
            'run',
            utilCmdArgs=remote_path
        )

    def move_on_device(self, remote_path):
        self.client.api.tm.util.unix_mv.exec_cmd(
            'run',
            utilCmdArgs='{0} /tmp/{1}'.format(
                remote_path, os.path.basename(remote_path)
            )
        )

    def upload_to_device(self, temp_name):
        template = StringIO(self.want.merge_content)
        upload = self.client.api.shared.file_transfer.uploads
        upload.upload_stringio(template, temp_name)

    def save(self):
        if self.client.check_mode:
            return True
        return self.save_on_device()

    def save_on_device(self):
        result = None
        command = 'tmsh save sys config'
        output = self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "{0}"'.format(command)
        )
        if hasattr(output, 'commandResult'):
            result = str(output.commandResult)
        return result


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            reset=dict(
                type='bool',
                default=False
            ),
            merge_content=dict(),
            verify=dict(
                type='bool',
                default=True
            ),
            save=dict(
                type='bool',
                default=True
            )
        )
        self.f5_product_name = 'bigip'


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        client.module.exit_json(**results)
    except F5ModuleError as e:
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
