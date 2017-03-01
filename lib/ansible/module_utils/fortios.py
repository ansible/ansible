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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception


#check for pyFG lib
try:
    from pyFG import FortiOS, FortiConfig
    from pyFG.exceptions import CommandExecutionException, FailedCommit
    HAS_PYFG=True
except:
    HAS_PYFG=False

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


fortios_error_codes = {
    '-3':"Object not found",
    '-61':"Command error"
}


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




class AnsibleFortios(object):
    def __init__(self, module):
        if not HAS_PYFG:
            module.fail_json(msg='Could not import the python library pyFG required by this module')

        self.result = {
            'changed': False,
        }
        self.module = module


    def _connect(self):
        host = self.module.params['host']
        username = self.module.params['username']
        password = self.module.params['password']
        timeout = self.module.params['timeout']
        vdom = self.module.params['vdom']

        self.forti_device = FortiOS(host, username=username, password=password, timeout=timeout, vdom=vdom)

        try:
            self.forti_device.open()
        except Exception:
            e = get_exception()
            self.module.fail_json(msg='Error connecting device. %s' % e)


    def load_config(self, path):
        self._connect()
        self.path = path
        #get  config
        try:
            self.forti_device.load_config(path=path)
            self.result['running_config'] = self.forti_device.running_config.to_text()
        except Exception:
            self.forti_device.close()
            e = get_exception()
            self.module.fail_json(msg='Error reading running config. %s' % e)

        #backup if needed
        if self.module.params['backup']:
            backup(self.module, self.result['running_config'])

        self.candidate_config = self.forti_device.candidate_config


    def apply_changes(self):
        change_string = self.forti_device.compare_config()
        if change_string:
            self.result['change_string'] = change_string
            self.result['changed'] = True

        #Commit if not check mode
        if change_string and not self.module.check_mode:
            try:
                self.forti_device.commit()
            except FailedCommit:
                #Something's wrong (rollback is automatic)
                self.forti_device.close()
                e = get_exception()
                error_list = self.get_error_infos(e)
                self.module.fail_json(msg_error_list=error_list, msg="Unable to commit change, check your args, the error was %s" % e.message )

        self.forti_device.close()
        self.module.exit_json(**self.result)


    def del_block(self, block_id):
        self.forti_device.candidate_config[self.path].del_block(block_id)


    def add_block(self, block_id, block):
        self.forti_device.candidate_config[self.path][block_id] = block


    def get_error_infos(self, cli_errors):
        error_list = []
        for errors in cli_errors.args:
            for error in errors:
                error_code = error[0]
                error_string = error[1]
                error_type = fortios_error_codes.get(error_code,"unknown")
                error_list.append(dict(error_code=error_code, error_type=error_type, error_string= error_string))

        return error_list

    def get_empty_configuration_block(self, block_name, block_type):
        return FortiConfig(block_name, block_type)

