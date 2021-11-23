# (c) 2013-2016, Michael DeHaan <michael.dehaan@gmail.com>
#           Stephen Fromm <sfromm@gmail.com>
#           Brian Coca  <briancoca+dev@gmail.com>
#           Toshio Kuratomi  <tkuratomi@ansible.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import codecs
import os
import os.path
import re
import tempfile

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleAction, _AnsibleActionDone, AnsibleActionFail
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase
from ansible.utils.hashing import checksum_s


class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def _assemble_from_fragments(self, src_path, delimiter=None, compiled_regexp=None, ignore_hidden=False, decrypt=True):
        ''' assemble a file from a directory of fragments '''

        tmpfd, temp_path = tempfile.mkstemp(dir=C.DEFAULT_LOCAL_TMP)
        tmp = os.fdopen(tmpfd, 'wb')
        delimit_me = False
        add_newline = False

        for f in (to_text(p, errors='surrogate_or_strict') for p in sorted(os.listdir(src_path))):
            if compiled_regexp and not compiled_regexp.search(f):
                continue
            fragment = u"%s/%s" % (src_path, f)
            if not os.path.isfile(fragment) or (ignore_hidden and os.path.basename(fragment).startswith('.')):
                continue

            with open(self._loader.get_real_file(fragment, decrypt=decrypt), 'rb') as fragment_fh:
                fragment_content = fragment_fh.read()

            # always put a newline between fragments if the previous fragment didn't end with a newline.
            if add_newline:
                tmp.write(b'\n')

            # delimiters should only appear between fragments
            if delimit_me:
                if delimiter:
                    # un-escape anything like newlines
                    delimiter = codecs.escape_decode(delimiter)[0]
                    tmp.write(delimiter)
                    # always make sure there's a newline after the
                    # delimiter, so lines don't run together
                    if delimiter[-1] != b'\n':
                        tmp.write(b'\n')

            tmp.write(fragment_content)
            delimit_me = True
            if fragment_content.endswith(b'\n'):
                add_newline = False
            else:
                add_newline = True

        tmp.close()
        return temp_path

    def run(self, tmp=None, task_vars=None):

        self._supports_check_mode = True

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if task_vars is None:
            task_vars = dict()

        src = self._task.args.get('src', None)
        dest = self._task.args.get('dest', None)
        delimiter = self._task.args.get('delimiter', None)
        remote_src = self._task.args.get('remote_src', 'yes')
        regexp = self._task.args.get('regexp', None)
        follow = self._task.args.get('follow', False)
        ignore_hidden = self._task.args.get('ignore_hidden', False)
        decrypt = self._task.args.pop('decrypt', True)

        try:
            if src is None or dest is None:
                raise AnsibleActionFail("src and dest are required")

            if boolean(remote_src, strict=False):
                # call assemble via ansible.legacy to allow library/ overrides of the module without collection search
                result.update(self._execute_module(module_name='ansible.legacy.assemble', task_vars=task_vars))
                raise _AnsibleActionDone()
            else:
                try:
                    src = self._find_needle('files', src)
                except AnsibleError as e:
                    raise AnsibleActionFail(to_native(e))

            if not os.path.isdir(src):
                raise AnsibleActionFail(u"Source (%s) is not a directory" % src)

            _re = None
            if regexp is not None:
                _re = re.compile(regexp)

            # Does all work assembling the file
            path = self._assemble_from_fragments(src, delimiter, _re, ignore_hidden, decrypt)

            path_checksum = checksum_s(path)
            dest = self._remote_expand_user(dest)
            dest_stat = self._execute_remote_stat(dest, all_vars=task_vars, follow=follow)

            diff = {}

            # setup args for running modules
            new_module_args = self._task.args.copy()

            # clean assemble specific options
            for opt in ['remote_src', 'regexp', 'delimiter', 'ignore_hidden', 'decrypt']:
                if opt in new_module_args:
                    del new_module_args[opt]
            new_module_args['dest'] = dest

            if path_checksum != dest_stat['checksum']:

                if self._play_context.diff:
                    diff = self._get_diff_data(dest, path, task_vars)

                    # _get_diff_data uses the tmp path for 'after_header'
                    # which makes there always appear to be a diff
                    diff['after_header'] = '%s (content)' % dest

                    if not dest_stat['exists']:
                        # Ensure the before_header key is defined for ease of access
                        diff['before_header'] = ''
                    else:
                        diff['before_header'] = diff['before_header'] + ' (content)'

                    if diff['before_header'] == diff['after_header'] and diff['before'] == diff['after']:
                        # Nothing actually changed
                        diff = {}

                if self._play_context.check_mode:
                    # The copy module supports check mode, so just provide the tmp path as the source
                    new_module_args.update(dict(src=path,))
                else:
                    remote_path = self._connection._shell.join_path(self._connection._shell.tmpdir, 'src')
                    xfered = self._transfer_file(path, remote_path)

                    # fix file permissions when the copy is done as a different user
                    self._fixup_perms2((self._connection._shell.tmpdir, remote_path))

                    new_module_args.update(dict(src=xfered,))

                # FIXME: add diff support
                res = self._execute_module(module_name='ansible.legacy.copy', module_args=new_module_args, task_vars=task_vars)

                if self._play_context.diff:
                    res['diff'] = []
                    if diff:
                        res['diff'].append(diff)
                result.update(res)
            else:
                result.update(self._execute_module(module_name='ansible.legacy.file', module_args=new_module_args, task_vars=task_vars))

        except AnsibleAction as e:
            result.update(e.result)
        finally:
            self._remove_tmp_path(self._connection._shell.tmpdir)

        return result
