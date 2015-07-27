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
import pipes
from ansible.utils import template
from ansible import utils
from ansible import errors
from ansible.runner.return_data import ReturnData
import base64

class ActionModule(object):

    TRANSFERS_FILES = True

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):
        ''' handler for template operations '''

        if not self.runner.is_playbook:
            raise errors.AnsibleError("in current versions of ansible, templates are only usable in playbooks")

        # load up options
        options  = {}
        if complex_args:
            options.update(complex_args)
        options.update(utils.parse_kv(module_args))

        source   = options.get('src', None)
        dest     = options.get('dest', None)

        if (source is None and 'first_available_file' not in inject) or dest is None:
            result = dict(failed=True, msg="src and dest are required")
            return ReturnData(conn=conn, comm_ok=False, result=result)

        # if we have first_available_file in our vars
        # look up the files and use the first one we find as src

        if 'first_available_file' in inject:
            found = False
            for fn in self.runner.module_vars.get('first_available_file'):
                fn_orig = fn
                fnt = template.template(self.runner.basedir, fn, inject)
                fnd = utils.path_dwim(self.runner.basedir, fnt)
                if not os.path.exists(fnd) and '_original_file' in inject:
                    fnd = utils.path_dwim_relative(inject['_original_file'], 'templates', fnt, self.runner.basedir, check=False)
                if os.path.exists(fnd):
                    source = fnd
                    found = True
                    break
            if not found:
                result = dict(failed=True, msg="could not find src in first_available_file list")
                return ReturnData(conn=conn, comm_ok=False, result=result)
        else:
            source = template.template(self.runner.basedir, source, inject)

            if '_original_file' in inject:
                source = utils.path_dwim_relative(inject['_original_file'], 'templates', source, self.runner.basedir)
            else:
                source = utils.path_dwim(self.runner.basedir, source)

        if conn.shell.path_has_trailing_slash(dest):
            base = os.path.basename(source)
            dest = conn.shell.join_path(dest, base)

        # template the source data locally & get ready to transfer
        try:
            resultant = template.template_from_file(self.runner.basedir, source, inject, vault_password=self.runner.vault_pass)
        except Exception, e:
            result = dict(failed=True, msg=type(e).__name__ + ": " + str(e))
            return ReturnData(conn=conn, comm_ok=False, result=result)

        local_checksum = utils.checksum_s(resultant)
        remote_checksum = self.runner._remote_checksum(conn, tmp, dest, inject)

        if local_checksum != remote_checksum:

            # template is different from the remote value

            # if showing diffs, we need to get the remote value
            dest_contents = ''

            if self.runner.diff:
                # using persist_files to keep the temp directory around to avoid needing to grab another
                dest_result = self.runner._execute_module(conn, tmp, 'slurp', "path=%s" % dest, inject=inject, persist_files=True)
                if 'content' in dest_result.result:
                    dest_contents = dest_result.result['content']
                    if dest_result.result['encoding'] == 'base64':
                        dest_contents = base64.b64decode(dest_contents)
                    else:
                        raise Exception("unknown encoding, failed: %s" % dest_result.result)

            xfered = self.runner._transfer_str(conn, tmp, 'source', resultant)

            # fix file permissions when the copy is done as a different user
            if self.runner.become and self.runner.become_user != 'root':
                self.runner._remote_chmod(conn, 'a+r', xfered, tmp)

            # run the copy module
            new_module_args = dict(
               src=xfered,
               dest=dest,
               original_basename=os.path.basename(source),
               follow=True,
            )
            module_args_tmp = utils.merge_module_args(module_args, new_module_args)

            if self.runner.noop_on_check(inject):
                return ReturnData(conn=conn, comm_ok=True, result=dict(changed=True), diff=dict(before_header=dest, after_header=source, before=dest_contents, after=resultant))
            else:
                res = self.runner._execute_module(conn, tmp, 'win_copy', module_args_tmp, inject=inject, complex_args=complex_args)
                if res.result.get('changed', False):
                    res.diff = dict(before=dest_contents, after=resultant)
                return res
        else:
            # when running the file module based on the template data, we do
            # not want the source filename (the name of the template) to be used,
            # since this would mess up links, so we clear the src param and tell
            # the module to follow links
            new_module_args = dict(
                src=None,
                follow=True,
            )
            # be sure to inject the check mode param into the module args and
            # rely on the file module to report its changed status
            if self.runner.noop_on_check(inject):
                new_module_args['CHECKMODE'] = True
            module_args = utils.merge_module_args(module_args, new_module_args)
            return self.runner._execute_module(conn, tmp, 'win_file', module_args, inject=inject, complex_args=complex_args)

