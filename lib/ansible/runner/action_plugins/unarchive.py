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

        if source is None or dest is None:
            result = dict(failed=True, msg="src (or content) and dest are required")
            return ReturnData(conn=conn, result=result)

        dest = os.path.expanduser(dest)
        source = template.template(self.runner.basedir, os.path.expanduser(source), inject)
        if copy:
            if '_original_file' in inject:
                source = utils.path_dwim_relative(inject['_original_file'], 'files', source, self.runner.basedir)
            else:
                source = utils.path_dwim(self.runner.basedir, source)

        remote_md5 = self.runner._remote_md5(conn, tmp, dest)
        if remote_md5 != '3':
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
            if self.runner.sudo and self.runner.sudo_user != 'root':
                self.runner._low_level_exec_command(conn, "chmod a+r %s" % tmp_src, tmp)
            module_args = "%s src=%s original_basename=%s" % (module_args, pipes.quote(tmp_src), pipes.quote(os.path.basename(source)))
        else:
            module_args = "%s original_basename=%s" % (module_args, pipes.quote(os.path.basename(source)))
        return self.runner._execute_module(conn, tmp, 'unarchive', module_args, inject=inject, complex_args=complex_args)
