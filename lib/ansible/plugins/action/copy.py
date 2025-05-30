# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Toshio Kuratomi <tkuraotmi@ansible.com>
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

from __future__ import annotations

import json
import os
import os.path
import stat
import tempfile

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleActionFail, AnsibleFileNotFound
from ansible.module_utils.basic import FILE_COMMON_ARGUMENTS
from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase
from ansible.utils.hashing import checksum


# Supplement the FILE_COMMON_ARGUMENTS with arguments that are specific to file
REAL_FILE_ARGS = frozenset(FILE_COMMON_ARGUMENTS.keys()).union(
                          ('state', 'path', '_original_basename', 'recurse', 'force',
                           '_diff_peek', 'src'))


def _create_remote_file_args(module_args):
    """remove keys that are not relevant to file"""
    return dict((k, v) for k, v in module_args.items() if k in REAL_FILE_ARGS)


def _create_remote_copy_args(module_args):
    """remove action plugin only keys"""
    return dict((k, v) for k, v in module_args.items() if k not in ('content', 'decrypt'))


def _walk_dirs(topdir, base_path=None, local_follow=False, trailing_slash_detector=None):
    """
    Walk a filesystem tree returning enough information to copy the files

    :arg topdir: The directory that the filesystem tree is rooted at
    :kwarg base_path: The initial directory structure to strip off of the
        files for the destination directory.  If this is None (the default),
        the base_path is set to ``top_dir``.
    :kwarg local_follow: Whether to follow symlinks on the source.  When set
        to False, no symlinks are dereferenced.  When set to True (the
        default), the code will dereference most symlinks.  However, symlinks
        can still be present if needed to break a circular link.
    :kwarg trailing_slash_detector: Function to determine if a path has
        a trailing directory separator. Only needed when dealing with paths on
        a remote machine (in which case, pass in a function that is aware of the
        directory separator conventions on the remote machine).
    :returns: dictionary of tuples.  All of the path elements in the structure are text strings.
            This separates all the files, directories, and symlinks along with
            important information about each::

                { 'files': [('/absolute/path/to/copy/from', 'relative/path/to/copy/to'), ...],
                  'directories': [('/absolute/path/to/copy/from', 'relative/path/to/copy/to'), ...],
                  'symlinks': [('/symlink/target/path', 'relative/path/to/copy/to'), ...],
                }

        The ``symlinks`` field is only populated if ``local_follow`` is set to False
        *or* a circular symlink cannot be dereferenced.

    """
    # Convert the path segments into byte strings

    r_files = {'files': [], 'directories': [], 'symlinks': []}

    def _recurse(topdir, rel_offset, parent_dirs, rel_base=u''):
        """
        This is a closure (function utilizing variables from it's parent
        function's scope) so that we only need one copy of all the containers.
        Note that this function uses side effects (See the Variables used from
        outer scope).

        :arg topdir: The directory we are walking for files
        :arg rel_offset: Integer defining how many characters to strip off of
            the beginning of a path
        :arg parent_dirs: Directories that we're copying that this directory is in.
        :kwarg rel_base: String to prepend to the path after ``rel_offset`` is
            applied to form the relative path.

        Variables used from the outer scope
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        :r_files: Dictionary of files in the hierarchy.  See the return value
            for :func:`walk` for the structure of this dictionary.
        :local_follow: Read-only inside of :func:`_recurse`. Whether to follow symlinks
        """
        for base_path, sub_folders, files in os.walk(topdir):
            for filename in files:
                filepath = os.path.join(base_path, filename)
                dest_filepath = os.path.join(rel_base, filepath[rel_offset:])

                if os.path.islink(filepath):
                    # Dereference the symlnk
                    real_file = os.path.realpath(filepath)
                    if local_follow and os.path.isfile(real_file):
                        # Add the file pointed to by the symlink
                        r_files['files'].append((real_file, dest_filepath))
                    else:
                        # Mark this file as a symlink to copy
                        r_files['symlinks'].append((os.readlink(filepath), dest_filepath))
                else:
                    # Just a normal file
                    r_files['files'].append((filepath, dest_filepath))

            for dirname in sub_folders:
                dirpath = os.path.join(base_path, dirname)
                dest_dirpath = os.path.join(rel_base, dirpath[rel_offset:])
                real_dir = os.path.realpath(dirpath)
                dir_stats = os.stat(real_dir)

                if os.path.islink(dirpath):
                    if local_follow:
                        if (dir_stats.st_dev, dir_stats.st_ino) in parent_dirs:
                            # Just insert the symlink if the target directory
                            # exists inside of the copy already
                            r_files['symlinks'].append((os.readlink(dirpath), dest_dirpath))
                        else:
                            # Walk the dirpath to find all parent directories.
                            new_parents = set()
                            parent_dir_list = os.path.dirname(dirpath).split(os.path.sep)
                            for parent in range(len(parent_dir_list), 0, -1):
                                parent_stat = os.stat(u'/'.join(parent_dir_list[:parent]))
                                if (parent_stat.st_dev, parent_stat.st_ino) in parent_dirs:
                                    # Reached the point at which the directory
                                    # tree is already known.  Don't add any
                                    # more or we might go to an ancestor that
                                    # isn't being copied.
                                    break
                                new_parents.add((parent_stat.st_dev, parent_stat.st_ino))

                            if (dir_stats.st_dev, dir_stats.st_ino) in new_parents:
                                # This was a circular symlink.  So add it as
                                # a symlink
                                r_files['symlinks'].append((os.readlink(dirpath), dest_dirpath))
                            else:
                                # Walk the directory pointed to by the symlink
                                r_files['directories'].append((real_dir, dest_dirpath))
                                offset = len(real_dir) + 1
                                _recurse(real_dir, offset, parent_dirs.union(new_parents), rel_base=dest_dirpath)
                    else:
                        # Add the symlink to the destination
                        r_files['symlinks'].append((os.readlink(dirpath), dest_dirpath))
                else:
                    # Just a normal directory
                    r_files['directories'].append((dirpath, dest_dirpath))

    # Check if the source ends with a "/" so that we know which directory
    # level to work at (similar to rsync)
    source_trailing_slash = False
    if trailing_slash_detector:
        source_trailing_slash = trailing_slash_detector(topdir)
    else:
        source_trailing_slash = topdir.endswith(os.path.sep)

    # Calculate the offset needed to strip the base_path to make relative
    # paths
    if base_path is None:
        base_path = topdir
    if not source_trailing_slash:
        base_path = os.path.dirname(base_path)
    if topdir.startswith(base_path):
        offset = len(base_path)

    # Make sure we're making the new paths relative
    if trailing_slash_detector and not trailing_slash_detector(base_path):
        offset += 1
    elif not base_path.endswith(os.path.sep):
        offset += 1

    if os.path.islink(topdir) and not local_follow:
        r_files['symlinks'] = (os.readlink(topdir), os.path.basename(topdir))
        return r_files

    dir_stats = os.stat(topdir)
    parents = frozenset(((dir_stats.st_dev, dir_stats.st_ino),))
    # Actually walk the directory hierarchy
    _recurse(topdir, offset, parents)

    return r_files


class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def _ensure_invocation(self, result):
        # NOTE: adding invocation arguments here needs to be kept in sync with
        # any no_log specified in the argument_spec in the module.
        # This is not automatic.
        # NOTE: do not add to this. This should be made a generic function for action plugins.
        # This should also use the same argspec as the module instead of keeping it in sync.
        if 'invocation' not in result:
            if self._task.no_log:
                result['invocation'] = "CENSORED: no_log is set"
            else:
                # NOTE: Should be removed in the future. For now keep this broken
                # behaviour, have a look in the PR 51582
                result['invocation'] = self._task.args.copy()
                result['invocation']['module_args'] = self._task.args.copy()

        if isinstance(result['invocation'], dict):
            if 'content' in result['invocation']:
                result['invocation']['content'] = 'CENSORED: content is a no_log parameter'
            if result['invocation'].get('module_args', {}).get('content') is not None:
                result['invocation']['module_args']['content'] = 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'

        return result

    def _copy_file(self, source_full, source_rel, content, content_tempfile,
                   dest, task_vars, follow):
        decrypt = boolean(self._task.args.get('decrypt', True), strict=False)
        force = boolean(self._task.args.get('force', 'yes'), strict=False)
        raw = boolean(self._task.args.get('raw', 'no'), strict=False)

        result = {}
        result['diff'] = []

        # If the local file does not exist, get_real_file() raises AnsibleFileNotFound
        try:
            source_full = self._loader.get_real_file(source_full, decrypt=decrypt)
        except AnsibleFileNotFound as e:
            result['failed'] = True
            result['msg'] = "could not find src=%s, %s" % (source_full, to_text(e))
            return result

        # Get the local mode and set if user wanted it preserved
        # https://github.com/ansible/ansible-modules-core/issues/1124
        lmode = None
        if self._task.args.get('mode', None) == 'preserve':
            lmode = '0%03o' % stat.S_IMODE(os.stat(source_full).st_mode)

        # This is kind of optimization - if user told us destination is
        # dir, do path manipulation right away, otherwise we still check
        # for dest being a dir via remote call below.
        if self._connection._shell.path_has_trailing_slash(dest):
            dest_file = self._connection._shell.join_path(dest, source_rel)
        else:
            dest_file = dest

        # Attempt to get remote file info
        dest_status = self._execute_remote_stat(dest_file, all_vars=task_vars, follow=follow, checksum=force)

        if dest_status['exists'] and dest_status['isdir']:
            # The dest is a directory.
            if content is not None:
                # If source was defined as content remove the temporary file and fail out.
                self._remove_tempfile_if_content_defined(content, content_tempfile)
                result['failed'] = True
                result['msg'] = "can not use content with a dir as dest"
                return result
            else:
                # Append the relative source location to the destination and get remote stats again
                dest_file = self._connection._shell.join_path(dest, source_rel)
                dest_status = self._execute_remote_stat(dest_file, all_vars=task_vars, follow=follow, checksum=force)

        if dest_status['exists'] and not force:
            # remote_file exists so continue to next iteration.
            return None

        # Generate a hash of the local file.
        local_checksum = checksum(source_full)

        if local_checksum != dest_status['checksum']:
            # The checksums don't match and we will change or error out.

            if self._task.diff and not raw:
                result['diff'].append(self._get_diff_data(dest_file, source_full, task_vars, content))

            if self._task.check_mode:
                self._remove_tempfile_if_content_defined(content, content_tempfile)
                result['changed'] = True
                return result

            # Define a remote directory that we will copy the file to.
            tmp_src = self._connection._shell.join_path(self._connection._shell.tmpdir, '.source')

            # ensure we keep suffix for validate
            suffix = os.path.splitext(dest_file)[1]
            if suffix:
                tmp_src += suffix

            remote_path = None

            if not raw:
                remote_path = self._transfer_file(source_full, tmp_src)
            else:
                self._transfer_file(source_full, dest_file)

            # We have copied the file remotely and no longer require our content_tempfile
            self._remove_tempfile_if_content_defined(content, content_tempfile)
            self._loader.cleanup_tmp_file(source_full)

            # FIXME: I don't think this is needed when PIPELINING=0 because the source is created
            # world readable.  Access to the directory itself is controlled via fixup_perms2() as
            # part of executing the module. Check that umask with scp/sftp/piped doesn't cause
            # a problem before acting on this idea. (This idea would save a round-trip)
            # fix file permissions when the copy is done as a different user
            if remote_path:
                self._fixup_perms2((self._connection._shell.tmpdir, remote_path))

            if raw:
                # Continue to next iteration if raw is defined.
                return None

            # Run the copy module

            # src and dest here come after original and override them
            # we pass dest only to make sure it includes trailing slash in case of recursive copy
            new_module_args = _create_remote_copy_args(self._task.args)
            new_module_args.update(
                dict(
                    src=tmp_src,
                    dest=dest,
                    _original_basename=source_rel,
                    follow=follow
                )
            )
            if not self._task.args.get('checksum'):
                new_module_args['checksum'] = local_checksum

            if lmode:
                new_module_args['mode'] = lmode

            module_return = self._execute_module(module_name='ansible.legacy.copy', module_args=new_module_args, task_vars=task_vars)

        else:
            # no need to transfer the file, already correct hash, but still need to call
            # the file module in case we want to change attributes
            self._remove_tempfile_if_content_defined(content, content_tempfile)
            self._loader.cleanup_tmp_file(source_full)

            if raw:
                return None

            # Fix for https://github.com/ansible/ansible-modules-core/issues/1568.
            # If checksums match, and follow = True, find out if 'dest' is a link. If so,
            # change it to point to the source of the link.
            if follow:
                dest_status_nofollow = self._execute_remote_stat(dest_file, all_vars=task_vars, follow=False)
                if dest_status_nofollow['islnk'] and 'lnk_source' in dest_status_nofollow.keys():
                    dest = dest_status_nofollow['lnk_source']

            # Build temporary module_args.
            new_module_args = _create_remote_file_args(self._task.args)
            new_module_args.update(
                dict(
                    dest=dest,
                    _original_basename=source_rel,
                    recurse=False,
                    state='file',
                )
            )
            # src is sent to the file module in _original_basename, not in src
            try:
                del new_module_args['src']
            except KeyError:
                pass

            if lmode:
                new_module_args['mode'] = lmode

            # Execute the file module.
            module_return = self._execute_module(module_name='ansible.legacy.file', module_args=new_module_args, task_vars=task_vars)

        if not module_return.get('checksum'):
            module_return['checksum'] = local_checksum

        result.update(module_return)
        return result

    def _create_content_tempfile(self, content):
        """ Create a tempfile containing defined content """
        fd, content_tempfile = tempfile.mkstemp(dir=C.DEFAULT_LOCAL_TMP, prefix='.')
        content = to_bytes(content)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(content)
        except Exception as err:
            os.remove(content_tempfile)
            raise Exception(err)
        return content_tempfile

    def _remove_tempfile_if_content_defined(self, content, content_tempfile):
        if content is not None:
            os.remove(content_tempfile)

    def run(self, tmp=None, task_vars=None):
        """ handler for file transfer operations """
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        del tmp  # tmp no longer has any effect

        # ensure user is not setting internal parameters
        for internal in ('_original_basename', '_diff_peek'):
            if self._task.args.get(internal, None) is not None:
                raise AnsibleActionFail(f'Invalid parameter specified: "{internal}"')

        source = self._task.args.get('src', None)
        content = self._task.args.get('content', None)
        dest = self._task.args.get('dest', None)
        remote_src = boolean(self._task.args.get('remote_src', False), strict=False)
        local_follow = boolean(self._task.args.get('local_follow', True), strict=False)

        result['failed'] = True
        if not source and content is None:
            result['msg'] = 'src (or content) is required'
        elif not dest:
            result['msg'] = 'dest is required'
        elif source and content is not None:
            result['msg'] = 'src and content are mutually exclusive'
        elif content is not None and dest is not None and dest.endswith("/"):
            result['msg'] = "can not use content with a dir as dest"
        else:
            del result['failed']

        if result.get('failed'):
            return self._ensure_invocation(result)

        # Define content_tempfile in case we set it after finding content populated.
        content_tempfile = None

        # If content is defined make a tmp file and write the content into it.
        if content is not None:
            try:
                # If content comes to us as a dict it should be decoded json.
                # We need to encode it back into a string to write it out.
                if isinstance(content, dict) or isinstance(content, list):
                    content_tempfile = self._create_content_tempfile(json.dumps(content))
                else:
                    content_tempfile = self._create_content_tempfile(content)
                source = content_tempfile
            except Exception as ex:
                self._ensure_invocation(result)

                raise AnsibleActionFail(message="could not write content temp file", result=result) from ex

        # if we have first_available_file in our vars
        # look up the files and use the first one we find as src
        elif remote_src:
            result.update(self._execute_module(module_name='ansible.legacy.copy', task_vars=task_vars))
            return self._ensure_invocation(result)
        else:
            # find_needle returns a path that may not have a trailing slash on
            # a directory so we need to determine that now (we use it just
            # like rsync does to figure out whether to include the directory
            # or only the files inside the directory
            trailing_slash = source.endswith(os.path.sep)
            try:
                # find in expected paths
                source = self._find_needle('files', source)
            except AnsibleError as ex:
                self._ensure_invocation(result)

                raise AnsibleActionFail(result=result) from ex

            if trailing_slash != source.endswith(os.path.sep):
                if source[-1] == os.path.sep:
                    source = source[:-1]
                else:
                    source = source + os.path.sep

        # A list of source file tuples (full_path, relative_path) which will try to copy to the destination
        source_files = {'files': [], 'directories': [], 'symlinks': []}

        # If source is a directory populate our list else source is a file and translate it to a tuple.
        if os.path.isdir(to_bytes(source, errors='surrogate_or_strict')):
            # Get a list of the files we want to replicate on the remote side
            source_files = _walk_dirs(source, local_follow=local_follow,
                                      trailing_slash_detector=self._connection._shell.path_has_trailing_slash)

            # If it's recursive copy, destination is always a dir,
            # explicitly mark it so (note - copy module relies on this).
            if not self._connection._shell.path_has_trailing_slash(dest):
                dest = self._connection._shell.join_path(dest, '')
            # FIXME: Can we optimize cases where there's only one file, no
            # symlinks and any number of directories?  In the original code,
            # empty directories are not copied....
        else:
            source_files['files'] = [(source, os.path.basename(source))]

        changed = False
        module_return = dict(changed=False)

        # A register for if we executed a module.
        # Used to cut down on command calls when not recursive.
        module_executed = False

        # expand any user home dir specifier
        dest = self._remote_expand_user(dest)

        implicit_directories = set()
        for source_full, source_rel in source_files['files']:
            # copy files over.  This happens first as directories that have
            # a file do not need to be created later

            # We only follow symlinks for files in the non-recursive case
            if source_files['directories']:
                follow = False
            else:
                follow = boolean(self._task.args.get('follow', False), strict=False)

            module_return = self._copy_file(source_full, source_rel, content, content_tempfile, dest, task_vars, follow)
            if module_return is None:
                continue

            if module_return.get('failed'):
                result.update(module_return)
                return self._ensure_invocation(result)

            paths = os.path.split(source_rel)
            dir_path = ''
            for dir_component in paths:
                os.path.join(dir_path, dir_component)
                implicit_directories.add(dir_path)
            if 'diff' in result and not result['diff']:
                del result['diff']
            module_executed = True
            changed = changed or module_return.get('changed', False)

        for src, dest_path in source_files['directories']:
            # Find directories that are leaves as they might not have been
            # created yet.
            if dest_path in implicit_directories:
                continue

            # Use file module to create these
            new_module_args = _create_remote_file_args(self._task.args)
            new_module_args['path'] = os.path.join(dest, dest_path)
            new_module_args['state'] = 'directory'
            new_module_args['mode'] = self._task.args.get('directory_mode', None)
            new_module_args['recurse'] = False
            del new_module_args['src']

            module_return = self._execute_module(module_name='ansible.legacy.file', module_args=new_module_args, task_vars=task_vars)

            if module_return.get('failed'):
                result.update(module_return)
                return self._ensure_invocation(result)

            module_executed = True
            changed = changed or module_return.get('changed', False)

        for target_path, dest_path in source_files['symlinks']:
            # Copy symlinks over
            new_module_args = _create_remote_file_args(self._task.args)
            new_module_args['path'] = os.path.join(dest, dest_path)
            new_module_args['src'] = target_path
            new_module_args['state'] = 'link'
            new_module_args['force'] = True

            # Only follow remote symlinks in the non-recursive case
            if source_files['directories']:
                new_module_args['follow'] = False

            # file module cannot deal with 'preserve' mode and is meaningless
            # for symlinks anyway, so just don't pass it.
            if new_module_args.get('mode', None) == 'preserve':
                new_module_args.pop('mode')

            module_return = self._execute_module(module_name='ansible.legacy.file', module_args=new_module_args, task_vars=task_vars)
            module_executed = True

            if module_return.get('failed'):
                result.update(module_return)
                return self._ensure_invocation(result)

            changed = changed or module_return.get('changed', False)

        if module_executed and len(source_files['files']) == 1:
            result.update(module_return)

            # the file module returns the file path as 'path', but
            # the copy module uses 'dest', so add it if it's not there
            if 'path' in result and 'dest' not in result:
                result['dest'] = result['path']
        else:
            result.update(dict(dest=dest, src=source, changed=changed))

        # Delete tmp path
        self._remove_tmp_path(self._connection._shell.tmpdir)

        return self._ensure_invocation(result)
