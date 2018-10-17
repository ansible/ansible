#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

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
    default: no
    type: bool
  create_on_missing:
    description:
      - Creates the UCS based on the value of C(src) if the file does not already
        exist on the remote system.
    default: yes
    type: bool
  dest:
    description:
      - A directory to save the UCS file into.
    required: yes
  encryption_password:
    description:
      - Password to use to encrypt the UCS file if desired
  fail_on_missing:
    description:
      - Make the module fail if the UCS file on the remote system is missing.
    default: no
    type: bool
  force:
    description:
      - If C(no), the file will only be transferred if the destination does not
        exist.
    default: yes
    type: bool
  src:
    description:
      - The name of the UCS file to create on the remote server for downloading
notes:
  - BIG-IP provides no way to get a checksum of the UCS files on the system
    via any interface except, perhaps, logging in directly to the box (which
    would not support appliance mode). Therefore, the best this module can
    do is check for the existence of the file on disk; no check-summing.
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Download a new UCS
  bigip_ucs_fetch:
    server: lb.mydomain.com
    user: admin
    password: secret
    src: cs_backup.ucs
    dest: /tmp/cs_backup.ucs
  delegate_to: localhost
'''

RETURN = r'''
checksum:
  description: The SHA1 checksum of the downloaded file
  returned: success or changed
  type: string
  sample: 7b46bbe4f8ebfee64761b5313855618f64c64109
dest:
  description: Location on the ansible host that the UCS was saved to
  returned: success
  type: string
  sample: /path/to/file.txt
src:
  description:
    - Name of the UCS file on the remote BIG-IP to download. If not
      specified, then this will be a randomly generated filename
  returned: changed
  type: string
  sample: cs_backup.ucs
backup_file:
  description: Name of backup file created
  returned: changed and if backup=yes
  type: string
  sample: /path/to/file.txt.2015-02-12@22:09~
gid:
  description: Group id of the UCS file, after execution
  returned: success
  type: int
  sample: 100
group:
  description: Group of the UCS file, after execution
  returned: success
  type: string
  sample: httpd
owner:
  description: Owner of the UCS file, after execution
  returned: success
  type: string
  sample: httpd
uid:
  description: Owner id of the UCS file, after execution
  returned: success
  type: int
  sample: 100
md5sum:
  description: The MD5 checksum of the downloaded file
  returned: changed or success
  type: string
  sample: 96cacab4c259c4598727d7cf2ceb3b45
mode:
  description: Permissions of the target UCS, after execution
  returned: success
  type: string
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
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    updatables = []
    returnables = ['dest', 'src', 'md5sum', 'checksum', 'backup_file']
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
        self.client = kwargs.get('client', None)
        self.kwargs = kwargs

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
        version = self.client.api.tmos_version
        if LooseVersion(version) < LooseVersion('12.1.0'):
            return True
        else:
            return False


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.want = Parameters(params=self.module.params)
        self.changes = UsableChanges()

    def exec_module(self):
        result = dict()

        try:
            self.present()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

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
            self.client.api.tm.sys.ucs.exec_cmd(
                'save',
                name=self.want.src,
                options=[{'passphrase': self.want.encryption_password}]
            )
        else:
            self.client.api.tm.sys.ucs.exec_cmd(
                'save',
                name=self.want.src
            )

    def download(self):
        self.download_from_device()
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
        if hasattr(output, 'commandResult'):
            result = self._read_ucs_files_from_output(output.commandResult)
        return result

    def read_current_from_device(self):
        output = self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "tmsh list sys ucs"'
        )
        return output

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

    def download_from_device(self):
        madm = self.client.api.shared.file_transfer.madm
        madm.download_file(self.want.filename, self.want.dest)
        if os.path.exists(self.want.dest):
            return True
        return False

    def _move_to_download(self):
        try:
            move_path = '/var/local/ucs/{0} {1}/{0}'.format(
                self.want.filename, self.remote_dir
            )
            self.client.api.tm.util.unix_mv.exec_cmd(
                'run',
                utilCmdArgs=move_path
            )
            return True
        except Exception:
            return False


class V2Manager(BaseManager):
    def read_current(self):
        collection = self.read_current_from_device()
        if 'items' not in collection.attrs:
            return []
        resources = collection.attrs['items']
        result = [x['apiRawValues']['filename'] for x in resources]
        return result

    def read_current_from_device(self):
        collection = self.client.api.tm.sys.ucs.load()
        return collection

    def exists(self):
        collection = self.read_current()
        base = os.path.basename(self.want.src)
        if any(base == os.path.basename(x) for x in collection):
            return True
        return False

    def download_from_device(self):
        ucs = self.client.api.shared.file_transfer.ucs_downloads
        ucs.download_file(self.want.src, self.want.dest)
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
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        module.exit_json(**results)
    except F5ModuleError as ex:
        cleanup_tokens(client)
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
