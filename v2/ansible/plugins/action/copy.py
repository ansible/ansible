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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import json
import os
import pipes
import stat
import tempfile

from ansible import constants as C
from ansible.plugins.action import ActionBase
from ansible.utils.boolean import boolean
from ansible.utils.hashing import checksum
from ansible.utils.unicode import to_bytes
from ansible.parsing.vault import VaultLib

class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=dict()):
        ''' handler for file transfer operations '''

        source  = self._task.args.get('src', None)
        content = self._task.args.get('content', None)
        dest    = self._task.args.get('dest', None)
        raw     = boolean(self._task.args.get('raw', 'no'))
        force   = boolean(self._task.args.get('force', 'yes'))

        # FIXME: first available file needs to be reworked somehow...
        #if (source is None and content is None and not 'first_available_file' in inject) or dest is None:
        #    result=dict(failed=True, msg="src (or content) and dest are required")
        #    return ReturnData(conn=conn, result=result)
        #elif (source is not None or 'first_available_file' in inject) and content is not None:
        #    result=dict(failed=True, msg="src and content are mutually exclusive")
        #    return ReturnData(conn=conn, result=result)

        # Check if the source ends with a "/"
        source_trailing_slash = False
        if source:
            source_trailing_slash = source.endswith(os.sep)

        # Define content_tempfile in case we set it after finding content populated.
        content_tempfile = None

        # If content is defined make a temp file and write the content into it.
        if content is not None:
            try:
                # If content comes to us as a dict it should be decoded json.
                # We need to encode it back into a string to write it out.
                if isinstance(content, dict):
                    content_tempfile = self._create_content_tempfile(json.dumps(content))
                else:
                    content_tempfile = self._create_content_tempfile(content)
                source = content_tempfile
            except Exception as err:
                return dict(failed=True, msg="could not write content temp file: %s" % err)

        ###############################################################################################
        # FIXME: first_available_file needs to be reworked?
        ###############################################################################################
        # if we have first_available_file in our vars
        # look up the files and use the first one we find as src
        #elif 'first_available_file' in inject:
        #    found = False
        #    for fn in inject.get('first_available_file'):
        #        fn_orig = fn
        #        fnt = template.template(self.runner.basedir, fn, inject)
        #        fnd = utils.path_dwim(self.runner.basedir, fnt)
        #        if not os.path.exists(fnd) and '_original_file' in inject:
        #            fnd = utils.path_dwim_relative(inject['_original_file'], 'files', fnt, self.runner.basedir, check=False)
        #        if os.path.exists(fnd):
        #            source = fnd
        #            found = True
        #            break
        #    if not found:
        #        results = dict(failed=True, msg="could not find src in first_available_file list")
        #        return ReturnData(conn=conn, result=results)
        ###############################################################################################
        else:
            if self._task._role is not None:
                source = self._loader.path_dwim_relative(self._task._role._role_path, 'files', source)
            else:
                source = self._loader.path_dwim(source)

        # A list of source file tuples (full_path, relative_path) which will try to copy to the destination
        source_files = []

        # If source is a directory populate our list else source is a file and translate it to a tuple.
        if os.path.isdir(source):
            # Get the amount of spaces to remove to get the relative path.
            if source_trailing_slash:
                sz = len(source)
            else:
                sz = len(source.rsplit('/', 1)[0]) + 1

            # Walk the directory and append the file tuples to source_files.
            for base_path, sub_folders, files in os.walk(source):
                for file in files:
                    full_path = os.path.join(base_path, file)
                    rel_path = full_path[sz:]
                    source_files.append((full_path, rel_path))

            # If it's recursive copy, destination is always a dir,
            # explicitly mark it so (note - copy module relies on this).
            if not self._shell.path_has_trailing_slash(dest):
                dest = self._shell.join_path(dest, '')
        else:
            source_files.append((source, os.path.basename(source)))

        changed = False
        diffs = []
        module_result = {"changed": False}

        # A register for if we executed a module.
        # Used to cut down on command calls when not recursive.
        module_executed = False

        # Tell _execute_module to delete the file if there is one file.
        delete_remote_tmp = (len(source_files) == 1)

        # If this is a recursive action create a tmp path that we can share as the _exec_module create is too late.
        if not delete_remote_tmp:
            if tmp is None or "-tmp-" not in tmp:
                tmp = self._make_tmp_path()

        # expand any user home dir specifier
        dest = self._remote_expand_user(dest, tmp)

        for source_full, source_rel in source_files:

            # Generate a hash of the local file.
            local_checksum = checksum(source_full)

            # If local_checksum is not defined we can't find the file so we should fail out.
            if local_checksum is None:
                return dict(failed=True, msg="could not find src=%s" % source_full)

            # This is kind of optimization - if user told us destination is
            # dir, do path manipulation right away, otherwise we still check
            # for dest being a dir via remote call below.
            if self._shell.path_has_trailing_slash(dest):
                dest_file = self._shell.join_path(dest, source_rel)
            else:
                dest_file = self._shell.join_path(dest)

            # Attempt to get the remote checksum
            remote_checksum = self._remote_checksum(tmp, dest_file)

            if remote_checksum == '3':
                # The remote_checksum was executed on a directory.
                if content is not None:
                    # If source was defined as content remove the temporary file and fail out.
                    self._remove_tempfile_if_content_defined(content, content_tempfile)
                    return dict(failed=True, msg="can not use content with a dir as dest")
                else:
                    # Append the relative source location to the destination and retry remote_checksum
                    dest_file = self._shell.join_path(dest, source_rel)
                    remote_checksum = self._remote_checksum(tmp, dest_file)

            if remote_checksum != '1' and not force:
                # remote_file does not exist so continue to next iteration.
                continue

            if local_checksum != remote_checksum:
                # The checksums don't match and we will change or error out.
                changed = True

                # Create a tmp path if missing only if this is not recursive.
                # If this is recursive we already have a tmp path.
                if delete_remote_tmp:
                    if tmp is None or "-tmp-" not in tmp:
                        tmp = self._make_tmp_path()

                # FIXME: runner shouldn't have the diff option there
                #if self.runner.diff and not raw:
                #    diff = self._get_diff_data(tmp, dest_file, source_full)
                #else:
                #    diff = {}
                diff = {}

                # FIXME: noop stuff
                #if self.runner.noop_on_check(inject):
                #    self._remove_tempfile_if_content_defined(content, content_tempfile)
                #    diffs.append(diff)
                #    changed = True
                #    module_result = dict(changed=True)
                #    continue

                # Define a remote directory that we will copy the file to.
                tmp_src = tmp + 'source'

                if not raw:
                    self._connection.put_file(source_full, tmp_src)
                else:
                    self._connection.put_file(source_full, dest_file)

                # We have copied the file remotely and no longer require our content_tempfile
                self._remove_tempfile_if_content_defined(content, content_tempfile)

                # fix file permissions when the copy is done as a different user
                if self._connection_info.become and self._connection_info.become_user != 'root':
                    self._remote_chmod('a+r', tmp_src, tmp)

                if raw:
                    # Continue to next iteration if raw is defined.
                    continue

                # Run the copy module

                # src and dest here come after original and override them
                # we pass dest only to make sure it includes trailing slash in case of recursive copy
                new_module_args = self._task.args.copy()
                new_module_args.update(
                    dict(
                        src=tmp_src,
                        dest=dest,
                        original_basename=source_rel,
                    )
                )

                module_return = self._execute_module(module_name='copy', module_args=new_module_args, delete_remote_tmp=delete_remote_tmp)
                module_executed = True

            else:
                # no need to transfer the file, already correct hash, but still need to call
                # the file module in case we want to change attributes
                self._remove_tempfile_if_content_defined(content, content_tempfile)

                if raw:
                    # Continue to next iteration if raw is defined.
                    # self._remove_tmp_path(tmp)
                    continue

                # Build temporary module_args.
                new_module_args = self._task.args.copy()
                new_module_args.update(
                    dict(
                        src=source_rel,
                        dest=dest,
                        original_basename=source_rel
                    )
                )

                # Execute the file module.
                module_return = self._execute_module(module_name='file', module_args=new_module_args, delete_remote_tmp=delete_remote_tmp)
                module_executed = True

            if not module_return.get('checksum'):
                module_return['checksum'] = local_checksum
            if module_return.get('failed') == True:
                return module_return
            if module_return.get('changed') == True:
                changed = True

            # the file module returns the file path as 'path', but
            # the copy module uses 'dest', so add it if it's not there
            if 'path' in module_return and 'dest' not in module_return:
                module_return['dest'] = module_return['path']

        # Delete tmp path if we were recursive or if we did not execute a module.
        if (not C.DEFAULT_KEEP_REMOTE_FILES and not delete_remote_tmp) or (not C.DEFAULT_KEEP_REMOTE_FILES and delete_remote_tmp and not module_executed):
            self._remove_tmp_path(tmp)

        # TODO: Support detailed status/diff for multiple files
        if module_executed and len(source_files) == 1:
            result = module_return
        else:
            result = dict(dest=dest, src=source, changed=changed)

        if len(diffs) == 1:
            result['diff']=diffs[0]

        return result

    def _create_content_tempfile(self, content):
        ''' Create a tempfile containing defined content '''
        fd, content_tempfile = tempfile.mkstemp()
        f = os.fdopen(fd, 'wb')
        content = to_bytes(content)
        try:
            f.write(content)
        except Exception as err:
            os.remove(content_tempfile)
            raise Exception(err)
        finally:
            f.close()
        return content_tempfile

    def _get_diff_data(self, tmp, destination, source):
        peek_result = self._execute_module(module_name='file', module_args=dict(path=destination, diff_peek=True), persist_files=True)
        if 'failed' in peek_result and peek_result['failed'] or peek_result.get('rc', 0) != 0:
            return {}

        diff = {}
        if peek_result['state'] == 'absent':
            diff['before'] = ''
        elif peek_result['appears_binary']:
            diff['dst_binary'] = 1
        # FIXME: this should not be in utils..
        #elif peek_result['size'] > utils.MAX_FILE_SIZE_FOR_DIFF:
        #    diff['dst_larger'] = utils.MAX_FILE_SIZE_FOR_DIFF
        else:
            dest_result = self._execute_module(module_name='slurp', module_args=dict(path=destination), tmp=tmp, persist_files=True)
            if 'content' in dest_result:
                dest_contents = dest_result['content']
                if dest_result['encoding'] == 'base64':
                    dest_contents = base64.b64decode(dest_contents)
                else:
                    raise Exception("unknown encoding, failed: %s" % dest_result)
                diff['before_header'] = destination
                diff['before'] = dest_contents

        src = open(source)
        src_contents = src.read(8192)
        st = os.stat(source)
        if "\x00" in src_contents:
            diff['src_binary'] = 1
        # FIXME: this should not be in utils
        #elif st[stat.ST_SIZE] > utils.MAX_FILE_SIZE_FOR_DIFF:
        #    diff['src_larger'] = utils.MAX_FILE_SIZE_FOR_DIFF
        else:
            src.seek(0)
            diff['after_header'] = source
            diff['after'] = src.read()

        return diff

    def _remove_tempfile_if_content_defined(self, content, content_tempfile):
        if content is not None:
            os.remove(content_tempfile)

