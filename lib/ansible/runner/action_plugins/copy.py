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


        local_md5 = utils.md5(source)
        if local_md5 is None:
            result=dict(failed=True, msg="could not find src=%s" % source)
            return ReturnData(conn=conn, result=result)

        if dest.endswith("/"):
            base = os.path.basename(source)
            dest = os.path.join(dest, base)

        remote_md5 = self.runner._remote_md5(conn, tmp, dest)
        if remote_md5 == '3':
            # Destination is a directory
            if content is not None:
                os.remove(tmp_content)
                result = dict(failed=True, msg="can not use content with a dir as dest")
                return ReturnData(conn=conn, result=result)
            dest = os.path.join(dest, os.path.basename(source))
            remote_md5 = self.runner._remote_md5(conn, tmp, dest)

        # remote_md5 == '1' would mean that the file does not exist.
        if remote_md5 != '1' and not force:
            return ReturnData(conn=conn, result=dict(changed=False))

        exec_rc = None
        if local_md5 != remote_md5:

            if self.runner.diff and not raw:
                diff = self._get_diff_data(conn, tmp, inject, dest, source)
            else:
                diff = {}

            if self.runner.noop_on_check(inject):
                if content is not None:
                    os.remove(tmp_content)
                return ReturnData(conn=conn, result=dict(changed=True), diff=diff)


            # transfer the file to a remote tmp location
            tmp_src = tmp + 'source'

            if not raw:
                conn.put_file(source, tmp_src)
            else:
                conn.put_file(source, dest)

            if content is not None:
                os.remove(tmp_content)

            # fix file permissions when the copy is done as a different user
            if self.runner.sudo and self.runner.sudo_user != 'root' and not raw:
                self.runner._low_level_exec_command(conn, "chmod a+r %s" % tmp_src, tmp)

            if raw:
                return ReturnData(conn=conn, result=dict(dest=dest, changed=True))

            # run the copy module
            if 'raw' in module_args:
                # don't send down raw=no
                module_args.pop('raw')
            module_args = "%s src=%s original_basename=%s" % (module_args, pipes.quote(tmp_src), pipes.quote(os.path.basename(source)))
            return self.runner._execute_module(conn, tmp, 'copy', module_args, inject=inject, complex_args=complex_args)

        else:
            # no need to transfer the file, already correct md5, but still need to call
            # the file module in case we want to change attributes

            if content is not None:
                os.remove(tmp_content)

            if raw:
                return ReturnData(conn=conn, result=dict(dest=dest, changed=False))

            tmp_src = tmp + os.path.basename(source)
            if 'raw' in module_args:
                # don't send down raw=no
                module_args.pop('raw')
            module_args = "%s src=%s" % (module_args, pipes.quote(tmp_src))
            if self.runner.noop_on_check(inject):
                module_args = "%s CHECKMODE=True" % module_args
            return self.runner._execute_module(conn, tmp, 'file', module_args, inject=inject, complex_args=complex_args)

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
