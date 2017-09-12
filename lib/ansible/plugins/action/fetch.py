# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import base64

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes
from ansible.module_utils.six import string_types
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase
from ansible.utils.hashing import checksum, checksum_s, md5, secure_hash
from ansible.utils.path import makedirs_safe

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        ''' handler for fetch operations '''
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        if self._play_context.check_mode:
            result['skipped'] = True
            result['msg'] = 'check mode not (yet) supported for this module'
            return result

        source = self._task.args.get('src', None)
        dest = self._task.args.get('dest', None)
        flat = boolean(self._task.args.get('flat'), strict=False)
        fail_on_missing = boolean(self._task.args.get('fail_on_missing'), strict=False)
        validate_checksum = boolean(self._task.args.get('validate_checksum',
                                                        self._task.args.get('validate_md5', True)),
                                    strict=False)

        # validate source and dest are strings FIXME: use basic.py and module specs
        if not isinstance(source, string_types):
            result['msg'] = "Invalid type supplied for source option, it must be a string"

        if not isinstance(dest, string_types):
            result['msg'] = "Invalid type supplied for dest option, it must be a string"

        # validate_md5 is the deprecated way to specify validate_checksum
        if 'validate_md5' in self._task.args and 'validate_checksum' in self._task.args:
            result['msg'] = "validate_checksum and validate_md5 cannot both be specified"

        if 'validate_md5' in self._task.args:
            display.deprecated('Use validate_checksum instead of validate_md5', version='2.8')

        if source is None or dest is None:
            result['msg'] = "src and dest are required"

        if result.get('msg'):
            result['failed'] = True
            return result

        source = self._connection._shell.join_path(source)
        source = self._remote_expand_user(source)

        remote_checksum = None
        if not self._play_context.become:
            # calculate checksum for the remote file, don't bother if using become as slurp will be used
            # Force remote_checksum to follow symlinks because fetch always follows symlinks
            remote_checksum = self._remote_checksum(source, all_vars=task_vars, follow=True)

        # use slurp if permissions are lacking or privilege escalation is needed
        remote_data = None
        if remote_checksum in ('1', '2', None):
            slurpres = self._execute_module(module_name='slurp', module_args=dict(src=source), task_vars=task_vars, tmp=tmp)
            if slurpres.get('failed'):
                if not fail_on_missing and (slurpres.get('msg').startswith('file not found') or remote_checksum == '1'):
                    result['msg'] = "the remote file does not exist, not transferring, ignored"
                    result['file'] = source
                    result['changed'] = False
                else:
                    result.update(slurpres)
                return result
            else:
                if slurpres['encoding'] == 'base64':
                    remote_data = base64.b64decode(slurpres['content'])
                if remote_data is not None:
                    remote_checksum = checksum_s(remote_data)
                # the source path may have been expanded on the
                # target system, so we compare it here and use the
                # expanded version if it's different
                remote_source = slurpres.get('source')
                if remote_source and remote_source != source:
                    source = remote_source

        # calculate the destination name
        if os.path.sep not in self._connection._shell.join_path('a', ''):
            source = self._connection._shell._unquote(source)
            source_local = source.replace('\\', '/')
        else:
            source_local = source

        dest = os.path.expanduser(dest)
        if flat:
            if os.path.isdir(to_bytes(dest, errors='surrogate_or_strict')) and not dest.endswith(os.sep):
                result['msg'] = "dest is an existing directory, use a trailing slash if you want to fetch src into that directory"
                result['file'] = dest
                result['failed'] = True
                return result
            if dest.endswith(os.sep):
                # if the path ends with "/", we'll use the source filename as the
                # destination filename
                base = os.path.basename(source_local)
                dest = os.path.join(dest, base)
            if not dest.startswith("/"):
                # if dest does not start with "/", we'll assume a relative path
                dest = self._loader.path_dwim(dest)
        else:
            # files are saved in dest dir, with a subdir for each host, then the filename
            if 'inventory_hostname' in task_vars:
                target_name = task_vars['inventory_hostname']
            else:
                target_name = self._play_context.remote_addr
            dest = "%s/%s/%s" % (self._loader.path_dwim(dest), target_name, source_local)

        dest = dest.replace("//", "/")

        if remote_checksum in ('0', '1', '2', '3', '4', '5'):
            result['changed'] = False
            result['file'] = source
            if remote_checksum == '0':
                result['msg'] = "unable to calculate the checksum of the remote file"
            elif remote_checksum == '1':
                result['msg'] = "the remote file does not exist"
            elif remote_checksum == '2':
                result['msg'] = "no read permission on remote file"
            elif remote_checksum == '3':
                result['msg'] = "remote file is a directory, fetch cannot work on directories"
            elif remote_checksum == '4':
                result['msg'] = "python isn't present on the system.  Unable to compute checksum"
            elif remote_checksum == '5':
                result['msg'] = "stdlib json or simplejson was not found on the remote machine. Only the raw module can work without those installed"
            # Historically, these don't fail because you may want to transfer
            # a log file that possibly MAY exist but keep going to fetch other
            # log files. Today, this is better achieved by adding
            # ignore_errors or failed_when to the task.  Control the behaviour
            # via fail_when_missing
            if fail_on_missing:
                result['failed'] = True
                del result['changed']
            else:
                result['msg'] += ", not transferring, ignored"
            return result

        # calculate checksum for the local file
        local_checksum = checksum(dest)

        if remote_checksum != local_checksum:
            # create the containing directories, if needed
            makedirs_safe(os.path.dirname(dest))

            # fetch the file and check for changes
            if remote_data is None:
                self._connection.fetch_file(source, dest)
            else:
                try:
                    f = open(to_bytes(dest, errors='surrogate_or_strict'), 'wb')
                    f.write(remote_data)
                    f.close()
                except (IOError, OSError) as e:
                    raise AnsibleError("Failed to fetch the file: %s" % e)
            new_checksum = secure_hash(dest)
            # For backwards compatibility. We'll return None on FIPS enabled systems
            try:
                new_md5 = md5(dest)
            except ValueError:
                new_md5 = None

            if validate_checksum and new_checksum != remote_checksum:
                result.update(dict(failed=True, md5sum=new_md5,
                                   msg="checksum mismatch", file=source, dest=dest, remote_md5sum=None,
                                   checksum=new_checksum, remote_checksum=remote_checksum))
            else:
                result.update({'changed': True, 'md5sum': new_md5, 'dest': dest,
                               'remote_md5sum': None, 'checksum': new_checksum,
                               'remote_checksum': remote_checksum})
        else:
            # For backwards compatibility. We'll return None on FIPS enabled systems
            try:
                local_md5 = md5(dest)
            except ValueError:
                local_md5 = None
            result.update(dict(changed=False, md5sum=local_md5, file=source, dest=dest, checksum=local_checksum))

        return result
