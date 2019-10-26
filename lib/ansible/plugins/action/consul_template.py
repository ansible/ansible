# Copyright: (c) 2019, Mikhail Morev <mmorev@live.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import shutil
import stat
import tempfile
import subprocess

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleFileNotFound, AnsibleAction, AnsibleActionFail
from ansible.module_utils._text import to_bytes, to_text, to_native
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.common.process import get_bin_path
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def run(self, tmp=None, task_vars=None):

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect
        self._connection._shell.tmpdir = tempfile.mkdtemp(dir=C.DEFAULT_LOCAL_TMP)

        # assign to local vars for ease of use
        tmpdir = self._connection._shell.tmpdir
        source = self._task.args.get('src', None)
        content = self._task.args.get('content', None)
        dest = self._task.args.get('dest', None)
        consul_addr = self._task.args.get('consul_addr', None)
        consul_token = self._task.args.get('consul_token', None)
        vault_addr = self._task.args.get('vault_addr', None)
        vault_token = self._task.args.get('vault_token', None)
        remote_src = boolean(self._task.args.get('remote_src', False), strict=False)
        mode = self._task.args.get('mode', None)
        if mode == 'preserve':
            self._task.args['mode'] = '0%03o' % stat.S_IMODE(os.stat(source).st_mode)

        # get environment from os and task - task gets precedence
        environment = os.environ.copy()
        task_environment = dict()
        self._compute_environment_string(task_environment)
        environment.update(task_environment)

        try:
            # get main executable
            ctmpl_cmd = [get_bin_path('consul-template', True)]

            # mandatory parameters validation
            if source is None and content is None or dest is None:
                raise AnsibleActionFail("src/content and dest are required")
            elif source is not None and content is not None:
                raise AnsibleActionFail("ambiguous parameter set: src and content are mutually exclusive")
            elif source is not None and remote_src is False:
                try:
                    source = self._find_needle('templates', source)
                except AnsibleError as e:
                    raise AnsibleActionFail(to_text(e))

            # If content is defined make a tmp file and write the content into it.
            if content is not None:
                try:
                    if isinstance(content, (dict, list)):
                        content = json.dumps(content)
                    fd, content_tempfile = tempfile.mkstemp(dir=tmpdir)
                    f = os.fdopen(fd, 'wb')
                    try:
                        f.write(to_bytes(content))
                    except Exception as e:
                        os.remove(content_tempfile)
                    finally:
                        f.close()

                    source_tpl = content_tempfile
                except Exception as e:
                    result['failed'] = True
                    result['msg'] = "could not write content temp file: %s" % to_native(e)

            elif remote_src:
                fetch_file = tempfile.mkstemp(dir=tmpdir)[1]
                fetch_task = self._task.copy()
                fetch_task.args.update(dict(src=source,
                                            dest=fetch_file,
                                            flat=True))
                fetch_action = self._shared_loader_obj.action_loader.get('fetch',
                                                                         task=fetch_task,
                                                                         connection=self._connection,
                                                                         play_context=self._play_context,
                                                                         loader=self._loader,
                                                                         templar=self._templar,
                                                                         shared_loader_obj=self._shared_loader_obj)
                # result.update(fetch_action.run(task_vars=task_vars))
                fetch_result = fetch_action.run(task_vars=task_vars)
                if fetch_result.get('failed'):
                    result['failed'] = fetch_result['failed']
                    result['msg'] = fetch_result['msg']
                    return result
                source_tpl = fetch_file
            else:
                source_tpl = source

            # Get vault decrypted tmp file
            try:
                tmp_source = self._loader.get_real_file(source_tpl)
            except AnsibleFileNotFound as e:
                raise AnsibleActionFail("could not find src=%s, %s" % (source, to_text(e)))

            result_file = os.path.join(tmpdir, os.path.basename(source_tpl))

            # template the source data locally & get ready to transfer
            ctmpl_cmd.append('-once')
            ctmpl_cmd.append('-vault-renew-token=false')
            ctmpl_cmd.append('-vault-retry=false')
            if consul_addr is not None:
                ctmpl_cmd.append('-consul-addr=' + consul_addr)
            if consul_token is not None:
                ctmpl_cmd.append('-consul-token=' + consul_token)
            if vault_addr is not None:
                ctmpl_cmd.append('-vault-addr=' + vault_addr)
            if vault_token is not None:
                ctmpl_cmd.append('-vault-token=' + vault_token)
            ctmpl_cmd.append('-template=' + tmp_source + ':' + result_file)

            p = subprocess.Popen(ctmpl_cmd,
                                 env=environment,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            if p.returncode != 0:
                raise AnsibleError('consul-template raised an error: %s' % (to_text(err)))
            if not os.path.isfile(result_file):
                result['msg'] = "Template rendered to empty file. Skipping"
                result['skipped'] = True
                return result

            self._loader.cleanup_tmp_file(tmp_source)

            # call ansible copy task to do the rest
            try:
                copy_task = self._task.copy()
                for arg in ('content', 'vault_addr', 'vault_token', 'consul_addr', 'consul_token', 'remote_src'):
                    copy_task.args.pop(arg, None)
                copy_task.args.update(dict(src=result_file,
                                           dest=dest))
                copy_action = self._shared_loader_obj.action_loader.get('copy',
                                                                        task=copy_task,
                                                                        connection=self._connection,
                                                                        play_context=self._play_context,
                                                                        loader=self._loader,
                                                                        templar=self._templar,
                                                                        shared_loader_obj=self._shared_loader_obj)
                copy_result = copy_action.run(task_vars=task_vars)
                result.update(copy_result)

                result['src'] = source
                if 'diff' in result and isinstance(result['diff'], list):
                    result['diff'][0]['after_header'] = dest

            finally:
                shutil.rmtree(to_bytes(tmpdir, errors='surrogate_or_strict'))

        except AnsibleAction as e:
            result.update(e.result)
        finally:
            self._remove_tmp_path(self._connection._shell.tmpdir)

        return result
