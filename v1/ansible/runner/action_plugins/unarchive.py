# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2013, Dylan Martin <dmartin@seattlecentral.edu>
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

## fixes https://github.com/ansible/ansible/issues/3518
# http://mypy.pythonblogs.com/12_mypy/archive/1253_workaround_for_python_bug_ascii_codec_cant_encode_character_uxa0_in_position_111_ordinal_not_in_range128.html
import sys
reload(sys)
sys.setdefaultencoding("utf8")
import pipes


class ActionModule(object):

    TRANSFERS_FILES = True

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
        dest    = options.get('dest', None)
        copy    = utils.boolean(options.get('copy', 'yes'))
        creates = options.get('creates', None)

        if source is None or dest is None:
            result = dict(failed=True, msg="src (or content) and dest are required")
            return ReturnData(conn=conn, result=result)

        if creates:
            # do not run the command if the line contains creates=filename
            # and the filename already exists. This allows idempotence
            # of command executions.
            module_args_tmp = ""
            complex_args_tmp = dict(path=creates, get_md5=False, get_checksum=False)
            module_return = self.runner._execute_module(conn, tmp, 'stat', module_args_tmp, inject=inject,
                                                        complex_args=complex_args_tmp, delete_remote_tmp=False)
            stat = module_return.result.get('stat', None)
            if stat and stat.get('exists', False):
                return ReturnData(
                    conn=conn,
                    comm_ok=True,
                    result=dict(
                        changed=False,
                        msg=("skipped, since %s exists" % creates)
                    )
                )

        dest = self.runner._remote_expand_user(conn, dest, tmp) # CCTODO: Fix path for Windows hosts.
        source = template.template(self.runner.basedir, os.path.expanduser(source), inject)
        if copy:
            if '_original_file' in inject:
                source = utils.path_dwim_relative(inject['_original_file'], 'files', source, self.runner.basedir)
            else:
                source = utils.path_dwim(self.runner.basedir, source)

        remote_checksum = self.runner._remote_checksum(conn, tmp, dest, inject)
        if remote_checksum == '4':
            result = dict(failed=True, msg="python isn't present on the system.  Unable to compute checksum")
            return ReturnData(conn=conn, result=result)
        if remote_checksum != '3':
            result = dict(failed=True, msg="dest '%s' must be an existing dir" % dest)
            return ReturnData(conn=conn, result=result)

        if copy:
            # transfer the file to a remote tmp location
            tmp_src = tmp + 'source'
            conn.put_file(source, tmp_src)

        # handle diff mode client side
        # handle check mode client side
        # fix file permissions when the copy is done as a different user
        if copy:
            if self.runner.become and self.runner.become_user != 'root':
                if not self.runner.noop_on_check(inject):
                    self.runner._remote_chmod(conn, 'a+r', tmp_src, tmp)
            # Build temporary module_args.
            new_module_args = dict(
                src=tmp_src,
                original_basename=os.path.basename(source),
            )

            # make sure checkmod is passed on correctly
            if self.runner.noop_on_check(inject):
                new_module_args['CHECKMODE'] = True

            module_args = utils.merge_module_args(module_args, new_module_args)
        else:
            module_args = "%s original_basename=%s" % (module_args, pipes.quote(os.path.basename(source)))
            # make sure checkmod is passed on correctly
            if self.runner.noop_on_check(inject):
                module_args += " CHECKMODE=True"
        return self.runner._execute_module(conn, tmp, 'unarchive', module_args, inject=inject, complex_args=complex_args)
