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
import re
import shlex

import ansible.constants as C
from ansible.utils import template
from ansible import utils
from ansible import errors
from ansible.runner.return_data import ReturnData


class ActionModule(object):
    TRANSFERS_FILES = True

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):
        ''' handler for file transfer operations '''

        if self.runner.noop_on_check(inject):
            # in check mode, always skip this module
            return ReturnData(conn=conn, comm_ok=True,
                              result=dict(skipped=True, msg='check mode not supported for this module'))

        # extract ansible reserved parameters
        # From library/command keep in sync
        creates = None
        removes = None
        r = re.compile(r'(^|\s)(creates|removes)=(?P<quote>[\'"])?(.*?)(?(quote)(?<!\\)(?P=quote))((?<!\\)(?=\s)|$)')
        for m in r.finditer(module_args):
            v = m.group(4).replace("\\", "")
            if m.group(2) == "creates":
                creates = v
            elif m.group(2) == "removes":
                removes = v
        module_args = r.sub("", module_args)

        if creates:
            # do not run the command if the line contains creates=filename
            # and the filename already exists. This allows idempotence
            # of command executions.
            module_args_tmp = "path=%s" % creates
            module_return = self.runner._execute_module(conn, tmp, 'stat', module_args_tmp, inject=inject,
                                                        complex_args=complex_args, persist_files=True)
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
        if removes:
            # do not run the command if the line contains removes=filename
            # and the filename does not exist. This allows idempotence
            # of command executions.
            module_args_tmp = "path=%s" % removes
            module_return = self.runner._execute_module(conn, tmp, 'stat', module_args_tmp, inject=inject,
                                                        complex_args=complex_args, persist_files=True)
            stat = module_return.result.get('stat', None)
            if stat and not stat.get('exists', False):
                return ReturnData(
                    conn=conn,
                    comm_ok=True,
                    result=dict(
                        changed=False,
                        msg=("skipped, since %s does not exist" % removes)
                    )
                )

        # Decode the result of shlex.split() to UTF8 to get around a bug in that's been fixed in Python 2.7 but not Python 2.6.
        # See: http://bugs.python.org/issue6988
        tokens = shlex.split(module_args.encode('utf8'))
        tokens = [s.decode('utf8') for s in tokens]
        # extract source script
        source = tokens[0]

        # FIXME: error handling
        args = " ".join(tokens[1:])
        source = template.template(self.runner.basedir, source, inject)
        if '_original_file' in inject:
            source = utils.path_dwim_relative(inject['_original_file'], 'files', source, self.runner.basedir)
        else:
            source = utils.path_dwim(self.runner.basedir, source)

        # transfer the file to a remote tmp location
        source = source.replace('\x00', '')  # why does this happen here?
        args = args.replace('\x00', '')  # why does this happen here?
        tmp_src = conn.shell.join_path(tmp, os.path.basename(source))
        tmp_src = tmp_src.replace('\x00', '')

        conn.put_file(source, tmp_src)

        sudoable = True
        # set file permissions, more permissive when the copy is done as a different user
        if self.runner.become and self.runner.become_user != 'root':
            chmod_mode = 'a+rx'
            sudoable = False
        else:
            chmod_mode = '+rx'
        self.runner._remote_chmod(conn, chmod_mode, tmp_src, tmp, sudoable=sudoable, become=self.runner.become)

        # add preparation steps to one ssh roundtrip executing the script
        env_string = self.runner._compute_environment_string(conn, inject)
        module_args = ' '.join([env_string, tmp_src, args])

        handler = utils.plugins.action_loader.get('raw', self.runner)
        result = handler.run(conn, tmp, 'raw', module_args, inject)

        # clean up after
        if "tmp" in tmp and not C.DEFAULT_KEEP_REMOTE_FILES:
            self.runner._remove_tmp_path(conn, tmp)

        result.result['changed'] = True

        return result
