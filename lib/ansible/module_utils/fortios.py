# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Benjamin Jolivot <bjolivot@gmail.com>, 2014
# All rights reserved.
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


fortios_argument_spec = dict(
    host            = dict(required=True ),
    username        = dict(required=True ),
    password        = dict(required=True, type='str', no_log=True ),
    timeout         = dict(type='int', default=60),
    vdom            = dict(type='str', default=None ),
    backup          = dict(type='bool', default=False),
    backup_path     = dict(type='path'),
    backup_filename = dict(type='str'),
)

fortios_required_if = [
    ['backup',   True   , ['backup_path']   ],
]

def backup(module,running_config):
    backup_path = module.params['backup_path']
    if not os.path.exists(backup_path):
        try:
            os.mkdir(backup_path)
        except:
            module.fail_json(msg="Can't create directory {0} Permission denied ?".format(backup_path))
    tstamp = time.strftime("%Y-%m-%d@%H:%M:%S", time.localtime(time.time()))
    filename = '%s/%s_config.%s' % (backup_path, module.params['host'], tstamp)
    try:
        open(filename, 'w').write(running_config)
    except:
        module.fail_json(msg="Can't create backup file {0} Permission denied ?".format(filename))
