# This file is part of Ansible

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import base64
import json
import os
import os.path
import shutil
import tempfile
import traceback
import zipfile

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase
from ansible.utils.hashing import checksum


def _walk_dirs(topdir, loader, decrypt=True, base_path=None, local_follow=False, trailing_slash_detector=None, checksum_check=False):
    """
    Walk a filesystem tree returning enough information to copy the files.
    This is similar to the _walk_dirs function in ``copy.py`` but returns
    a dict instead of a tuple for each entry and includes the checksum of
    a local file if wanted.

    :arg topdir: The directory that the filesystem tree is rooted at
    :arg loader: The self._loader object from ActionBase
    :kwarg decrypt: Whether to decrypt a file encrypted with ansible-vault
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
    :kawrg whether to get the checksum of the local file and add to the dict
    :returns: dictionary of dictionaries. All of the path elements in the structure are text string.
            This separates all the files, directories, and symlinks along with
            import information about each::

                {
                    'files'; [{
                        src: '/absolute/path/to/copy/from',
                        dest: 'relative/path/to/copy/to',
                        checksum: 'b54ba7f5621240d403f06815f7246006ef8c7d43'
                    }, ...],
                    'directories'; [{
                        src: '/absolute/path/to/copy/from',
                        dest: 'relative/path/to/copy/to'
                    }, ...],
                    'symlinks'; [{
                        src: '/symlink/target/path',
                        dest: 'relative/path/to/copy/to'
                    }, ...],

                }

        The ``symlinks`` field is only populated if ``local_follow`` is set to False
        *or* a circular symlink cannot be dereferenced. The ``checksum`` entry is set
        to None if checksum_check=False.

    """
    # Convert the path segments into byte strings

    r_files = {'files': [], 'directories': [], 'symlinks': []}

    def _recurse(topdir, rel_offset, parent_dirs, rel_base=u'', checksum_check=False):
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
                    real_file = loader.get_real_file(os.path.realpath(filepath), decrypt=decrypt)
                    if local_follow and os.path.isfile(real_file):
                        # Add the file pointed to by the symlink
                        r_files['files'].append(
                            {
                                "src": real_file,
                                "dest": dest_filepath,
                                "checksum": _get_local_checksum(checksum_check, real_file)
                            }
                        )
                    else:
                        # Mark this file as a symlink to copy
                        r_files['symlinks'].append({"src": os.readlink(filepath), "dest": dest_filepath})
                else:
                    # Just a normal file
                    real_file = loader.get_real_file(filepath, decrypt=decrypt)
                    r_files['files'].append(
                        {
                            "src": real_file,
                            "dest": dest_filepath,
                            "checksum": _get_local_checksum(checksum_check, real_file)
                        }
                    )

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
                            r_files['symlinks'].append({"src": os.readlink(dirpath), "dest": dest_dirpath})
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
                                r_files['symlinks'].append({"src": os.readlink(dirpath), "dest": dest_dirpath})
                            else:
                                # Walk the directory pointed to by the symlink
                                r_files['directories'].append({"src": real_dir, "dest": dest_dirpath})
                                offset = len(real_dir) + 1
                                _recurse(real_dir, offset, parent_dirs.union(new_parents),
                                         rel_base=dest_dirpath,
                                         checksum_check=checksum_check)
                    else:
                        # Add the symlink to the destination
                        r_files['symlinks'].append({"src": os.readlink(dirpath), "dest": dest_dirpath})
                else:
                    # Just a normal directory
                    r_files['directories'].append({"src": dirpath, "dest": dest_dirpath})

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
        r_files['symlinks'] = {"src": os.readlink(topdir), "dest": os.path.basename(topdir)}
        return r_files

    dir_stats = os.stat(topdir)
    parents = frozenset(((dir_stats.st_dev, dir_stats.st_ino),))
    # Actually walk the directory hierarchy
    _recurse(topdir, offset, parents, checksum_check=checksum_check)

    return r_files


def _get_local_checksum(get_checksum, local_path):
    if get_checksum:
        return checksum(local_path)
    else:
        return None


class ActionModule(ActionBase):

    WIN_PATH_SEPARATOR = "\\"

    def _create_content_tempfile(self, content):
        """ Create a tempfile containing defined content """
        fd, content_tempfile = tempfile.mkstemp(dir=C.DEFAULT_LOCAL_TMP)
        content = to_bytes(content)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(content)
        except Exception as err:
            os.remove(content_tempfile)
            raise Exception(err)
        return content_tempfile

    def _create_zip_tempfile(self, files, directories):
        tmpdir = tempfile.mkdtemp(dir=C.DEFAULT_LOCAL_TMP)
        zip_file_path = os.path.join(tmpdir, "win_copy.zip")
        zip_file = zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_STORED, True)

        # encoding the file/dir name with base64 so Windows can unzip a unicode
        # filename and get the right name, Windows doesn't handle unicode names
        # very well
        for directory in directories:
            directory_path = to_bytes(directory['src'], errors='surrogate_or_strict')
            archive_path = to_bytes(directory['dest'], errors='surrogate_or_strict')

            encoded_path = to_text(base64.b64encode(archive_path), errors='surrogate_or_strict')
            zip_file.write(directory_path, encoded_path, zipfile.ZIP_DEFLATED)

        for file in files:
            file_path = to_bytes(file['src'], errors='surrogate_or_strict')
            archive_path = to_bytes(file['dest'], errors='surrogate_or_strict')

            encoded_path = to_text(base64.b64encode(archive_path), errors='surrogate_or_strict')
            zip_file.write(file_path, encoded_path, zipfile.ZIP_DEFLATED)

        return zip_file_path

    def _remove_tempfile_if_content_defined(self, content, content_tempfile):
        if content is not None:
            os.remove(content_tempfile)

    def _copy_single_file(self, local_file, dest, source_rel, task_vars, tmp, backup):
        if self._play_context.check_mode:
            module_return = dict(changed=True)
            return module_return

        # copy the file across to the server
        tmp_src = self._connection._shell.join_path(tmp, 'source')
        self._transfer_file(local_file, tmp_src)

        copy_args = self._task.args.copy()
        copy_args.update(
            dict(
                dest=dest,
                src=tmp_src,
                _original_basename=source_rel,
                _copy_mode="single",
                backup=backup,
            )
        )
        copy_args.pop('content', None)

        copy_result = self._execute_module(module_name="copy",
                                           module_args=copy_args,
                                           task_vars=task_vars)

        return copy_result

    def _copy_zip_file(self, dest, files, directories, task_vars, tmp, backup):
        # create local zip file containing all the files and directories that
        # need to be copied to the server
        if self._play_context.check_mode:
            module_return = dict(changed=True)
            return module_return

        try:
            zip_file = self._create_zip_tempfile(files, directories)
        except Exception as e:
            module_return = dict(
                changed=False,
                failed=True,
                msg="failed to create tmp zip file: %s" % to_text(e),
                exception=traceback.format_exc()
            )
            return module_return

        zip_path = self._loader.get_real_file(zip_file)

        # send zip file to remote, file must end in .zip so
        # Com Shell.Application works
        tmp_src = self._connection._shell.join_path(tmp, 'source.zip')
        self._transfer_file(zip_path, tmp_src)

        # run the explode operation of win_copy on remote
        copy_args = self._task.args.copy()
        copy_args.update(
            dict(
                src=tmp_src,
                dest=dest,
                _copy_mode="explode",
                backup=backup,
            )
        )
        copy_args.pop('content', None)
        module_return = self._execute_module(module_name='copy',
                                             module_args=copy_args,
                                             task_vars=task_vars)
        shutil.rmtree(os.path.dirname(zip_path))
        return module_return

    def run(self, tmp=None, task_vars=None):
        """ handler for file transfer operations """
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        source = self._task.args.get('src', None)
        content = self._task.args.get('content', None)
        dest = self._task.args.get('dest', None)
        remote_src = boolean(self._task.args.get('remote_src', False), strict=False)
        local_follow = boolean(self._task.args.get('local_follow', False), strict=False)
        force = boolean(self._task.args.get('force', True), strict=False)
        decrypt = boolean(self._task.args.get('decrypt', True), strict=False)
        backup = boolean(self._task.args.get('backup', False), strict=False)

        result['src'] = source
        result['dest'] = dest

        result['failed'] = True
        if (source is None and content is None) or dest is None:
            result['msg'] = "src (or content) and dest are required"
        elif source is not None and content is not None:
            result['msg'] = "src and content are mutually exclusive"
        elif content is not None and dest is not None and (
                dest.endswith(os.path.sep) or dest.endswith(self.WIN_PATH_SEPARATOR)):
            result['msg'] = "dest must be a file if content is defined"
        else:
            del result['failed']

        if result.get('failed'):
            return result

        # If content is defined make a temp file and write the content into it
        content_tempfile = None
        if content is not None:
            try:
                # if content comes to us as a dict it should be decoded json.
                # We need to encode it back into a string and write it out
                if isinstance(content, dict) or isinstance(content, list):
                    content_tempfile = self._create_content_tempfile(json.dumps(content))
                else:
                    content_tempfile = self._create_content_tempfile(content)
                source = content_tempfile
            except Exception as err:
                result['failed'] = True
                result['msg'] = "could not write content tmp file: %s" % to_native(err)
                return result
        # all actions should occur on the remote server, run win_copy module
        elif remote_src:
            new_module_args = self._task.args.copy()
            new_module_args.update(
                dict(
                    _copy_mode="remote",
                    dest=dest,
                    src=source,
                    force=force,
                    backup=backup,
                )
            )
            new_module_args.pop('content', None)
            result.update(self._execute_module(module_args=new_module_args, task_vars=task_vars))
            return result
        # find_needle returns a path that may not have a trailing slash on a
        # directory so we need to find that out first and append at the end
        else:
            trailing_slash = source.endswith(os.path.sep)
            try:
                # find in expected paths
                source = self._find_needle('files', source)
            except AnsibleError as e:
                result['failed'] = True
                result['msg'] = to_text(e)
                result['exception'] = traceback.format_exc()
                return result

            if trailing_slash != source.endswith(os.path.sep):
                if source[-1] == os.path.sep:
                    source = source[:-1]
                else:
                    source = source + os.path.sep

        # A list of source file tuples (full_path, relative_path) which will try to copy to the destination
        source_files = {'files': [], 'directories': [], 'symlinks': []}

        # If source is a directory populate our list else source is a file and translate it to a tuple.
        if os.path.isdir(to_bytes(source, errors='surrogate_or_strict')):
            result['operation'] = 'folder_copy'

            # Get a list of the files we want to replicate on the remote side
            source_files = _walk_dirs(source, self._loader, decrypt=decrypt, local_follow=local_follow,
                                      trailing_slash_detector=self._connection._shell.path_has_trailing_slash,
                                      checksum_check=force)

            # If it's recursive copy, destination is always a dir,
            # explicitly mark it so (note - win_copy module relies on this).
            if not self._connection._shell.path_has_trailing_slash(dest):
                dest = "%s%s" % (dest, self.WIN_PATH_SEPARATOR)

            check_dest = dest
        # Source is a file, add details to source_files dict
        else:
            result['operation'] = 'file_copy'

            # If the local file does not exist, get_real_file() raises AnsibleFileNotFound
            try:
                source_full = self._loader.get_real_file(source, decrypt=decrypt)
            except AnsibleFileNotFound as e:
                result['failed'] = True
                result['msg'] = "could not find src=%s, %s" % (source, to_text(e))
                return result

            original_basename = os.path.basename(source)
            result['original_basename'] = original_basename

            # check if dest ends with / or \ and append source filename to dest
            if self._connection._shell.path_has_trailing_slash(dest):
                check_dest = dest
                filename = original_basename
                result['dest'] = self._connection._shell.join_path(dest, filename)
            else:
                # replace \\ with / so we can use os.path to get the filename or dirname
                unix_path = dest.replace(self.WIN_PATH_SEPARATOR, os.path.sep)
                filename = os.path.basename(unix_path)
                check_dest = os.path.dirname(unix_path)

            file_checksum = _get_local_checksum(force, source_full)
            source_files['files'].append(
                dict(
                    src=source_full,
                    dest=filename,
                    checksum=file_checksum
                )
            )
            result['checksum'] = file_checksum
            result['size'] = os.path.getsize(to_bytes(source_full, errors='surrogate_or_strict'))

        # find out the files/directories/symlinks that we need to copy to the server
        query_args = self._task.args.copy()
        query_args.update(
            dict(
                _copy_mode="query",
                dest=check_dest,
                force=force,
                files=source_files['files'],
                directories=source_files['directories'],
                symlinks=source_files['symlinks'],
            )
        )
        # src is not required for query, will fail path validation is src has unix allowed chars
        query_args.pop('src', None)

        query_args.pop('content', None)
        query_return = self._execute_module(module_args=query_args,
                                            task_vars=task_vars)

        if query_return.get('failed') is True:
            result.update(query_return)
            return result

        if len(query_return['files']) > 0 or len(query_return['directories']) > 0 and self._connection._shell.tmpdir is None:
            self._connection._shell.tmpdir = self._make_tmp_path()

        if len(query_return['files']) == 1 and len(query_return['directories']) == 0:
            # we only need to copy 1 file, don't mess around with zips
            file_src = query_return['files'][0]['src']
            file_dest = query_return['files'][0]['dest']
            result.update(self._copy_single_file(file_src, dest, file_dest,
                                                 task_vars, self._connection._shell.tmpdir, backup))
            if result.get('failed') is True:
                result['msg'] = "failed to copy file %s: %s" % (file_src, result['msg'])
            result['changed'] = True

        elif len(query_return['files']) > 0 or len(query_return['directories']) > 0:
            # either multiple files or directories need to be copied, compress
            # to a zip and 'explode' the zip on the server
            # TODO: handle symlinks
            result.update(self._copy_zip_file(dest, source_files['files'],
                                              source_files['directories'],
                                              task_vars, self._connection._shell.tmpdir, backup))
            result['changed'] = True
        else:
            # no operations need to occur
            result['failed'] = False
            result['changed'] = False

        # remove the content tmp file and remote tmp file if it was created
        self._remove_tempfile_if_content_defined(content, content_tempfile)
        self._remove_tmp_path(self._connection._shell.tmpdir)
        return result
