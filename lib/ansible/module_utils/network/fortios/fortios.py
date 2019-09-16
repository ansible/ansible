# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Benjamin Jolivot <bjolivot@gmail.com>, 2014,
# Miguel Angel Munoz <magonzalez@fortinet.com>, 2019
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
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE
#
import os
import time
import traceback

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback

import json

# BEGIN DEPRECATED

# check for pyFG lib
try:
    from pyFG import FortiOS, FortiConfig
    from pyFG.exceptions import FailedCommit
    HAS_PYFG = True
except ImportError:
    HAS_PYFG = False

fortios_argument_spec = dict(
    file_mode=dict(type='bool', default=False),
    config_file=dict(type='path'),
    host=dict(),
    username=dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    password=dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    timeout=dict(type='int', default=60),
    vdom=dict(type='str'),
    backup=dict(type='bool', default=False),
    backup_path=dict(type='path'),
    backup_filename=dict(type='str'),
)

fortios_required_if = [
    ['file_mode', False, ['host', 'username', 'password']],
    ['file_mode', True, ['config_file']],
    ['backup', True, ['backup_path']],
]

fortios_mutually_exclusive = [
    ['config_file', 'host'],
    ['config_file', 'username'],
    ['config_file', 'password']
]

fortios_error_codes = {
    '-3': "Object not found",
    '-61': "Command error"
}

# END DEPRECATED


class FortiOSHandler(object):

    def __init__(self, conn):
        self._conn = conn

    def cmdb_url(self, path, name, vdom=None, mkey=None):

        url = '/api/v2/cmdb/' + path + '/' + name
        if mkey:
            url = url + '/' + str(mkey)
        if vdom:
            if vdom == "global":
                url += '?global=1'
            else:
                url += '?vdom=' + vdom
        return url

    def mon_url(self, path, name, vdom=None, mkey=None):
        url = '/api/v2/monitor/' + path + '/' + name
        if mkey:
            url = url + '/' + str(mkey)
        if vdom:
            if vdom == "global":
                url += '?global=1'
            else:
                url += '?vdom=' + vdom
        return url

    def schema(self, path, name, vdom=None):
        if vdom is None:
            url = self.cmdb_url(path, name) + "?action=schema"
        else:
            url = self.cmdb_url(path, name, vdom=vdom) + "&action=schema"

        status, result_data = self._conn.send_request(url=url)

        if status == 200:
            if vdom == "global":
                return json.loads(to_text(result_data))[0]['results']
            else:
                return json.loads(to_text(result_data))['results']
        else:
            return json.loads(to_text(result_data))

    def get_mkeyname(self, path, name, vdom=None):
        schema = self.schema(path, name, vdom=vdom)
        try:
            keyname = schema['mkey']
        except KeyError:
            return False
        return keyname

    def get_mkey(self, path, name, data, vdom=None):

        keyname = self.get_mkeyname(path, name, vdom)
        if not keyname:
            return None
        else:
            try:
                mkey = data[keyname]
            except KeyError:
                return None
        return mkey

    def get(self, path, name, vdom=None, mkey=None, parameters=None):
        url = self.cmdb_url(path, name, vdom, mkey=mkey)

        status, result_data = self._conn.send_request(url=url, params=parameters, method='GET')

        return self.formatresponse(result_data, vdom=vdom)

    def monitor(self, path, name, vdom=None, mkey=None, parameters=None):
        url = self.mon_url(path, name, vdom, mkey)

        status, result_data = self._conn.send_request(url=url, params=parameters, method='GET')

        return self.formatresponse(result_data, vdom=vdom)

    def set(self, path, name, data, mkey=None, vdom=None, parameters=None):

        if not mkey:
            mkey = self.get_mkey(path, name, data, vdom=vdom)
        url = self.cmdb_url(path, name, vdom, mkey)

        status, result_data = self._conn.send_request(url=url, params=parameters, data=json.dumps(data), method='PUT')

        if status == 404 or status == 405 or status == 500:
            return self.post(path, name, data, vdom, mkey)
        else:
            return self.formatresponse(result_data, vdom=vdom)

    def post(self, path, name, data, vdom=None,
             mkey=None, parameters=None):

        if mkey:
            mkeyname = self.get_mkeyname(path, name, vdom)
            data[mkeyname] = mkey

        url = self.cmdb_url(path, name, vdom, mkey=None)

        status, result_data = self._conn.send_request(url=url, params=parameters, data=json.dumps(data), method='POST')

        return self.formatresponse(result_data, vdom=vdom)

    def execute(self, path, name, data, vdom=None,
                mkey=None, parameters=None, timeout=300):
        url = self.mon_url(path, name, vdom, mkey=mkey)

        status, result_data = self._conn.send_request(url=url, params=parameters, data=json.dumps(data), method='POST', timeout=timeout)

        return self.formatresponse(result_data, vdom=vdom)

    def delete(self, path, name, vdom=None, mkey=None, parameters=None, data=None):
        if not mkey:
            mkey = self.get_mkey(path, name, data, vdom=vdom)
        url = self.cmdb_url(path, name, vdom, mkey)
        status, result_data = self._conn.send_request(url=url, params=parameters, data=json.dumps(data), method='DELETE')
        return self.formatresponse(result_data, vdom=vdom)

    def formatresponse(self, res, vdom=None):
        if vdom == "global":
            resp = json.loads(to_text(res))[0]
            resp['vdom'] = "global"
        else:
            resp = json.loads(to_text(res))
        return resp

# BEGIN DEPRECATED


def backup(module, running_config):
    backup_path = module.params['backup_path']
    backup_filename = module.params['backup_filename']
    if not os.path.exists(backup_path):
        try:
            os.mkdir(backup_path)
        except Exception:
            module.fail_json(msg="Can't create directory {0} Permission denied ?".format(backup_path))
    tstamp = time.strftime("%Y-%m-%d@%H:%M:%S", time.localtime(time.time()))
    if 0 < len(backup_filename):
        filename = '%s/%s' % (backup_path, backup_filename)
    else:
        filename = '%s/%s_config.%s' % (backup_path, module.params['host'], tstamp)
    try:
        open(filename, 'w').write(running_config)
    except Exception:
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
        if self.module.params['file_mode']:
            self.forti_device = FortiOS('')
        else:
            host = self.module.params['host']
            username = self.module.params['username']
            password = self.module.params['password']
            timeout = self.module.params['timeout']
            vdom = self.module.params['vdom']

            self.forti_device = FortiOS(host, username=username, password=password, timeout=timeout, vdom=vdom)

            try:
                self.forti_device.open()
            except Exception as e:
                self.module.fail_json(msg='Error connecting device. %s' % to_text(e),
                                      exception=traceback.format_exc())

    def load_config(self, path):
        self.path = path
        self._connect()
        # load in file_mode
        if self.module.params['file_mode']:
            try:
                f = open(self.module.params['config_file'], 'r')
                running = f.read()
                f.close()
            except IOError as e:
                self.module.fail_json(msg='Error reading configuration file. %s' % to_text(e),
                                      exception=traceback.format_exc())
            self.forti_device.load_config(config_text=running, path=path)

        else:
            # get  config
            try:
                self.forti_device.load_config(path=path)
            except Exception as e:
                self.forti_device.close()
                self.module.fail_json(msg='Error reading running config. %s' % to_text(e),
                                      exception=traceback.format_exc())

        # set configs in object
        self.result['running_config'] = self.forti_device.running_config.to_text()
        self.candidate_config = self.forti_device.candidate_config

        # backup if needed
        if self.module.params['backup']:
            backup(self.module, self.forti_device.running_config.to_text())

    def apply_changes(self):
        change_string = self.forti_device.compare_config()
        if change_string:
            self.result['change_string'] = change_string
            self.result['changed'] = True

        # Commit if not check mode
        if change_string and not self.module.check_mode:
            if self.module.params['file_mode']:
                try:
                    f = open(self.module.params['config_file'], 'w')
                    f.write(self.candidate_config.to_text())
                    f.close()
                except IOError as e:
                    self.module.fail_json(msg='Error writing configuration file. %s' %
                                          to_text(e), exception=traceback.format_exc())
            else:
                try:
                    self.forti_device.commit()
                except FailedCommit as e:
                    # Something's wrong (rollback is automatic)
                    self.forti_device.close()
                    error_list = self.get_error_infos(e)
                    self.module.fail_json(msg_error_list=error_list, msg="Unable to commit change, check your args, the error was %s" % e.message)

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
                error_type = fortios_error_codes.get(error_code, "unknown")
                error_list.append(dict(error_code=error_code, error_type=error_type, error_string=error_string))

        return error_list

    def get_empty_configuration_block(self, block_name, block_type):
        return FortiConfig(block_name, block_type)

# END DEPRECATED
