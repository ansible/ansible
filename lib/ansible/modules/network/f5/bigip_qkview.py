#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_qkview
short_description: Manage qkviews on the device
description:
  - Manages creating and downloading qkviews from a BIG-IP. Various
    options can be provided when creating qkviews. The qkview is important
    when dealing with F5 support. It may be required that you upload this
    qkview to the supported channels during resolution of an SRs that you
    may have opened.
version_added: 2.4
options:
  filename:
    description:
      - Name of the qkview to create on the remote BIG-IP.
    type: str
    default: "localhost.localdomain.qkview"
  dest:
    description:
      - Destination on your local filesystem when you want to save the qkview.
    type: path
    required: True
  asm_request_log:
    description:
      - When C(True), includes the ASM request log data. When C(False),
        excludes the ASM request log data.
    type: bool
    default: no
  max_file_size:
    description:
      - Max file size, in bytes, of the qkview to create. By default, no max
        file size is specified.
    type: int
    default: 0
  complete_information:
    description:
      - Include complete information in the qkview.
    type: bool
    default: no
  exclude_core:
    description:
      - Exclude core files from the qkview.
    type: bool
    default: no
  exclude:
    description:
      - Exclude various file from the qkview.
    type: list
    choices:
      - all
      - audit
      - secure
      - bash_history
  force:
    description:
      - If C(no), the file will only be transferred if the destination does not
        exist.
    type: bool
    default: yes
notes:
  - This module does not include the "max time" or "restrict to blade" options.
  - If you are using this module with either Ansible Tower or Ansible AWX, you
    should be aware of how these Ansible products execute jobs in restricted
    environments. More informat can be found here
    https://clouddocs.f5.com/products/orchestration/ansible/devel/usage/module-usage-with-tower.html
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Fetch a qkview from the remote device
  bigip_qkview:
    asm_request_log: yes
    exclude:
      - audit
      - secure
    dest: /tmp/localhost.localdomain.qkview
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
# only common fields returned
'''

import os
import re
import socket
import ssl
import time

from ansible.module_utils.basic import AnsibleModule
from distutils.version import LooseVersion

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.icontrol import download_file
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.icontrol import download_file


class Parameters(AnsibleF5Parameters):
    api_attributes = [
        'asm_request_log',
        'complete_information',
        'exclude',
        'exclude_core',
        'filename_cmd',
        'max_file_size',
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
        if self._values['max_file_size'] in [None]:
            return None
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
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.kwargs = kwargs

    def exec_module(self):
        if self.is_version_less_than_14():
            manager = self.get_manager('madm')
        else:
            manager = self.get_manager('bulk')
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'madm':
            return MadmLocationManager(**self.kwargs)
        elif type == 'bulk':
            return BulkLocationManager(**self.kwargs)

    def is_version_less_than_14(self):
        uri = "https://{0}:{1}/mgmt/tm/sys".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        version = urlparse.parse_qs(urlparse.urlparse(response['selfLink']).query)['ver'][0]
        if LooseVersion(version) < LooseVersion('14.0.0'):
            return True
        else:
            return False


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.have = None
        self.want = Parameters(params=self.module.params)
        self.changes = Parameters()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Parameters(params=changed)

    def exec_module(self):
        result = dict()

        self.present()

        result.update(**self.changes.to_return())
        result.update(dict(changed=False))
        return result

    def present(self):
        if os.path.exists(self.want.dest) and not self.want.force:
            raise F5ModuleError(
                "The specified 'dest' file already exists."
            )
        if not os.path.exists(os.path.dirname(self.want.dest)):
            raise F5ModuleError(
                "The directory of your 'dest' file does not exist."
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
        params = dict(
            command='run',
            utilCmdArgs=self.remote_dir
        )
        uri = "https://{0}:{1}/mgmt/tm/util/unix-ls".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False

        try:
            if self.want.filename in response['commandResult']:
                return True
        except KeyError:
            return False

    def execute(self):
        response = self.execute_on_device()
        if not response:
            raise F5ModuleError(
                "Failed to create qkview on device."
            )

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

    def _delete_qkview(self):
        tpath_name = '{0}/{1}'.format(self.remote_dir, self.want.filename)
        params = dict(
            command='run',
            utilCmdArgs=tpath_name
        )
        uri = "https://{0}:{1}/mgmt/tm/util/unix-rm".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False

    def execute_on_device(self):
        self._upsert_temporary_cli_script_on_device()
        task_id = self._create_async_task_on_device()
        self._exec_async_task_on_device(task_id)
        self._wait_for_async_task_to_finish_on_device(task_id)
        self._remove_temporary_cli_script_from_device()
        return True

    def _upsert_temporary_cli_script_on_device(self):
        args = {
            "name": "__ansible_mkqkview",
            "apiAnonymous": """
                proc script::run {} {
                    set cmd [lreplace $tmsh::argv 0 0]; eval "exec $cmd 2> /dev/null"
                }
            """
        }
        result = self._create_temporary_cli_script_on_device(args)
        if result:
            return True
        return self._update_temporary_cli_script_on_device(args)

    def _create_temporary_cli_script_on_device(self, args):
        uri = "https://{0}:{1}/mgmt/tm/cli/script".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=args)
        try:
            response = resp.json()
            if 'code' in response and response['code'] in [404, 409]:
                return False
        except ValueError:
            pass
        if resp.status in [404, 409]:
            return False
        return True

    def _update_temporary_cli_script_on_device(self, args):
        uri = "https://{0}:{1}/mgmt/tm/cli/script/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name('Common', '__ansible_mkqkview')
        )
        resp = self.client.api.put(uri, json=args)
        try:
            resp.json()
            return True
        except ValueError:
            raise F5ModuleError(
                "Failed to update temporary cli script on device."
            )

    def _create_async_task_on_device(self):
        """Creates an async cli script task in the REST API

        Returns:
            int: The ID of the task staged for running.

        :return:
        """
        command = ' '.join(self.want.api_params().values())
        args = {
            "command": "run",
            "name": "__ansible_mkqkview",
            "utilCmdArgs": "/usr/bin/qkview {0}".format(command)
        }
        uri = "https://{0}:{1}/mgmt/tm/task/cli/script".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=args)
        try:
            response = resp.json()
            return response['_taskId']
        except ValueError:
            raise F5ModuleError(
                "Failed to create the async task on the device."
            )

    def _exec_async_task_on_device(self, task_id):
        args = {"_taskState": "VALIDATING"}
        uri = "https://{0}:{1}/mgmt/tm/task/cli/script/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            task_id
        )
        resp = self.client.api.put(uri, json=args)
        try:
            resp.json()
            return True
        except ValueError:
            raise F5ModuleError(
                "Failed to execute the async task on the device"
            )

    def _wait_for_async_task_to_finish_on_device(self, task_id):
        uri = "https://{0}:{1}/mgmt/tm/task/cli/script/{2}/result".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            task_id
        )
        while True:
            try:
                resp = self.client.api.get(uri, timeout=10)
            except (socket.timeout, ssl.SSLError):
                continue
            try:
                response = resp.json()
            except ValueError:
                # It is possible that the API call can return invalid JSON.
                # This invalid JSON appears to be just empty strings.
                continue
            if response['_taskState'] == 'FAILED':
                raise F5ModuleError(
                    "qkview creation task failed unexpectedly."
                )
            if response['_taskState'] == 'COMPLETED':
                return True
            time.sleep(3)

    def _remove_temporary_cli_script_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/task/cli/script/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name('Common', '__ansible_mkqkview')
        )
        try:
            self.client.api.delete(uri)
            return True
        except ValueError:
            raise F5ModuleError(
                "Failed to remove the temporary cli script from the device."
            )

    def _move_qkview_to_download(self):
        uri = "https://{0}:{1}/mgmt/tm/util/unix-mv/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        args = dict(
            command='run',
            utilCmdArgs='/var/tmp/{0} {1}/{0}'.format(self.want.filename, self.remote_dir)
        )
        self.client.api.post(uri, json=args)
        return True


class BulkLocationManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super(BulkLocationManager, self).__init__(**kwargs)
        self.remote_dir = '/var/config/rest/bulk'

    def _download_file(self):
        uri = "https://{0}:{1}/mgmt/shared/file-transfer/bulk/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.filename
        )
        download_file(self.client, uri, self.want.dest)
        if os.path.exists(self.want.dest):
            return True
        return False


class MadmLocationManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super(MadmLocationManager, self).__init__(**kwargs)
        self.remote_dir = '/var/config/rest/madm'

    def _download_file(self):
        uri = "https://{0}:{1}/mgmt/shared/file-transfer/madm/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.filename
        )
        download_file(self.client, uri, self.want.dest)
        if os.path.exists(self.want.dest):
            return True
        return False


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            filename=dict(
                default='localhost.localdomain.qkview'
            ),
            asm_request_log=dict(
                type='bool',
                default='no',
            ),
            max_file_size=dict(
                type='int',
            ),
            complete_information=dict(
                default='no',
                type='bool'
            ),
            exclude_core=dict(
                default="no",
                type='bool'
            ),
            force=dict(
                default=True,
                type='bool'
            ),
            exclude=dict(
                type='list',
                choices=[
                    'all', 'audit', 'secure', 'bash_history'
                ]
            ),
            dest=dict(
                type='path',
                required=True
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
