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
module: bigip_ucs_fetch
short_description: Fetches a UCS file from remote nodes
description:
   - This module is used for fetching UCS files from remote machines and
     storing them locally in a file tree, organized by hostname. Note that
     this module is written to transfer UCS files that might not be present,
     so a missing remote UCS won't be an error unless fail_on_missing is
     set to 'yes'.
version_added: 2.5
options:
  backup:
    description:
      - Create a backup file including the timestamp information so you can
        get the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: no
  create_on_missing:
    description:
      - Creates the UCS based on the value of C(src) if the file does not already
        exist on the remote system.
    type: bool
    default: yes
  dest:
    description:
      - A directory to save the UCS file into.
    type: path
    required: True
  encryption_password:
    description:
      - Password to use to encrypt the UCS file if desired.
    type: str
  fail_on_missing:
    description:
      - Make the module fail if the UCS file on the remote system is missing.
    type: bool
    default: no
  force:
    description:
      - If C(no), the file will only be transferred if the destination does not
        exist.
    type: bool
    default: yes
  src:
    description:
      - The name of the UCS file to create on the remote server for downloading
    type: str
notes:
  - BIG-IP provides no way to get a checksum of the UCS files on the system
    via any interface except, perhaps, logging in directly to the box (which
    would not support appliance mode). Therefore, the best this module can
    do is check for the existence of the file on disk; no check-summing.
  - If you are using this module with either Ansible Tower or Ansible AWX, you
    should be aware of how these Ansible products execute jobs in restricted
    environments. More information can be found here
    https://clouddocs.f5.com/products/orchestration/ansible/devel/usage/module-usage-with-tower.html
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Download a new UCS
  bigip_ucs_fetch:
    src: cs_backup.ucs
    dest: /tmp/cs_backup.ucs
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
checksum:
  description: The SHA1 checksum of the downloaded file
  returned: success or changed
  type: str
  sample: 7b46bbe4f8ebfee64761b5313855618f64c64109
dest:
  description: Location on the ansible host that the UCS was saved to
  returned: success
  type: str
  sample: /path/to/file.txt
src:
  description:
    - Name of the UCS file on the remote BIG-IP to download. If not
      specified, then this will be a randomly generated filename
  returned: changed
  type: str
  sample: cs_backup.ucs
backup_file:
  description: Name of backup file created
  returned: changed and if backup=yes
  type: str
  sample: /path/to/file.txt.2015-02-12@22:09~
gid:
  description: Group id of the UCS file, after execution
  returned: success
  type: int
  sample: 100
group:
  description: Group of the UCS file, after execution
  returned: success
  type: str
  sample: httpd
owner:
  description: Owner of the UCS file, after execution
  returned: success
  type: str
  sample: httpd
uid:
  description: Owner id of the UCS file, after execution
  returned: success
  type: int
  sample: 100
md5sum:
  description: The MD5 checksum of the downloaded file
  returned: changed or success
  type: str
  sample: 96cacab4c259c4598727d7cf2ceb3b45
mode:
  description: Permissions of the target UCS, after execution
  returned: success
  type: str
  sample: 0644
size:
  description: Size of the target UCS, after execution
  returned: success
  type: int
  sample: 1220
'''

import os
import re
import tempfile

from ansible.module_utils.basic import AnsibleModule
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.icontrol import download_file
    from library.module_utils.network.f5.icontrol import tmos_version
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.icontrol import download_file
    from ansible.module_utils.network.f5.icontrol import tmos_version


class Parameters(AnsibleF5Parameters):
    updatables = []
    returnables = [
        'dest',
        'src',
        'md5sum',
        'checksum',
        'backup_file']
    api_attributes = []
    api_map = {}

    @property
    def options(self):
        result = []
        if self.passphrase:
            result.append(dict(
                passphrase=self.want.passphrase
            ))
        return result

    @property
    def src(self):
        if self._values['src'] is not None:
            return self._values['src']
        result = next(tempfile._get_candidate_names()) + '.ucs'
        self._values['src'] = result
        return result

    @property
    def fulldest(self):
        result = None
        if os.path.isdir(self.dest):
            result = os.path.join(self.dest, self.src)
        else:
            if os.path.exists(os.path.dirname(self.dest)):
                result = self.dest
            else:
                try:
                    # os.path.exists() can return false in some
                    # circumstances where the directory does not have
                    # the execute bit for the current user set, in
                    # which case the stat() call will raise an OSError
                    os.stat(os.path.dirname(result))
                except OSError as e:
                    if "permission denied" in str(e).lower():
                        raise F5ModuleError(
                            "Destination directory {0} is not accessible".format(os.path.dirname(result))
                        )
                    raise F5ModuleError(
                        "Destination directory {0} does not exist".format(os.path.dirname(result))
                    )

        if not os.access(os.path.dirname(result), os.W_OK):
            raise F5ModuleError(
                "Destination {0} not writable".format(os.path.dirname(result))
            )
        return result


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):
    pass


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)

    def exec_module(self):
        if self.is_version_v1():
            manager = self.get_manager('v1')
        else:
            manager = self.get_manager('v2')
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'v1':
            return V1Manager(**self.kwargs)
        elif type == 'v2':
            return V2Manager(**self.kwargs)

    def is_version_v1(self):
        """Checks to see if the TMOS version is less than 12.1.0

        Versions prior to 12.1.0 have a bug which prevents the REST
        API from properly listing any UCS files when you query the
        /mgmt/tm/sys/ucs endpoint. Therefore you need to do everything
        through tmsh over REST.

        :return: bool
        """
        version = tmos_version(self.client)
        if LooseVersion(version) < LooseVersion('12.1.0'):
            return True
        else:
            return False


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = Parameters(params=self.module.params)
        self.changes = UsableChanges()

    def exec_module(self):
        result = dict()

        self.present()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=True))
        return result

    def present(self):
        if self.exists():
            self.update()
        else:
            self.create()

    def update(self):
        if os.path.exists(self.want.fulldest):
            if not self.want.force:
                raise F5ModuleError(
                    "File '{0}' already exists".format(self.want.fulldest)
                )
        self.execute()

    def _get_backup_file(self):
        return self.module.backup_local(self.want.fulldest)

    def execute(self):
        try:
            if self.want.backup:
                if os.path.exists(self.want.fulldest):
                    backup_file = self._get_backup_file()
                    self.changes.update({'backup_file': backup_file})
            self.download()
        except IOError:
            raise F5ModuleError(
                "Failed to copy: {0} to {1}".format(self.want.src, self.want.fulldest)
            )
        self._set_checksum()
        self._set_md5sum()
        file_args = self.module.load_file_common_arguments(self.module.params)
        return self.module.set_fs_attributes_if_different(file_args, True)

    def _set_checksum(self):
        try:
            result = self.module.sha1(self.want.fulldest)
            self.want.update({'checksum': result})
        except ValueError:
            pass

    def _set_md5sum(self):
        try:
            result = self.module.md5(self.want.fulldest)
            self.want.update({'md5sum': result})
        except ValueError:
            pass

    def create(self):
        if self.want.fail_on_missing:
            raise F5ModuleError(
                "UCS '{0}' was not found".format(self.want.src)
            )

        if not self.want.create_on_missing:
            raise F5ModuleError(
                "UCS '{0}' was not found".format(self.want.src)
            )

        if self.module.check_mode:
            return True
        if self.want.create_on_missing:
            self.create_on_device()
        self.execute()
        return True

    def create_on_device(self):
        if self.want.passphrase:
            params = dict(
                command='save',
                name=self.want.src,
                options=[{'passphrase': self.want.encryption_password}]
            )
        else:
            params = dict(
                command='save',
                name=self.want.src,
            )

        uri = "https://{0}:{1}/mgmt/tm/sys/ucs".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def download(self):
        self.download_from_device(self.want.dest)
        if os.path.exists(self.want.dest):
            return True
        raise F5ModuleError(
            "Failed to download the remote file"
        )


class V1Manager(BaseManager):
    def __init__(self, *args, **kwargs):
        super(V1Manager, self).__init__(**kwargs)
        self.remote_dir = '/var/config/rest/madm'

    def read_current(self):
        result = None
        output = self.read_current_from_device()
        if 'commandResult' in output:
            result = self._read_ucs_files_from_output(output['commandResult'])
        return result

    def read_current_from_device(self):
        params = dict(
            command='run',
            utilCmdArgs='-c "tmsh list sys ucs"'
        )

        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )

        resp = self.client.api.post(uri, json=params)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response

    def _read_ucs_files_from_output(self, output):
        search = re.compile(r'filename\s+(.*)').search
        lines = output.split("\n")
        result = [m.group(1) for m in map(search, lines) if m]
        return result

    def exists(self):
        collection = self.read_current()
        base = os.path.basename(self.want.src)
        if any(base == os.path.basename(x) for x in collection):
            return True
        return False

    def download_from_device(self, dest):
        url = 'https://{0}:{1}/mgmt/shared/file-transfer/madm/{2}'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.filename
        )
        try:
            download_file(self.client, url, dest)
        except F5ModuleError:
            raise F5ModuleError(
                "Failed to download the file."
            )
        if os.path.exists(self.want.dest):
            return True
        return False

    def _move_to_download(self):
        move_path = '/var/local/ucs/{0} {1}/{0}'.format(
            self.want.filename, self.remote_dir
        )
        params = dict(
            command='run',
            utilCmdArgs=move_path
        )

        uri = "https://{0}:{1}/mgmt/tm/util/unix-mv/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )

        resp = self.client.api.post(uri, json=params)

        try:
            response = resp.json()
            if 'commandResult' in response:
                if 'cannot stat' in response['commandResult']:
                    raise F5ModuleError(response['commandResult'])
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        return True


class V2Manager(BaseManager):
    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/ucs".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        return response

    def read_current(self):
        collection = self.read_current_from_device()
        if 'items' not in collection:
            return []
        resources = collection['items']
        result = [x['apiRawValues']['filename'] for x in resources]
        return result

    def exists(self):
        collection = self.read_current()
        base = os.path.basename(self.want.src)
        if any(base == os.path.basename(x) for x in collection):
            return True
        return False

    def download_from_device(self, dest):
        url = 'https://{0}:{1}/mgmt/shared/file-transfer/ucs-downloads/{2}'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.src
        )
        try:
            download_file(self.client, url, dest)
        except F5ModuleError:
            raise F5ModuleError(
                "Failed to download the file."
            )
        if os.path.exists(self.want.dest):
            return True
        return False


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            backup=dict(
                default='no',
                type='bool'
            ),
            create_on_missing=dict(
                default='yes',
                type='bool'
            ),
            encryption_password=dict(no_log=True),
            dest=dict(
                required=True,
                type='path'
            ),
            force=dict(
                default='yes',
                type='bool'
            ),
            fail_on_missing=dict(
                default='no',
                type='bool'
            ),
            src=dict()
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.add_file_common_args = True


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        add_file_common_args=spec.add_file_common_args
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
