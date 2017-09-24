# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Benjamin Jolivot <bjolivot@gmail.com>, 2014
# Copyright (c) API class, Will Wagner <willwagner602@gmail.com> and Eugene Opredelennov <eoprede@gmail.com>, 2017
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
import traceback
import json
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule, _load_params
from ansible.module_utils._text import to_native

# check for pyFG lib
try:
    from pyFG import FortiOS, FortiConfig
    from pyFG.exceptions import FailedCommit
    HAS_PYFG = True
except ImportError:
    HAS_PYFG = False

try:
    import requests
    from requests import ConnectionError

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

fortios_argument_spec = dict(
    file_mode=dict(type='bool', default=False),
    config_file=dict(type='path'),
    host=dict(),
    username=dict(),
    password=dict(type='str', no_log=True),
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


def backup(module, running_config):
    backup_path = module.params['backup_path']
    backup_filename = module.params['backup_filename']
    if not os.path.exists(backup_path):
        try:
            os.mkdir(backup_path)
        except:
            module.fail_json(
                msg="Can't create directory {0} Permission denied ?".format(backup_path))
    tstamp = time.strftime("%Y-%m-%d@%H:%M:%S", time.localtime(time.time()))
    if 0 < len(backup_filename):
        filename = '%s/%s' % (backup_path, backup_filename)
    else:
        filename = '%s/%s_config.%s' % (backup_path,
                                        module.params['host'], tstamp)
    try:
        open(filename, 'w').write(running_config)
    except:
        module.fail_json(
            msg="Can't create backup file {0} Permission denied ?".format(filename))


class AnsibleFortios(object):

    def __init__(self, module):
        if not HAS_PYFG:
            module.fail_json(
                msg='Could not import the python library pyFG required by this module')

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

            self.forti_device = FortiOS(
                host, username=username, password=password, timeout=timeout, vdom=vdom)

            try:
                self.forti_device.open()
            except Exception as e:
                self.module.fail_json(msg='Error connecting device. %s' % to_native(e),
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
                self.module.fail_json(msg='Error reading configuration file. %s' % to_native(e),
                                      exception=traceback.format_exc())
            self.forti_device.load_config(config_text=running, path=path)

        else:
            # get  config
            try:
                self.forti_device.load_config(path=path)
            except Exception as e:
                self.forti_device.close()
                self.module.fail_json(msg='Error reading running config. %s' % to_native(e),
                                      exception=traceback.format_exc())

        # set configs in object
        self.result[
            'running_config'] = self.forti_device.running_config.to_text()
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
                                          to_native(e), exception=traceback.format_exc())
            else:
                try:
                    self.forti_device.commit()
                except FailedCommit as e:
                    # Something's wrong (rollback is automatic)
                    self.forti_device.close()
                    error_list = self.get_error_infos(e)
                    self.module.fail_json(
                        msg_error_list=error_list, msg="Unable to commit change, check your args, the error was %s" % e.message)

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
                error_list.append(
                    dict(error_code=error_code, error_type=error_type, error_string=error_string))

        return error_list

    def get_empty_configuration_block(self, block_name, block_type):
        return FortiConfig(block_name, block_type)


fortios_api_argument_spec = dict(
    conn_params=dict(
        params=dict(
            fortigate_ip=dict(required=True),
            fortigate_username=dict(type='str', required=True),
            fortigate_password=dict(type='str', required=True, no_log=True),
            port=dict(type='int'),
            disable_warnings=dict(type='bool', default=False),
            ssh_keyfile=dict(type='path'),
            verify=dict(type='bool', default=True),
        ), type='dict'),
    vdom=dict(type='str', default="root"),
    print_current_config=dict(type='bool'),
    permanent_objects=dict(type='list'),
    ignore_objects=dict(type='list'),
    default_ignore_params=dict(type='list'),
    endpoint_information=dict(type='dict')
)


def connection_handler(func):
    def func_wrapper(*args, **kwargs):
        api = args[0]
        if func.__name__ != "_login":
            try:
                return func(*args, **kwargs)
            except ConnectionError:
                try:
                    api.fail("Connection to API endpoint %s failed with status %s" % (
                        api._endpoint, api.response.status_code))
                except AttributeError:
                    api.fail(
                        "Connection to API endpoint %s failed with no response." % api._endpoint)
        else:
            try:
                return func(*args, **kwargs)
            except ConnectionError as e:
                try:
                    api.fail("Failed to login to endpoint %s with status %s" % (
                        api._endpoint, api.response.status_code))
                except AttributeError:
                    api._module = AnsibleModule(
                        {}, bypass_checks=True, check_invalid_arguments=False)
                    api.fail("Failed to login to endpoint: %s" % e)

    return func_wrapper


def return_handler(func):
    def return_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, TypeError) as e:
            api = args[0]
            failure_msg = "Empty response received from endpoint %s for API.%s"
            path = args[1]
            api.fail(failure_msg % (path, func.__name__))

    return return_wrapper


class API(object):

    def __init__(self, api_info):

        if not HAS_REQUESTS:
            self.fail(
                'Could not import the python library requests required by this module.')

        self._fortigate_original_config = None
        self._fortigate_current_config = None

        self._params = _load_params()
        self._vdom = self._params.get('vdom', "root")

        self._arg_spec_filename = "FortiosAPIArgSpecs.json"

        self._api_info = api_info
        if api_info.get('from_configs') is True:
            self._api_info = self._params['endpoint_information']

        self._match_ignore_params = self._api_info.get(
            'match_ignore_params', [])
        if self._match_ignore_params:
            self._match_ignore_params.append('name')

        if isinstance(self._api_info["endpoint"], list):
            self._endpoint = '/'.join(self._api_info["endpoint"])
        else:
            self._endpoint = self._api_info["endpoint"]

        if self._params['conn_params'].get('disable_warnings', False):
            requests.packages.urllib3.disable_warnings()
        self._verify = self._params['conn_params'].get('verify', True)
        self._secure = self._params['conn_params'].get('secure', True)
        self.proxies = self._params['conn_params'].get('proxies')

        self._ip = self._build_target_ip()
        response = self._login()
        self.cookies = response.cookies
        self.header = self._set_csrf_header()

        if not response.cookies:
            self.fail(
                "Authentication failed. Authentication attempts likely blocked temporarily.")
        if "just_logged_in" in response.cookies:
            self.fail(
                "Authentication with FortiOS device failed. Check your username/password.")

        self._minimum_object_params = self._params.get('default_object', [])
        self._default_object_configuration = self._get_default_object()
        self._object_identifier = self._api_info.get('object_identifier')
        self._permanent_object_ids = self._get_permanent_object_identifiers()
        self._ignore_object_ids = self._get_ignore_object_identifiers()

        self.http_status_codes = {
            200: "Request Successful.",
            400: "Request cannot be processed by API.",
            401: "Login unsuccessful.",
            403: "Account doesn't have access permissions.",
            404: "Unable to find specified resource.",
            405: "HTTP method not allowed for this resource.",
            413: "Request can't be processed because entity is too large.",
            424: "Failed dependency - one of: duplicate resource, missing required parameter, "
                 "missing required attribute, or invalid attribute value.",
            500: "Internal server error.",
            501: "Not Implemented. Check that your endpoint is correct."
        }

        self._object_map = []
        self._used_object_ids = []
        self._existing_object_ids = []
        self._object_ids_to_update = []
        self._permanent_object_ids_to_reset = []

        self._list_identifier = self._api_info['list_identifier']
        self._argument_spec = {self._list_identifier: dict(
            type='list', options=self._get_argument_spec())}
        self._argument_spec.update(fortios_api_argument_spec)

        self._module = AnsibleModule(self._argument_spec, supports_check_mode=True)
        self._update_config = self._module.params.get(self._list_identifier) or []
        self._print_current_config = self._module.params.get('print_current_config')
        self._check_mode = self._module.check_mode or self._print_current_config

    def apply_configuration_to_endpoint(self):
        self._execute_config_changes()
        if not self._check_mode:
            message, changed, failed = self._process_response()
        else:
            message = "Check Mode"
            changed = not self._configurations_match(
                self._fortigate_original_config, self._update_config)
            failed = False

        self._module.exit_json(msg=message, changed=changed, failed=failed,
                               existing=self._fortigate_original_config, proposed=self._update_config, end_state=self._fortigate_current_config)

    def _execute_config_changes(self):
        self._get_current_configuration()
        if isinstance(self._fortigate_current_config, list):
            self._delete_unused_objects()
            self._update_objects()
            self._create_new_objects()
        else:
            self._update_single_object_endpoint()

    def _get_current_configuration(self):
        try:
            self._fortigate_current_config = self._show(self._endpoint)[
                'results']
        except KeyError:
            self.fail("Failed to find any configuration at %s" %
                      self._endpoint)

        if self._fortigate_original_config is None:
            self._fortigate_original_config = deepcopy(self._fortigate_current_config)
            if self._print_current_config:
                file_name = self._endpoint.replace('/', '-') + '-CurrentConfig.json'
                json.dump({"current": self._fortigate_current_config}, open(file_name, 'w+'), indent=4, sort_keys=True)

        if isinstance(self._fortigate_current_config, list):
            try:
                self._used_object_ids = [o[self._object_identifier] for o in self._update_config]
                self._existing_object_ids = [o[self._object_identifier] for o in self._fortigate_current_config]
            except KeyError:
                self.fail("No or incorrect object identifier specified. List endpoints require an object identifier, typically name or id.")

    def _delete_unused_objects(self):
        if not self._update_config and not self._check_mode:
            self._delete(self._endpoint)
            self._get_current_configuration()

        unused_objects = [identifier for identifier in self._existing_object_ids
                          if identifier not in self._used_object_ids and
                          identifier not in self._permanent_object_ids and
                          identifier not in self._ignore_object_ids]

        failures = {}
        for object_identifier in unused_objects:
            if not self._check_mode:
                response = self._remove(
                    '/'.join([self._endpoint, str(object_identifier)]))
                if response['http_status'] == 200:
                    self._remove_object_from_current_config(object_identifier)
                else:
                    failures[object_identifier] = self.http_status_codes[
                        response['http_status']]
            else:
                self._remove_object_from_current_config(object_identifier)

        if failures:
            self.fail("Failed to delete objects:\n ", msg_args=failures)

    def _remove_object_from_current_config(self, object_identifier):
        for i, forti_object in enumerate(self._fortigate_current_config):
            if forti_object[self._object_identifier] == object_identifier:
                del self._fortigate_current_config[i]
                return

    def _update_objects(self):
        matching_objects = [o[self._object_identifier] for o in self._update_config if o[self._object_identifier] in self._existing_object_ids and
                            not self._diff_unknown(self._get_current_object(o), o)]
        self._object_ids_to_update = [o[self._object_identifier] for o in self._update_config if o[self._object_identifier] in self._existing_object_ids and
                                      o[self._object_identifier] not in matching_objects]
        self._permanent_object_ids_to_reset = [obj_id for obj_id in self._permanent_object_ids if obj_id not in self._object_ids_to_update and
                                               obj_id not in matching_objects]

        failures = {}
        self._update_temporary_and_permanent_objects(failures)
        self._reset_permanent_objects(failures)
        if failures:
            failures_string = ""
            for k, v in failures.items():
                failures_string += ' '.join(['#' + str(k), v, '\n'])
            self.fail("Failed to update objects:\n " + failures_string)

    def _update_temporary_and_permanent_objects(self, failures):
        update_objects = [o for o in self._update_config if o[
            self._object_identifier] in self._object_ids_to_update]
        for forti_object in update_objects:
            if not self._check_mode:
                response = self._edit(
                    self._endpoint + "/%s" % str(forti_object[self._object_identifier]), data=forti_object)
                if response['http_status'] != 200:
                    failures[forti_object[self._object_identifier]
                             ] = self.http_status_codes[response['http_status']]

    def _reset_permanent_objects(self, failures):
        for identifier in self._permanent_object_ids_to_reset:
            response_data = deepcopy(self._default_object_configuration)
            response_data[self._object_identifier] = identifier
            if not self._check_mode:
                response = self._edit(self._endpoint + "/%s" %
                                      str(identifier), data=response_data)
                if response['http_status'] != 200:
                    failures[identifier] = self.http_status_codes[
                        response['http_status']]

    def _get_current_object(self, forti_object):
        for obj in self._fortigate_current_config:
            if obj[self._object_identifier] == forti_object[self._object_identifier]:
                return obj
        return None

    def _create_new_objects(self):
        if not self._update_config:
            return
        existing_object_ids = [o[self._object_identifier]
                               for o in self._fortigate_current_config]
        new_objects = [o for o in self._update_config if o[self._object_identifier] not in existing_object_ids and
                       o[self._object_identifier] not in self._permanent_object_ids]
        failures = {}
        for forti_object in new_objects:
            if not self._check_mode:
                response = self._create(self._endpoint, data=forti_object)
                if response['http_status'] != 200:
                    failures[forti_object[self._object_identifier]
                             ] = self.http_status_codes[response['http_status']]
        if failures:
            self.fail("Failed to create objects:\n ", msg_args=failures)

    def _update_single_object_endpoint(self):

        if self._update_config and isinstance(self._update_config, list):
            self._update_config = self._update_config[0]
        else:
            self._update_config = self._default_object_configuration

        if not self._check_mode:
            self._edit(self._endpoint, data=self._update_config)

    def __enter__(self):
        return self

    def __del__(self):
        try:
            self._logout()
        except AttributeError:
            pass

    def __exit__(self, *args):
        pass

    @connection_handler
    def _login(self):
        data = {'username': self._params['conn_params']['fortigate_username'],
                'secretkey': self._params['conn_params']['fortigate_password']}
        return requests.post(self._ip + '/logincheck', data=data, verify=self._verify, proxies=self.proxies)

    @connection_handler
    def _logout(self):
        requests.post(self._ip + '/logout', cookies=self.cookies,
                      verify=self._verify, proxies=self.proxies)

    @connection_handler
    def _get(self, path, api='v2', params=None):
        if isinstance(path, list):
            path = '/'.join(path) + '/'
        return requests.get(self._ip + '/api/' + api + '/' + path, cookies=self.cookies, verify=self._verify,
                            proxies=self.proxies, params=params)

    @connection_handler
    def _put(self, path, api='v2', params=None, data=None):
        if isinstance(path, list):
            path = '/'.join(path) + '/'
        return requests.put(self._ip + '/api/' + api + '/' + path, headers=self.header,
                            cookies=self.cookies, verify=self._verify, proxies=self.proxies, params=params,
                            json={'json': data})

    @connection_handler
    def _post(self, path, api='v2', params=None, data=None):
        if isinstance(path, list):
            path = '/'.join(path) + '/'
        return requests.post(self._ip + '/api/' + api + '/' + path, headers=self.header, cookies=self.cookies,
                             verify=self._verify, proxies=self.proxies, params=params, json={'json': data})

    @connection_handler
    def _delete(self, path, api='v2', params=None, data=None):
        if isinstance(path, list):
            path = '/'.join(path) + '/'
        return requests.delete(self._ip + '/api/' + api + '/' + path, headers=self.header,
                               cookies=self.cookies, verify=self._verify, proxies=self.proxies, params=params,
                               json={'json': data})

    @return_handler
    def _show(self, path, api='v2', params=None):
        return json.loads(self._get(path, api=api, params=self._build_params(params)).content)

    @return_handler
    def _edit(self, path, api='v2', params=None, data=None):
        return json.loads(self._put(path, api=api, params=self._build_params(params), data=data).content)

    @return_handler
    def _create(self, path, api='v2', params=None, data=None):
        return json.loads(self._post(path, api=api, params=self._build_params(params), data=data).content)

    @return_handler
    def _remove(self, path, api='v2', params=None, data=None):
        return json.loads(self._delete(path, api=api, params=self._build_params(params), data=data).content)

    def _build_params(self, new_params):
        params = {}
        if self._vdom:
            params['vdom'] = self._vdom
        if new_params:
            params.update(new_params)

        if params:
            return params
        else:
            return None

    def _get_local_spec(self):
        try:
            with open(self._arg_spec_filename, "r+") as f:
                local_spec = json.load(f)
        except IOError:
            local_spec = None
        return local_spec

    def _write_local_spec(self, spec):
        with open(self._arg_spec_filename, "w+") as f:
            json.dump(spec, f, indent=4, sort_keys=True)

    def _get_permanent_object_identifiers(self):
        perm_objs_from_module = self._api_info.get("permanent_objects", [])
        perm_objs_from_config = self._params.get("permanent_objects", [])
        if perm_objs_from_module is None:
            perm_objs_from_module = []
        if perm_objs_from_config is None:
            perm_objs_from_config = []
        return perm_objs_from_config + perm_objs_from_module

    def _get_ignore_object_identifiers(self):
        perm_objs_from_module = self._api_info.get("ignore_objects", [])
        perm_objs_from_config = self._params.get("ignore_objects", [])
        if perm_objs_from_module is None:
            perm_objs_from_module = []
        if perm_objs_from_config is None:
            perm_objs_from_config = []
        return perm_objs_from_config + perm_objs_from_module

    def _get_argument_spec(self):
        local_spec = self._get_local_spec()
        if local_spec is None:
            local_spec = {}

        if self._endpoint not in local_spec or "arg_spec" not in local_spec[self._endpoint]:
            try:
                arg_spec = self._process_schema(self._show(
                    self._endpoint + "?action=schema")['results'])
            except KeyError as e:
                self.fail("""Failed to identify argument for spec: %s
                             Probably need to update keys in convert_type_str.""" % e)

            if arg_spec:
                endpoint_spec = local_spec.get(self._endpoint)
                if endpoint_spec is None:
                    local_spec[self._endpoint] = {}
                try:
                    local_spec[self._endpoint]["arg_spec"] = arg_spec
                except KeyError:
                    local_spec[self._endpoint] = {"arg_spec": arg_spec}
                self._write_local_spec(local_spec)

            else:
                self.fail("Failed to retrieve argument spec at %s" %
                          self._endpoint)
        else:
            arg_spec = local_spec[self._endpoint]['arg_spec']

        return arg_spec

    def _process_schema(self, schema):
        arg_spec = {}

        avoid_keys = [
            # originally found in interface
            'name', 'status', 'priority', 'prefix', 'autonomous-flag', 'onlink-flag',
            'gwdetect', 'detectprotocol', 'ip', 'detectserver', 'allowaccess', 'ping-serv-status', 'ha-priority',
            # from admin
            'id', 'vdom',
            # from global
            'time',
        ]

        for key, val in schema['children'].items():
            if key not in avoid_keys or (key not in arg_spec and key in avoid_keys):
                characteristics = {}

                if key in arg_spec:
                    raise KeyError(
                        "Found key %s already existing in arg_spec." % key)

                if 'children' in val:
                    characteristics['options'] = self._process_schema(val)
                if val['category'] == 'unitary':
                    if 'mkey_type' in val:
                        characteristics['type'] = self.convert_type_str(
                            str(val['mkey_type']))
                    elif 'type' in val:
                        characteristics['type'] = self.convert_type_str(
                            str(val['type']))
                    else:
                        self.fail("Type not found for key %s" % key)
                elif val['category'] in ["table", "complex", ]:
                    characteristics['type'] = self.convert_type_str(
                        val['category'])
                if 'options' in val:
                    characteristics['options'] = [
                        str(opt['name']) for opt in val['options']]

                arg_spec[key] = characteristics

        return arg_spec

    def convert_type_str(self, type_str):
        types = {
            'integer': 'int',
            'ipv4-address': 'str',
            'ipv4-address-any': 'str',
            'ipv4-classnet': 'str',
            'ipv4-classnet-any': 'str',
            'ipv4-classnet-host': 'str',
            'ipv6-network': 'str',
            'ipv6-prefix': 'str',
            'ipv6-address': 'str',
            'mac-address': 'str',
            'password': 'str',
            'password-2': 'str',
            'string': 'str',
            'user': 'str',
            'var-string': 'str',
            'list': 'list',
            'option': 'str',
            'datetime': 'str',
            'uuid': 'str',
            'complex': 'dict',
            'table': 'list',
            'time': 'str',
            'ipv4-netmask': 'str'
        }

        try:
            return types[type_str]
        except KeyError:
            self.fail("Couldn't find type with key %s" % type_str)

    def _get_default_object(self):
        local_specification = self._get_local_spec()
        if local_specification is None:
            local_specification = {}

        if self._endpoint not in local_specification or "default_object" not in local_specification[self._endpoint]:
            try:
                default_object = self._show(
                    self._endpoint + "?action=default")['results']
            except KeyError:
                self.fail("Invalid endpoint %s specified" % self._endpoint)

            if default_object:
                try:
                    local_specification[self._endpoint][
                        'default_object'] = default_object
                except KeyError:
                    local_specification[self._endpoint] = {
                        'default_object': default_object}

                self._write_local_spec(local_specification)
            else:
                self.fail("Failed to retrieve default object at %s" %
                          self._endpoint)
        else:
            default_object = local_specification[
                self._endpoint]['default_object']

        for k in self._api_info.get('default_ignore_params', []):
            if k in default_object:
                del default_object[k]

        return default_object

    def _set_csrf_header(self):
        for cookie in self.cookies:
            if cookie.name == "ccsrftoken":
                csrftoken = cookie.value[1:-1]
                return {"X-CSRFTOKEN": csrftoken}

    def _build_target_ip(self):
        if self._secure:
            port = self._params['conn_params'].get('port', 443)
            string = 'https://'
        else:
            port = self._params['conn_params'].get('port', 80)
            string = 'http://'
        return "%s%s:%i" % (string, self._params['conn_params']['fortigate_ip'], port)

    def _process_response(self):
        success_msg = "Configuration updated."
        not_applied_msg = """Configuration update could not be applied, but the FortiOS API generated no errors.
                             This is generally the result of attempting to make changes that cannot affect the current configuration."""
        no_change_needed_msg = "Configuration already correct, no changes needed."
        default_failed_msg = "Default configuration applied but not currently matched by the device."
        rollback_msg = "Update failed, successfully rolled back to original configuration."
        intermediate_msg = "Configuration update failed and rollback failed, configuration appears to be in a partially applied state."

        self._get_current_configuration()
        matches_original_config, matches_update_config = self._original_or_update_match_current_configuration()

        default_applied = not self._update_config
        if default_applied and not matches_update_config:
            message = default_failed_msg
            matches_update_config = True
        elif matches_original_config and matches_update_config:
            message = no_change_needed_msg
        elif not matches_original_config and matches_update_config:
            message = success_msg
        elif matches_original_config and not matches_update_config:
            message = not_applied_msg
        # not matches_original_config and not matches_update_config
        else:
            self._rollback_config()
            matches_original_config, matches_update_config = self._original_or_update_match_current_configuration()
            if matches_original_config:
                self.fail(rollback_msg)
            else:
                self.fail(intermediate_msg)

        return message, not matches_original_config, not matches_update_config

    def _original_or_update_match_current_configuration(self):
        if isinstance(self._fortigate_current_config, list):
            if len(self._fortigate_current_config) > len(self._fortigate_original_config):
                matches_original_config = self._configurations_match(
                    self._fortigate_original_config, self._fortigate_current_config)
            else:
                matches_original_config = self._configurations_match(
                    self._fortigate_current_config, self._fortigate_original_config)
            matches_update_config = self._configurations_match()
        else:
            matches_original_config = self._configurations_match(
                self._fortigate_current_config, self._fortigate_original_config)
            if isinstance(self._fortigate_current_config, dict) and self._update_config:
                matches_update_config = self._dictionaries_match(
                    self._fortigate_current_config, self._update_config)
            elif isinstance(self._fortigate_current_config, dict) and not self._update_config:
                matches_update_config = self._dictionaries_match(
                    self._fortigate_current_config, self._default_object_configuration)
        return matches_original_config, matches_update_config

    def _rollback_config(self):
        temp = deepcopy(self._update_config)
        self._update_config = self._fortigate_original_config
        self._execute_config_changes()
        self._update_config = temp

    def fail(self, msg, msg_args=None):
        try:
            self._logout()
        except:
            pass  # I don't really care if logout failed at this point
        if msg_args is not None:
            for k, v in msg_args.items():
                msg += ', '.join(['#' + str(k), v, '\n'])
        try:
            self._module.fail_json(msg=msg, existing=self._fortigate_original_config,
                                   proposed=self._update_config, end_state=self._fortigate_current_config)
        except AttributeError:
            local_module = AnsibleModule(
                {}, bypass_checks=True, check_invalid_arguments=False, supports_check_mode=True)
            local_module.fail_json(msg=msg, existing=self._fortigate_original_config,
                                   proposed='NA', end_state=self._fortigate_current_config)

    def _configurations_match(self, current_config=None, update_config=None):
        if current_config is None and update_config is None:
            current_config = self._fortigate_current_config
            update_config = self._update_config
        current_config, update_config, existing_objects_only_in_update = self._setup_configs_for_diff(
            current_config, update_config)

        if existing_objects_only_in_update:
            return False

        if isinstance(update_config, dict):
            if not self._dictionaries_match(current_config, update_config):
                return False

        elif isinstance(update_config, list):
            if not self._lists_match(current_config, update_config):
                return False

        return True

    def _setup_configs_for_diff(self, current_config, update_config):
        if isinstance(current_config, dict):
            objects_only_in_update_config = {}
        else:
            update_object_ids = [o[self._object_identifier]
                                 for o in update_config]
            check_current_matches = [o for o in current_config if o[
                self._object_identifier] in update_object_ids]
            current_match_ids = [o[self._object_identifier]
                                 for o in check_current_matches]
            objects_only_in_update_config = [o for o in update_config if o[self._object_identifier] not in current_match_ids and
                                             o[self._object_identifier] not in self._permanent_object_ids]
            if update_config:
                current_config = [self._get_object_from_list_by_id(
                    current_config, obj_id) for obj_id in update_object_ids]

        return current_config, update_config, objects_only_in_update_config

    def _unknown_types_match(self, current_config, update_config):
        # the _match functions determine whether every single key and value in
        # a given pair of objects match recursively.
        if current_config is None:
            return False

        if isinstance(update_config, dict):
            if not self._dictionaries_match(current_config, update_config):
                return False
        elif isinstance(update_config, list):
            if not self._lists_match(current_config, update_config):
                return False
        else:
            if current_config != update_config:
                return False

        return True

    def _dictionaries_match(self, current_config, update_config):
        for key, val in update_config.items():
            current_val = current_config.get(key)

            if isinstance(val, dict):
                if not self._dictionaries_match(current_val, val):
                    return False

            elif isinstance(val, list):
                if not self._lists_match(current_val, val):
                    return False

            elif val != current_val and key not in self._match_ignore_params:
                return False

        return True

    def _lists_match(self, current_config, update_config):
        if not isinstance(current_config, list) or len(update_config) != len(current_config) or current_config is None:
            return False

        if current_config == update_config:
            return True

        for i, val in enumerate(update_config):
            if val not in current_config and not self._unknown_types_match(current_config[i], val):
                return False

        return True

    def _get_object_from_list_by_id(self, objects, obj_id):
        for i in objects:
            if i[self._object_identifier] == obj_id:
                return i
        return None

    def _diff_configs(self, current=None, update=None):
        # the _diff functions determine whether the given "current" object has
        # all matching keys/values to the given "update" object
        if current is None and update is None:
            current = self._fortigate_current_config
            update = self._update_config

        if isinstance(current, list):
            update_ids = [o[self._object_identifier] for o in update]
            needed_objects = [o for o in current if o[
                self._object_identifier] in update_ids]
            update = sorted(update, key=lambda k: k[self._object_identifier])
            current = sorted(needed_objects, key=lambda k: k[
                             self._object_identifier])
            diff = []
            for i, update_val in enumerate(update):
                try:
                    sub_diff = self._diff_unknown(current[i], update_val)
                except IndexError:
                    sub_diff = None
                if sub_diff and any([v for k, v in sub_diff.items()]):
                    sub_diff[self._object_identifier] = update_val[
                        self._object_identifier]
                    diff.append(sub_diff)
                elif sub_diff in ([], {}):
                    diff.append(sub_diff)
        elif isinstance(current, dict):
            diff = self._diff_dicts(current, update)
        else:
            raise TypeError("Invalid type to diff: %s" % type(current))

        if diff and not any(diff):
            diff = None
        return diff

    def _diff_dicts(self, current, update):
        diff = {}
        for key, update_val in update.items():
            if key in current:
                try:
                    current_val = current[key]
                except KeyError:
                    self.fail('Could not find key %s' % str(key))
                sub_val = self._diff_unknown(current_val, update_val)
                if sub_val is not False:
                    diff[key] = sub_val
            elif key not in self._match_ignore_params:
                diff[key] = update_val
        if not diff:
            return None
        return diff

    def _diff_lists(self, current, update):
        if current is None or len(current) != len(update):
            return update

        diff = []
        for i, update_val in enumerate(update):
            current_val = current[i]
            diff.append(self._diff_unknown(current_val, update_val))

        if not any(diff):
            diff = None
        return diff

    def _diff_unknown(self, current, update):

        if isinstance(update, dict):
            diff = self._diff_dicts(current, update)
            if diff and any([v for k, v in diff.items()]):
                return diff
            elif diff is {}:
                return diff
            else:
                return None

        elif isinstance(update, list):
            diff = self._diff_lists(current, update)
            if diff and any(diff):
                return diff
            elif diff is []:
                return []
            else:
                return None
        else:
            if current != update:
                return update
            else:
                return False
