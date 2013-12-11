# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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
import ansible.utils.template as template
from ansible import errors
from ansible.runner.return_data import ReturnData
import base64
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

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):
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

        if (source is None and content is None and not 'first_available_file' in inject) or dest is None:
            result=dict(failed=True, msg="src (or content) and dest are required")
            return ReturnData(conn=conn, result=result)
        elif (source is not None or 'first_available_file' in inject) and content is not None:
            result=dict(failed=True, msg="src and content are mutually exclusive")
            return ReturnData(conn=conn, result=result)

        source_trailing_slash = False
        if source:
            source_trailing_slash = source.endswith("/")

        # if we have first_available_file in our vars
        # look up the files and use the first one we find as src
        if 'first_available_file' in inject:
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
                results=dict(failed=True, msg="could not find src in first_available_file list")
                return ReturnData(conn=conn, result=results)
        elif content is not None:
            fd, tmp_content = tempfile.mkstemp()
            f = os.fdopen(fd, 'w')
            try:
                f.write(content)
            except Exception, err:
                os.remove(tmp_content)
                result = dict(failed=True, msg="could not write content temp file: %s" % err)
                return ReturnData(conn=conn, result=result)
            f.close()
            source = tmp_content
        else:
            source = template.template(self.runner.basedir, source, inject)
            if '_original_file' in inject:
                source = utils.path_dwim_relative(inject['_original_file'], 'files', source, self.runner.basedir)
            else:
                source = utils.path_dwim(self.runner.basedir, source)


        source_files = []
        if os.path.isdir(source):
            # Implement rsync-like behavior: if source is "dir/" , only
            # inside its contents will be copied to destination. Otherwise
            # if it's "dir", dir itself will be copied to destination.
            if source_trailing_slash:
                sz = len(source) + 1
            else:
                sz = len(source.rsplit('/', 1)[0]) + 1
            for base_path, sub_folders, files in os.walk(source):
                for file in files:
                    full_path = os.path.join(base_path, file)
                    rel_path = full_path[sz:]
                    source_files.append((full_path, rel_path))
            # If it's recursive copy, destination is always a dir,
            # explictly mark it so (note - copy module relies on this).
            if not dest.endswith("/"):
                dest += "/"
        else:
            source_files.append((source, os.path.basename(source)))

        changed = False
        diffs = []
        module_result = {"changed": False}
        for source_full, source_rel in source_files:
            # We need to get a new tmp path for each file, otherwise the copy module deletes the folder.
            tmp = self.runner._make_tmp_path(conn)
            local_md5 = utils.md5(source_full)

            if local_md5 is None:
                result=dict(failed=True, msg="could not find src=%s" % source_full)
                return ReturnData(conn=conn, result=result)

            # This is kind of optimization - if user told us destination is
            # dir, do path manipulation right away, otherwise we still check
            # for dest being a dir via remote call below.
            if dest.endswith("/"):
                dest_file = os.path.join(dest, source_rel)
            else:
                dest_file = dest

            remote_md5 = self.runner._remote_md5(conn, tmp, dest_file)
            if remote_md5 == '3':
                # Destination is a directory
                if content is not None:
                    os.remove(tmp_content)
                    result = dict(failed=True, msg="can not use content with a dir as dest")
                    return ReturnData(conn=conn, result=result)
                dest_file = os.path.join(dest, source_rel)
                remote_md5 = self.runner._remote_md5(conn, tmp, dest_file)

            # remote_md5 == '1' would mean that the file does not exist.
            if remote_md5 != '1' and not force:
                continue

            exec_rc = None
            if local_md5 != remote_md5:
                # Assume we either really change file or error out
                changed = True

                if self.runner.diff and not raw:
                    diff = self._get_diff_data(conn, tmp, inject, dest_file, source_full)
                else:
                    diff = {}

                if self.runner.noop_on_check(inject):
                    if content is not None:
                        os.remove(tmp_content)
                    diffs.append(diff)
                    changed = True
                    module_result = dict(changed=True)
                    continue


                # transfer the file to a remote tmp location
                tmp_src = tmp + 'source'

                if not raw:
                    conn.put_file(source_full, tmp_src)
                else:
                    conn.put_file(source_full, dest_file)

                if content is not None:
                    os.remove(tmp_content)

                # fix file permissions when the copy is done as a different user
                if self.runner.sudo and self.runner.sudo_user != 'root' and not raw:
                    self.runner._low_level_exec_command(conn, "chmod a+r %s" % tmp_src, tmp)

                if raw:
                    continue

                # run the copy module
                if raw:
                    # don't send down raw=no
                    module_args.pop('raw')

                # src and dest here come after original and override them
                # we pass dest only to make sure it includes trailing slash
                # in case of recursive copy
                module_args_tmp = "%s src=%s dest=%s original_basename=%s" % (module_args,
                                  pipes.quote(tmp_src), pipes.quote(dest), pipes.quote(source_rel))
                module_return = self.runner._execute_module(conn, tmp, 'copy', module_args_tmp, inject=inject, complex_args=complex_args)

            else:
                # no need to transfer the file, already correct md5, but still need to call
                # the file module in case we want to change attributes
                if content is not None:
                    os.remove(tmp_content)

                if raw:
                    continue

                tmp_src = tmp + source_rel
                if raw:
                    # don't send down raw=no
                    module_args.pop('raw')
                module_args_tmp = "%s src=%s original_basename=%s" % (module_args,
                                  pipes.quote(tmp_src), pipes.quote(source_rel))
                if self.runner.noop_on_check(inject):
                    module_args_tmp = "%s CHECKMODE=True" % module_args_tmp
                module_return = self.runner._execute_module(conn, tmp, 'file', module_args_tmp, inject=inject, complex_args=complex_args)

            module_result = module_return.result
            if module_result.get('failed') == True:
                return module_return
            if module_result.get('changed') == True:
                changed = True

        # TODO: Support detailed status/diff for multiple files
        if len(source_files) == 1:
            result = module_result
        else:
            result = dict(dest=dest, src=source, changed=changed)
        if len(diffs) == 1:
            return ReturnData(conn=conn, result=result, diff=diffs[0])
        else:
            return ReturnData(conn=conn, result=result)

    def _get_diff_data(self, conn, tmp, inject, destination, source):
        peek_result = self.runner._execute_module(conn, tmp, 'file', "path=%s diff_peek=1" % destination, inject=inject, persist_files=True)

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
        if src_contents.find("\x00") != -1:
            diff['src_binary'] = 1
        elif st[stat.ST_SIZE] > utils.MAX_FILE_SIZE_FOR_DIFF:
            diff['src_larger'] = utils.MAX_FILE_SIZE_FOR_DIFF
        else:
            src.seek(0)
            diff['after_header'] = source
            diff['after'] = src.read()

        return diff
    
    def _result_key_merge(self, options, results):
        # add keys to file module results to mimic copy
        if 'path' in results.result and 'dest' not in results.result:
            results.result['dest'] = results.result['path']
            del results.result['path']
        return results
