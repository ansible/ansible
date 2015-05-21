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
import pwd
import random
import traceback
import tempfile
import base64

from ansible import constants as C
from ansible.errors import *
from ansible.plugins.action import ActionBase
from ansible.utils.boolean import boolean
from ansible.utils.hashing import checksum, checksum_s, md5, secure_hash

class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=dict()):
        ''' handler for fetch operations '''

        # FIXME: is this even required anymore?
        #if self.runner.noop_on_check(inject):
        #    return ReturnData(conn=conn, comm_ok=True, result=dict(skipped=True, msg='check mode not (yet) supported for this module'))

        source            = self._task.args.get('src', None)
        dest              = self._task.args.get('dest', None)
        flat              = boolean(self._task.args.get('flat'))
        fail_on_missing   = boolean(self._task.args.get('fail_on_missing'))
        validate_checksum = boolean(self._task.args.get('validate_checksum', self._task.args.get('validate_md5')))

        if 'validate_md5' in self._task.args and 'validate_checksum' in self._task.args:
            return dict(failed=True, msg="validate_checksum and validate_md5 cannot both be specified")

        if source is None or dest is None:
            return dict(failed=True, msg="src and dest are required")

        source = self._shell.join_path(source)
        source = self._remote_expand_user(source, tmp)

        # calculate checksum for the remote file
        remote_checksum = self._remote_checksum(tmp, source)

        # use slurp if sudo and permissions are lacking
        remote_data = None
        if remote_checksum in ('1', '2') or self._connection_info.become:
            slurpres = self._execute_module(module_name='slurp', module_args=dict(src=source), tmp=tmp)
            if slurpres.get('rc') == 0:
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
            else:
                # FIXME: should raise an error here? the old code did nothing
                pass

        # calculate the destination name
        if os.path.sep not in self._shell.join_path('a', ''):
            source_local = source.replace('\\', '/')
        else:
            source_local = source

        dest = os.path.expanduser(dest)
        if flat:
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
                target_name = self._connection_info.remote_addr
            dest = "%s/%s/%s" % (self._loader.path_dwim(dest), target_name, source_local)

        dest = dest.replace("//","/")

        if remote_checksum in ('0', '1', '2', '3', '4'):
            # these don't fail because you may want to transfer a log file that possibly MAY exist
            # but keep going to fetch other log files
            if remote_checksum == '0':
                result = dict(msg="unable to calculate the checksum of the remote file", file=source, changed=False)
            elif remote_checksum == '1':
                if fail_on_missing:
                    result = dict(failed=True, msg="the remote file does not exist", file=source)
                else:
                    result = dict(msg="the remote file does not exist, not transferring, ignored", file=source, changed=False)
            elif remote_checksum == '2':
                result = dict(msg="no read permission on remote file, not transferring, ignored", file=source, changed=False)
            elif remote_checksum == '3':
                result = dict(msg="remote file is a directory, fetch cannot work on directories", file=source, changed=False)
            elif remote_checksum == '4':
                result = dict(msg="python isn't present on the system.  Unable to compute checksum", file=source, changed=False)
            return result

        # calculate checksum for the local file
        local_checksum = checksum(dest)

        if remote_checksum != local_checksum:
            # create the containing directories, if needed
            if not os.path.isdir(os.path.dirname(dest)):
                os.makedirs(os.path.dirname(dest))

            # fetch the file and check for changes
            if remote_data is None:
                self._connection.fetch_file(source, dest)
            else:
                f = open(dest, 'w')
                f.write(remote_data)
                f.close()
            new_checksum = secure_hash(dest)
            # For backwards compatibility.  We'll return None on FIPS enabled
            # systems
            try:
                new_md5 = md5(dest)
            except ValueError:
                new_md5 = None

            if validate_checksum and new_checksum != remote_checksum:
                return dict(failed=True, md5sum=new_md5, msg="checksum mismatch", file=source, dest=dest, remote_md5sum=None, checksum=new_checksum, remote_checksum=remote_checksum)
            return dict(changed=True, md5sum=new_md5, dest=dest, remote_md5sum=None, checksum=new_checksum, remote_checksum=remote_checksum)
        else:
            # For backwards compatibility.  We'll return None on FIPS enabled
            # systems
            try:
                local_md5 = md5(dest)
            except ValueError:
                local_md5 = None

            return dict(changed=False, md5sum=local_md5, file=source, dest=dest, checksum=local_checksum)

