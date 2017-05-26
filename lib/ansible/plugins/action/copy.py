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

import json
import os
import stat
import tempfile

from ansible.constants import mk_boolean as boolean
from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.action import ActionBase
from ansible.utils.hashing import checksum


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        ''' handler for file transfer operations '''
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        source  = self._task.args.get('src', None)
        content = self._task.args.get('content', None)
        dest    = self._task.args.get('dest', None)
        raw     = boolean(self._task.args.get('raw', 'no'))
        force   = boolean(self._task.args.get('force', 'yes'))
        remote_src = boolean(self._task.args.get('remote_src', False))
        follow  = boolean(self._task.args.get('follow', False))

        result['failed'] = True
        if (source is None and content is None) or dest is None:
            result['msg'] = "src (or content) and dest are required"
        elif source is not None and content is not None:
            result['msg'] = "src and content are mutually exclusive"
        elif content is not None and dest is not None and dest.endswith("/"):
            result['msg'] = "dest must be a file if content is defined"
        else:
            del result['failed']

        if result.get('failed'):
            return result

        # Check if the source ends with a "/"
        source_trailing_slash = False
        if source:
            source_trailing_slash = self._connection._shell.path_has_trailing_slash(source)

        # Define content_tempfile in case we set it after finding content populated.
        content_tempfile = None

        # If content is defined make a temp file and write the content into it.
        if content is not None:
            try:
                # If content comes to us as a dict it should be decoded json.
                # We need to encode it back into a string to write it out.
                if isinstance(content, dict) or isinstance(content, list):
                    content_tempfile = self._create_content_tempfile(json.dumps(content))
                else:
                    content_tempfile = self._create_content_tempfile(content)
                source = content_tempfile
            except Exception as err:
                result['failed'] = True
                result['msg'] = "could not write content temp file: %s" % to_native(err)
                return result

        # if we have first_available_file in our vars
        # look up the files and use the first one we find as src
        elif remote_src:
            result.update(self._execute_module(task_vars=task_vars))
            return result
        else:  # find in expected paths
            try:
                source = self._find_needle('files', source)
            except AnsibleError as e:
                result['failed'] = True
                result['msg'] = to_text(e)
                return result

        # A list of source file tuples (full_path, relative_path) which will try to copy to the destination
        source_files = []

        # If source is a directory populate our list else source is a file and translate it to a tuple.
        if os.path.isdir(to_bytes(source, errors='surrogate_or_strict')):
            # Get the amount of spaces to remove to get the relative path.
            if source_trailing_slash:
                sz = len(source)
            else:
                sz = len(source.rsplit('/', 1)[0]) + 1

            # Walk the directory and append the file tuples to source_files.
            for base_path, sub_folders, files in os.walk(to_bytes(source)):
                for file in files:
                    full_path = to_text(os.path.join(base_path, file), errors='surrogate_or_strict')
                    rel_path = full_path[sz:]
                    if rel_path.startswith('/'):
                        rel_path = rel_path[1:]
                    source_files.append((full_path, rel_path))

                # recurse into subdirs
                for sf in sub_folders:
                    source_files += self._get_recursive_files(os.path.join(source, to_text(sf)), sz=sz)

            # If it's recursive copy, destination is always a dir,
            # explicitly mark it so (note - copy module relies on this).
            if not self._connection._shell.path_has_trailing_slash(dest):
                dest = self._connection._shell.join_path(dest, '')
        else:
            source_files.append((source, os.path.basename(source)))

        changed = False
        module_return = dict(changed=False)

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
        dest = self._remote_expand_user(dest)

        # Keep original value for mode parameter
        mode_value = self._task.args.get('mode', None)

        diffs = []
        for source_full, source_rel in source_files:

            # If the local file does not exist, get_real_file() raises AnsibleFileNotFound
            try:
                source_full = self._loader.get_real_file(source_full)
            except AnsibleFileNotFound as e:
                result['failed'] = True
                result['msg'] = "could not find src=%s, %s" % (source_full, e)
                self._remove_tmp_path(tmp)
                return result

            # Get the local mode and set if user wanted it preserved
            # https://github.com/ansible/ansible-modules-core/issues/1124
            if self._task.args.get('mode', None) == 'preserve':
                lmode = '0%03o' % stat.S_IMODE(os.stat(source_full).st_mode)
                self._task.args['mode'] = lmode

            # This is kind of optimization - if user told us destination is
            # dir, do path manipulation right away, otherwise we still check
            # for dest being a dir via remote call below.
            if self._connection._shell.path_has_trailing_slash(dest):
                dest_file = self._connection._shell.join_path(dest, source_rel)
            else:
                dest_file = self._connection._shell.join_path(dest)

            # Attempt to get remote file info
            dest_status = self._execute_remote_stat(dest_file, all_vars=task_vars, follow=follow, tmp=tmp, checksum=force)

            if dest_status['exists'] and dest_status['isdir']:
                # The dest is a directory.
                if content is not None:
                    # If source was defined as content remove the temporary file and fail out.
                    self._remove_tempfile_if_content_defined(content, content_tempfile)
                    self._remove_tmp_path(tmp)
                    result['failed'] = True
                    result['msg'] = "can not use content with a dir as dest"
                    return result
                else:
                    # Append the relative source location to the destination and get remote stats again
                    dest_file = self._connection._shell.join_path(dest, source_rel)
                    dest_status = self._execute_remote_stat(dest_file, all_vars=task_vars, follow=follow, tmp=tmp, checksum=force)

            if dest_status['exists'] and not force:
                # remote_file exists so continue to next iteration.
                continue

            # Generate a hash of the local file.
            local_checksum = checksum(source_full)

            if local_checksum != dest_status['checksum']:
                # The checksums don't match and we will change or error out.
                changed = True

                # Create a tmp path if missing only if this is not recursive.
                # If this is recursive we already have a tmp path.
                if delete_remote_tmp:
                    if tmp is None or "-tmp-" not in tmp:
                        tmp = self._make_tmp_path()

                if self._play_context.diff and not raw:
                    diffs.append(self._get_diff_data(dest_file, source_full, task_vars))

                if self._play_context.check_mode:
                    self._remove_tempfile_if_content_defined(content, content_tempfile)
                    changed = True
                    module_return = dict(changed=True)
                    continue

                # Define a remote directory that we will copy the file to.
                tmp_src = self._connection._shell.join_path(tmp, 'source')

                remote_path = None

                if not raw:
                    remote_path = self._transfer_file(source_full, tmp_src)
                else:
                    self._transfer_file(source_full, dest_file)

                # We have copied the file remotely and no longer require our content_tempfile
                self._remove_tempfile_if_content_defined(content, content_tempfile)
                self._loader.cleanup_tmp_file(source_full)

                # fix file permissions when the copy is done as a different user
                if remote_path:
                    self._fixup_perms2((tmp, remote_path))

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
                if 'content' in new_module_args:
                    del new_module_args['content']

                module_return = self._execute_module(module_name='copy',
                        module_args=new_module_args, task_vars=task_vars,
                        tmp=tmp, delete_remote_tmp=delete_remote_tmp)
                module_executed = True

            else:
                # no need to transfer the file, already correct hash, but still need to call
                # the file module in case we want to change attributes
                self._remove_tempfile_if_content_defined(content, content_tempfile)
                self._loader.cleanup_tmp_file(source_full)

                if raw:
                    # Continue to next iteration if raw is defined.
                    self._remove_tmp_path(tmp)
                    continue

                # Fix for https://github.com/ansible/ansible-modules-core/issues/1568.
                # If checksums match, and follow = True, find out if 'dest' is a link. If so,
                # change it to point to the source of the link.
                if follow:
                    dest_status_nofollow = self._execute_remote_stat(dest_file, all_vars=task_vars, follow=False)
                    if dest_status_nofollow['islnk'] and 'lnk_source' in dest_status_nofollow.keys():
                        dest = dest_status_nofollow['lnk_source']

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
                module_return = self._execute_module(module_name='file',
                        module_args=new_module_args, task_vars=task_vars,
                        tmp=tmp, delete_remote_tmp=delete_remote_tmp)
                module_executed = True

            if not module_return.get('checksum'):
                module_return['checksum'] = local_checksum
            if module_return.get('failed'):
                result.update(module_return)
                if not delete_remote_tmp:
                    self._remove_tmp_path(tmp)
                return result
            if module_return.get('changed'):
                changed = True

            # the file module returns the file path as 'path', but
            # the copy module uses 'dest', so add it if it's not there
            if 'path' in module_return and 'dest' not in module_return:
                module_return['dest'] = module_return['path']

            # reset the mode
            self._task.args['mode'] = mode_value

        # Delete tmp path if we were recursive or if we did not execute a module.
        if not delete_remote_tmp or (delete_remote_tmp and not module_executed):
            self._remove_tmp_path(tmp)

        if module_executed and len(source_files) == 1:
            result.update(module_return)
        else:
            result.update(dict(dest=dest, src=source, changed=changed))

        if diffs:
            result['diff'] = diffs

        return result

    def _get_recursive_files(self, topdir, sz=0):
        ''' Recursively create file tuples for sub folders '''
        r_files = []
        for base_path, sub_folders, files in os.walk(to_bytes(topdir)):
            for fname in files:
                full_path = to_text(os.path.join(base_path, fname), errors='surrogate_or_strict')
                rel_path = full_path[sz:]
                if rel_path.startswith('/'):
                    rel_path = rel_path[1:]
                r_files.append((full_path, rel_path))

                for sf in sub_folders:
                    r_files += self._get_recursive_files(os.path.join(topdir, to_text(sf)), sz=sz)

        return r_files

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

    def _remove_tempfile_if_content_defined(self, content, content_tempfile):
        if content is not None:
            os.remove(content_tempfile)
