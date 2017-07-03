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
module: bigip_qkview
short_description: Manage qkviews on the device.
description:
  - Manages creating and downloading qkviews from a BIG-IP. Various
    options can be provided when creating qkviews. The qkview is important
    when dealing with F5 support. It may be required that you upload this
    qkview to the supported channels during resolution of an SRs that you
    may have opened.
version_added: "2.4"
options:
  filename:
    description:
      - Name of the qkview to create on the remote BIG-IP.
    default: "localhost.localdomain.qkview"
  dest:
    description:
      - Destination on your local filesystem when you want to save the qkview.
    required: True
  asm_request_log:
    description:
      - When C(True), includes the ASM request log data. When C(False),
        excludes the ASM request log data.
    default: no
    choices:
      - yes
      - no
  max_file_size:
    description:
      - Max file size, in bytes, of the qkview to create. By default, no max
        file size is specified.
    default: 0
  complete_information:
    description:
      - Include complete information in the qkview.
    default: yes
    choices:
      - yes
      - no
  exclude_core:
    description:
      - Exclude core files from the qkview.
    default: no
    choices:
      - yes
      - no
  exclude:
    description:
      - Exclude various file from the qkview.
    choices:
      - all
      - audit
      - secure
      - bash_history
  force:
    description:
      - If C(no), the file will only be transferred if the destination does not
        exist.
    default: yes
    choices:
      - yes
      - no
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
  - This module does not include the "max time" or "restrict to blade" options.
requirements:
  - f5-sdk >= 2.2.3
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Fetch a qkview from the remote device
  bigip_qkview:
      asm_request_log: "yes"
      exclude:
          - audit
          - secure
      dest: "/tmp/localhost.localdomain.qkview"
  delegate_to: localhost
'''

RETURN = '''
stdout:
    description: The set of responses from the commands
    returned: always
    type: list
    sample: ['...', '...']
stdout_lines:
    description: The value of stdout split into a list
    returned: always
    type: list
    sample: [['...', '...'], ['...'], ['...']]
'''

import re
import os

from distutils.version import LooseVersion

from ansible.module_utils.six import string_types
from ansible.module_utils.f5_utils import (
    AnsibleF5Client,
    AnsibleF5Parameters,
    HAS_F5SDK,
    F5ModuleError,
    iControlUnexpectedHTTPError
)


class Parameters(AnsibleF5Parameters):
    api_attributes = [
        'exclude', 'exclude_core', 'complete_information', 'max_file_size',
        'asm_request_log', 'filename_cmd'
    ]

    returnables = ['stdout', 'stdout_lines', 'warnings']

    @property
    def exclude(self):
        if self._values['exclude'] is None:
            return None
        exclude = ' '.join(self._values['exclude'])
        return "--exclude='{0}'".format(exclude)

    @property
    def exclude_raw(self):
        return self._values['exclude']

    @property
    def exclude_core(self):
        if self._values['exclude']:
            return '-C'
        else:
            return None

    @property
    def complete_information(self):
        if self._values['complete_information']:
            return '-c'
        return None

    @property
    def max_file_size(self):
        if self._values['max_file_size'] in [None, 0]:
            return '-s0'
        return '-s {0}'.format(self._values['max_file_size'])

    @property
    def asm_request_log(self):
        if self._values['asm_request_log']:
            return '-o asm-request-log'
        return None

    @property
    def filename(self):
        pattern = r'^[\w\.]+$'
        filename = os.path.basename(self._values['filename'])
        if re.match(pattern, filename):
            return filename
        else:
            raise F5ModuleError(
                "The provided filename must contain word characters only."
            )

    @property
    def filename_cmd(self):
        return '-f {0}'.format(self.filename)

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if self.api_map is not None and api_attribute in self.api_map:
                result[api_attribute] = getattr(self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result


class ModuleManager(object):
    def __init__(self, client):
        self.client = client

    def exec_module(self):
        if self.is_version_less_than_14():
            manager = self.get_manager('madm')
        else:
            manager = self.get_manager('bulk')
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'madm':
            return MadmLocationManager(self.client)
        elif type == 'bulk':
            return BulkLocationManager(self.client)

    def is_version_less_than_14(self):
        """Checks to see if the TMOS version is less than 14

        Anything less than BIG-IP 13.x does not support users
        on different partitions.

        :return: Bool
        """
        version = self.client.api.tmos_version
        if LooseVersion(version) < LooseVersion('14.0.0'):
            return True
        else:
            return False


class BaseManager(object):
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
        lines = []
        if isinstance(stdout, string_types):
            lines = str(stdout).split('\n')
        return lines

    def exec_module(self):
        result = dict()

        try:
            self.present()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        result.update(**self.changes.to_return())
        result.update(dict(changed=False))
        return result

    def present(self):
        if os.path.exists(self.want.dest) and not self.want.force:
            raise F5ModuleError(
                "The specified 'dest' file already exists"
            )
        if self.want.exclude:
            choices = ['all', 'audit', 'secure', 'bash_history']
            if not all(x in choices for x in self.want.exclude_raw):
                raise F5ModuleError(
                    "The specified excludes must be in the following list: "
                    "{0}".format(','.join(choices))
                )
        self.execute()

    def exists(self):
        ls = self.client.api.tm.util.unix_ls.exec_cmd(
            'run', utilCmdArgs=self.remote_dir
        )

        # Empty directories return nothing to the commandResult
        if not hasattr(ls, 'commandResult'):
            return False

        if self.want.filename in ls.commandResult:
            return True
        else:
            return False

    def execute(self):
        response = self.execute_on_device()
        result = self._move_qkview_to_download()
        if not result:
            raise F5ModuleError(
                "Failed to move the file to a downloadable location"
            )

        self._download_file()
        if not os.path.exists(self.want.dest):
            raise F5ModuleError(
                "Failed to save the qkview to local disk"
            )

        self._delete_qkview()
        result = self.exists()
        if result:
            raise F5ModuleError(
                "Failed to remove the remote qkview"
            )

        self.changes = Parameters({
            'stdout': response,
            'stdout_lines': self._to_lines(response)
        })

    def _delete_qkview(self):
        tpath_name = '{0}/{1}'.format(self.remote_dir, self.want.filename)
        self.client.api.tm.util.unix_rm.exec_cmd(
            'run', utilCmdArgs=tpath_name
        )

    def execute_on_device(self):
        params = self.want.api_params().values()
        output = self.client.api.tm.util.qkview.exec_cmd(
            'run',
            utilCmdArgs='{0}'.format(' '.join(params))
        )
        if hasattr(output, 'commandResult'):
            return str(output.commandResult)
        return None


class BulkLocationManager(BaseManager):
    def __init__(self, client):
        super(BulkLocationManager, self).__init__(client)
        self.remote_dir = '/var/config/rest/bulk'

    def _move_qkview_to_download(self):
        try:
            move_path = '/var/tmp/{0} {1}/{0}'.format(
                self.want.filename, self.remote_dir
            )
            self.client.api.tm.util.unix_mv.exec_cmd(
                'run',
                utilCmdArgs=move_path
            )
            return True
        except Exception:
            return False

    def _download_file(self):
        bulk = self.client.api.shared.file_transfer.bulk
        bulk.download_file(self.want.filename, self.want.dest)
        if os.path.exists(self.want.dest):
            return True
        return False


class MadmLocationManager(BaseManager):
    def __init__(self, client):
        super(MadmLocationManager, self).__init__(client)
        self.remote_dir = '/var/config/rest/madm'

    def _move_qkview_to_download(self):
        try:
            move_path = '/var/tmp/{0} {1}/{0}'.format(
                self.want.filename, self.remote_dir
            )
            self.client.api.tm.util.unix_mv.exec_cmd(
                'run',
                utilCmdArgs=move_path
            )
            return True
        except Exception:
            return False

    def _download_file(self):
        madm = self.client.api.shared.file_transfer.madm
        madm.download_file(self.want.filename, self.want.dest)
        if os.path.exists(self.want.dest):
            return True
        return False


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            filename=dict(
                default='localhost.localdomain.qkview'
            ),
            asm_request_log=dict(
                type='bool',
                default=False,
            ),
            max_file_size=dict(
                type='int',
            ),
            complete_information=dict(
                default=False,
                type='bool'
            ),
            exclude_core=dict(
                default=False,
                type='bool'
            ),
            force=dict(
                default=True,
                type='bool'
            ),
            exclude=dict(
                type='list'
            ),
            dest=dict(
                type='path',
                required=True
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
