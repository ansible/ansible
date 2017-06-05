# (c) 2013, Lukas Lalinsky <lalinsky@gmail.com>
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

import base64
import pipes
from ansible import utils
from ansible.utils import template
from ansible.runner.return_data import ReturnData

class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner

    def _expand_path(self, path, inject, subdir):
        path = template.template(self.runner.basedir, path, inject)
        if '_original_file' in inject:
            return utils.path_dwim_relative(inject['_original_file'], subdir, path, self.runner.basedir)
        else:
            return utils.path_dwim(self.runner.basedir, path)

    def _content_from_file(self, path, inject):
        path = self._expand_path(path, inject, 'files')
        return open(path).read()

    def _content_from_template(self, path, inject):
        path = self._expand_path(path, inject, 'templates')
        return template.template_from_file(self.runner.basedir, path, inject)

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):
        options = {}
        if complex_args:
            options.update(complex_args)
        options.update(utils.parse_kv(module_args))

        user = options.get('user')
        file = options.get('file')
        template = options.get('template')

        if template is None and file is None:
            result = dict(failed=True, msg='at least one of file or template is required')
            return ReturnData(conn=conn, result=result)

        if template is not None and file is not None:
            result = dict(failed=True, msg='only one of file or template can be used')
            return ReturnData(conn=conn, result=result)

        try:
            if template is not None:
                content = self._content_from_template(template, inject)
            else:
                content = self._content_from_file(file, inject)
        except Exception, e:
            result = dict(failed=True, msg=str(e))
            return ReturnData(conn=conn, result=result)

        xfered = self.runner._transfer_str(conn, tmp, 'source', content)

        module_args = "%s file=%s" % (module_args, pipes.quote(xfered))

        if self.runner.diff:
            module_args = "%s return_prev_content=True" % module_args

        if self.runner.check:
            module_args = "%s CHECKMODE=True" % module_args

        result = self.runner._execute_module(conn, tmp, module_name, module_args, inject=inject, complex_args=complex_args)
        if not result.is_successful():
            return result

        if self.runner.diff and 'prev_content' in result.result:
            result.diff = dict(
                before = base64.b64decode(result.result.pop('prev_content')),
                after = content,
            )

        return result

