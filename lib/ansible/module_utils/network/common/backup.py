# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import os
import time
import glob

from ansible.module_utils._text import to_text
from ansible.module_utils.six.moves.urllib.parse import urlsplit


def get_working_path(module):
    cwd = module._loader.get_basedir()
    if module._task._role is not None:
        cwd = module._task._role._role_path
    return cwd


def write_backup(module, host, contents, encoding='utf-8'):
    cwd = get_working_path(module)

    backup_path = os.path.join(cwd, 'backup')
    if not os.path.exists(backup_path):
        os.mkdir(backup_path)
    for existing_backup in glob.glob('%s/%s_config.*' % (backup_path, host)):
        os.remove(existing_backup)
    tstamp = time.strftime("%Y-%m-%d@%H:%M:%S", time.localtime(time.time()))
    filename = '%s/%s_config.%s' % (backup_path, host, tstamp)
    open(filename, 'w').write(to_text(contents, encoding=encoding))

    return filename


def handle_template(module):
    src = module._task.args.get('src')
    working_path = get_working_path(module)

    if os.path.isabs(src) or urlsplit('src').scheme:
        source = src
    else:
        source = module._loader.path_dwim_relative(working_path, 'templates', src)
        if not source:
            source = module._loader.path_dwim_relative(working_path, src)

    if not os.path.exists(source):
        raise ValueError('path specified in src not found')

    try:
        with open(source, 'r') as f:
            template_data = to_text(f.read())
    except IOError:
        return dict(failed=True, msg='unable to load src file')

    # Create a template search path in the following order:
    # [working_path, self_role_path, dependent_role_paths, dirname(source)]
    searchpath = [working_path]
    if module._task._role is not None:
        searchpath.append(module._task._role._role_path)
        if hasattr(module._task, "_block:"):
            dep_chain = module._task._block.get_dep_chain()
            if dep_chain is not None:
                for role in dep_chain:
                    searchpath.append(role._role_path)
    searchpath.append(os.path.dirname(source))
    module._templar.environment.loader.searchpath = searchpath
    return module._templar.template(template_data)
