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

import os

from ansible import utils
import ansible.constants as C
import ansible.utils.template as template
from ansible import errors
from ansible.runner.return_data import ReturnData
import base64
import json
import stat
import tempfile
import pipes

## fixes https://github.com/ansible/ansible/issues/3518
# http://mypy.pythonblogs.com/12_mypy/archive/1253_workaround_for_python_bug_ascii_codec_cant_encode_character_uxa0_in_position_111_ordinal_not_in_range128.html
import sys
reload(sys)
sys.setdefaultencoding("utf8")


class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp_path, module_name, module_args, inject, complex_args=None, **kwargs):
        ''' handler for file transfer operations '''

        # load up options
        options = {}
        if complex_args:
            options.update(complex_args)
        options.update(utils.parse_kv(module_args))
        source  = options.get('src', None)
        content = options.get('content', None)
        dest    = options.get('dest', None)
        raw     = utils.boolean(options.get('raw', 'no'))
        force   = utils.boolean(options.get('force', 'yes'))

        # content with newlines is going to be escaped to safely load in yaml
        # now we need to unescape it so that the newlines are evaluated properly
        # when writing the file to disk
        if content:
            if isinstance(content, unicode):
                try:
                    content = content.decode('unicode-escape')
                except UnicodeDecodeError:
                    pass

        if (source is None and content is None and not 'first_available_file' in inject) or dest is None:
            result=dict(failed=True, msg="src (or content) and dest are required")
            return ReturnData(conn=conn, result=result)
        elif (source is not None or 'first_available_file' in inject) and content is not None:
            result=dict(failed=True, msg="src and content are mutually exclusive")
            return ReturnData(conn=conn, result=result)

        # Check if the source ends with a "/"
        source_trailing_slash = False
        if source:
            source_trailing_slash = source.endswith("/")

        # Define content_tempfile in case we set it after finding content populated.
        content_tempfile = None

        # If content is defined make a temp file and write the content into it.
        if content is not None:
            try:
                # If content comes to us as a dict it should be decoded json.
                # We need to encode it back into a string to write it out.
                if type(content) is dict:
                    content_tempfile = self._create_content_tempfile(json.dumps(content))
                else:
                    content_tempfile = self._create_content_tempfile(content)
                source = content_tempfile
            except Exception, err:
                result = dict(failed=True, msg="could not write content temp file: %s" % err)
                return ReturnData(conn=conn, result=result)
        # if we have first_available_file in our vars
        # look up the files and use the first one we find as src
        elif 'first_available_file' in inject:
            found = False
            for fn in inject.get('first_available_file'):
                fn_orig = fn
                fnt = template.template(self.runner.basedir, fn, inject)
                fnd = utils.path_dwim(self.runner.basedir, fnt)
                if not os.path.exists(fnd) and '_original_file' in inject:
                    fnd = utils.path_dwim_relative(inject['_original_file'], 'files', fnt, self.runner.basedir, check=False)
                if os.path.exists(fnd):
                    source = fnd
                    found = True
                    break
            if not found:
                results = dict(failed=True, msg="could not find src in first_available_file list")
                return ReturnData(conn=conn, result=results)
        else:
            source = template.template(self.runner.basedir, source, inject)
            if '_original_file' in inject:
                source = utils.path_dwim_relative(inject['_original_file'], 'files', source, self.runner.basedir)
            else:
                source = utils.path_dwim(self.runner.basedir, source)

        # A list of source file tuples (full_path, relative_path) which will try to copy to the destination
        source_files = []

        # If source is a directory populate our list else source is a file and translate it to a tuple.
        if os.path.isdir(source):
            # Get the amount of spaces to remove to get the relative path.
            if source_trailing_slash:
                sz = len(source) + 1
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
            if not conn.shell.path_has_trailing_slash(dest):
                dest = conn.shell.join_path(dest, '')
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

        # If this is a recursive action create a tmp_path that we can share as the _exec_module create is too late.
        if not delete_remote_tmp:
            if "-tmp-" not in tmp_path:
                tmp_path = self.runner._make_tmp_path(conn)

        # expand any user home dir specifier
        dest = self.runner._remote_expand_user(conn, dest, tmp_path)

        for source_full, source_rel in source_files:
            # Generate a hash of the local file.
            local_checksum = utils.checksum(source_full)

            # If local_checksum is not defined we can't find the file so we should fail out.
            if local_checksum is None:
                result = dict(failed=True, msg="could not find src=%s" % source_full)
                return ReturnData(conn=conn, result=result)

            # This is kind of optimization - if user told us destination is
            # dir, do path manipulation right away, otherwise we still check
            # for dest being a dir via remote call below.
            if conn.shell.path_has_trailing_slash(dest):
                dest_file = conn.shell.join_path(dest, source_rel)
            else:
                dest_file = conn.shell.join_path(dest)

            # Attempt to get the remote checksum
            remote_checksum = self.runner._remote_checksum(conn, tmp_path, dest_file, inject)

            if remote_checksum == '3':
                # The remote_checksum was executed on a directory.
                if content is not None:
                    # If source was defined as content remove the temporary file and fail out.
                    self._remove_tempfile_if_content_defined(content, content_tempfile)
                    result = dict(failed=True, msg="can not use content with a dir as dest")
                    return ReturnData(conn=conn, result=result)
                else:
                    # Append the relative source location to the destination and retry remote_checksum.
                    dest_file = conn.shell.join_path(dest, source_rel)
                    remote_checksum = self.runner._remote_checksum(conn, tmp_path, dest_file, inject)

            if remote_checksum != '1' and not force:
                # remote_file does not exist so continue to next iteration.
                continue

            if local_checksum != remote_checksum:
                # The checksums don't match and we will change or error out.
                changed = True

                # Create a tmp_path if missing only if this is not recursive.
                # If this is recursive we already have a tmp_path.
                if delete_remote_tmp:
                    if "-tmp-" not in tmp_path:
                        tmp_path = self.runner._make_tmp_path(conn)

                if self.runner.diff and not raw:
                    diff = self._get_diff_data(conn, tmp_path, inject, dest_file, source_full)
                else:
                    diff = {}

                if self.runner.noop_on_check(inject):
                    self._remove_tempfile_if_content_defined(content, content_tempfile)
                    diffs.append(diff)
                    changed = True
                    module_result = dict(changed=True)
                    continue

                # Define a remote directory that we will copy the file to.
                tmp_src = tmp_path + 'source'

                if not raw:
                    conn.put_file(source_full, tmp_src)
                else:
                    conn.put_file(source_full, dest_file)

                # We have copied the file remotely and no longer require our content_tempfile
                self._remove_tempfile_if_content_defined(content, content_tempfile)

                # fix file permissions when the copy is done as a different user
                if self.runner.become and self.runner.become_user != 'root' and not raw:
                    self.runner._remote_chmod(conn, 'a+r', tmp_src, tmp_path)

                if raw:
                    # Continue to next iteration if raw is defined.
                    continue

                # Run the copy module

                # src and dest here come after original and override them
                # we pass dest only to make sure it includes trailing slash in case of recursive copy
                new_module_args = dict(
                    src=tmp_src,
                    dest=dest,
                    original_basename=source_rel
                )
                if self.runner.noop_on_check(inject):
                    new_module_args['CHECKMODE'] = True
                if self.runner.no_log:
                    new_module_args['NO_LOG'] = True

                module_args_tmp = utils.merge_module_args(module_args, new_module_args)

                module_return = self.runner._execute_module(conn, tmp_path, 'win_copy', module_args_tmp, inject=inject, complex_args=complex_args, delete_remote_tmp=delete_remote_tmp)
                module_executed = True

            else:
                # no need to transfer the file, already correct md5, but still need to call
                # the file module in case we want to change attributes
                self._remove_tempfile_if_content_defined(content, content_tempfile)

                if raw:
                    # Continue to next iteration if raw is defined.
                    # self.runner._remove_tmp_path(conn, tmp_path)
                    continue

                tmp_src = tmp_path + source_rel

                # Build temporary module_args.
                new_module_args = dict(
                    src=tmp_src,
                    dest=dest,
                    original_basename=source_rel
                )
                if self.runner.noop_on_check(inject):
                    new_module_args['CHECKMODE'] = True
                if self.runner.no_log:
                    new_module_args['NO_LOG'] = True

                module_args_tmp = utils.merge_module_args(module_args, new_module_args)

                # Execute the file module.
                module_return = self.runner._execute_module(conn, tmp_path, 'win_file', module_args_tmp, inject=inject, complex_args=complex_args, delete_remote_tmp=delete_remote_tmp)
                module_executed = True

            module_result = module_return.result
            if not module_result.get('checksum'):
                module_result['checksum'] = local_checksum
            if module_result.get('failed') == True:
                return module_return
            if module_result.get('changed') == True:
                changed = True

        # Delete tmp_path if we were recursive or if we did not execute a module.
        if (not C.DEFAULT_KEEP_REMOTE_FILES and not delete_remote_tmp) \
            or (not C.DEFAULT_KEEP_REMOTE_FILES and delete_remote_tmp and not module_executed):
            self.runner._remove_tmp_path(conn, tmp_path)

        # the file module returns the file path as 'path', but
        # the copy module uses 'dest', so add it if it's not there
        if 'path' in module_result and 'dest' not in module_result:
            module_result['dest'] = module_result['path']

        # TODO: Support detailed status/diff for multiple files
        if len(source_files) == 1:
            result = module_result
        else:
            result = dict(dest=dest, src=source, changed=changed)
        if len(diffs) == 1:
            return ReturnData(conn=conn, result=result, diff=diffs[0])
        else:
            return ReturnData(conn=conn, result=result)

    def _create_content_tempfile(self, content):
        ''' Create a tempfile containing defined content '''
        fd, content_tempfile = tempfile.mkstemp()
        f = os.fdopen(fd, 'w')
        try:
            f.write(content)
        except Exception, err:
            os.remove(content_tempfile)
            raise Exception(err)
        finally:
            f.close()
        return content_tempfile

    def _get_diff_data(self, conn, tmp, inject, destination, source):
        peek_result = self.runner._execute_module(conn, tmp, 'win_file', "path=%s diff_peek=1" % destination, inject=inject, persist_files=True)

        if not peek_result.is_successful():
            return {}

        diff = {}
        if peek_result.result['state'] == 'absent':
            diff['before'] = ''
        elif peek_result.result['appears_binary']:
            diff['dst_binary'] = 1
        elif peek_result.result['size'] > utils.MAX_FILE_SIZE_FOR_DIFF:
            diff['dst_larger'] = utils.MAX_FILE_SIZE_FOR_DIFF
        else:
            dest_result = self.runner._execute_module(conn, tmp, 'slurp', "path=%s" % destination, inject=inject, persist_files=True)
            if 'content' in dest_result.result:
                dest_contents = dest_result.result['content']
                if dest_result.result['encoding'] == 'base64':
                    dest_contents = base64.b64decode(dest_contents)
                else:
                    raise Exception("unknown encoding, failed: %s" % dest_result.result)
                diff['before_header'] = destination
                diff['before'] = dest_contents

        src = open(source)
        src_contents = src.read(8192)
        st = os.stat(source)
        if "\x00" in src_contents:
            diff['src_binary'] = 1
        elif st[stat.ST_SIZE] > utils.MAX_FILE_SIZE_FOR_DIFF:
            diff['src_larger'] = utils.MAX_FILE_SIZE_FOR_DIFF
        else:
            src.seek(0)
            diff['after_header'] = source
            diff['after'] = src.read()

        return diff

    def _remove_tempfile_if_content_defined(self, content, content_tempfile):
        if content is not None:
            os.remove(content_tempfile)


    def _result_key_merge(self, options, results):
        # add keys to file module results to mimic copy
        if 'path' in results.result and 'dest' not in results.result:
            results.result['dest'] = results.result['path']
            del results.result['path']
        return results
