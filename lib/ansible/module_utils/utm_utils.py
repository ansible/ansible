# Copyright: (c) 2018, Johannes Brunswicker <johannes.brunswicker@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


class UTMModuleConfigurationError(Exception):

    def __init__(self, msg, **args):
        super(UTMModuleConfigurationError, self).__init__(self, msg)
        self.msg = msg
        self.module_fail_args = args

    def do_fail(self, module):
        module.fail_json(msg=self.msg, other=self.module_fail_args)

    def add(self):
        """
        adds or updates a host object on utm
        """
        is_changed = False
        info, result = self._lookup_entry(self.module, self.request_url)
        if info["status"] >= 400:
            self.module.fail_json(result=json.loads(info))
        else:
            if result is None:
                response, info = fetch_url(self.module, self.request_url, method="POST",
                                           headers={"Accept": "application/json", "Content-type": "application/json"},
                                           data=self.module.jsonify(self.module.params))
                if info["status"] >= 400:
                    self.module.fail_json(result=json.loads(info))
                is_changed = True
                result = self._clean_result(json.loads(response.read()))
            else:
                if self._is_object_changed(self.important_keys, self.module, result):
                    response, info = fetch_url(self.module, self.request_url + result['_ref'], method="PUT",
                                               headers={"Accept": "application/json",
                                                        "Content-type": "application/json"},
                                               data=self.module.jsonify(self.module.params))
                    if info['status'] >= 400:
                        self.module.fail_json(result=json.loads(info))
                    is_changed = True
                    result = self._clean_result(json.loads(response.read()))
            self.module.exit_json(result=result, changed=is_changed)

class UTMModule(AnsibleModule):
    """
    This is a helper class to construct any UTM Module. This will automatically add the utm host, port, token,
    protocol, validate_certs and state field to the module. If you want to implement your own sophos utm module
    just initialize this UTMModule class and define the Payload fields that are needed for your module.
    See the other modules like utm_aaa_group for example.
    """

    def __init__(self, argument_spec, bypass_checks=False, no_log=False, check_invalid_arguments=None,
                 mutually_exclusive=None, required_together=None, required_one_of=None, add_file_common_args=False,
                 supports_check_mode=False, required_if=None):
        default_specs = dict(
            utm_host=dict(type='str', required=True),
            utm_port=dict(type='int', default=4444),
            utm_token=dict(type='str', required=True, no_log=True),
            utm_protocol=dict(type='str', required=False, default="https", choices=["https", "http"]),
            validate_certs=dict(type='bool', required=False, default=True),
            state=dict(default='present', choices=['present', 'absent'])
        )
        super(UTMModule, self).__init__(self._merge_specs(default_specs, argument_spec), bypass_checks, no_log,
                                        check_invalid_arguments, mutually_exclusive, required_together, required_one_of,
                                        add_file_common_args, supports_check_mode, required_if)

    def _merge_specs(self, default_specs, custom_sepcs):
        result = default_specs.copy()
        result.update(custom_sepcs)
        return result


class UTM:

    def __init__(self, module, endpoint, change_relevant_keys):
        """
        Initialize UTM Class
        :param module: The ansible module
        :param endpoint: The corresponing endpoint to the module
        :param change_relevant_keys: The keys of the object to check for changes
        """
        self.module = module
        self.request_url = module.params.get('utm_protocol') + "://" + module.params.get('utm_host') + ":" + str(
            module.params.get('utm_port')) + "/api/objects/" + endpoint + "/"

        """
        The change_relevant_keys will be checked for changes to determine whether the object needs to be updated
        """
        self.change_relevant_keys = change_relevant_keys
        self.module.params['url_username'] = 'token'
        self.module.params['url_password'] = module.params.get('utm_token')
        if all(elem in self.change_relevant_keys for elem in module.params.keys()):
            raise UTMModuleConfigurationError(
                "The keys " + str(self.change_relevant_keys) + " to check are not in the modules keys:\n" + str(
                    module.params.keys()))

    def execute(self):
        try:
            if self.module.params.get('state') == 'present':
                self.add()
            else:
                self.remove()
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def add(self):
        """
        adds or updates a host object on utm
        """
        is_changed = False
        info, result = self._lookup_entry(self.module, self.request_url)
        if info["status"] >= 400:
            self.module.fail_json(result=json.loads(info))
        else:
            data_as_json_string = self.module.jsonify(self.module.params)
            if result is None:
                response, info = fetch_url(self.module, self.request_url, method="POST",
                                           headers={"Accept": "application/json", "Content-type": "application/json"},
                                           data=data_as_json_string)
                if info["status"] >= 400:
                    self.module.fail_json(msg=json.loads(info["body"]))
                is_changed = True
                result = self._clean_result(json.loads(response.read()))
            else:
                if self._is_object_changed(self.change_relevant_keys, self.module, result):
                    response, info = fetch_url(self.module, self.request_url + result['_ref'], method="PUT",
                                               headers={"Accept": "application/json",
                                                        "Content-type": "application/json"},
                                               data=data_as_json_string)
                    if info['status'] >= 400:
                        self.module.fail_json(msg=json.loads(info["body"]))
                    is_changed = True
                    result = self._clean_result(json.loads(response.read()))
            self.module.exit_json(result=result, changed=is_changed)

    def remove(self):
        """
        removes an object from utm
        """
        is_changed = False
        info, result = self._lookup_entry(self.module, self.request_url)
        if result is not None:
            response, info = fetch_url(self.module, self.request_url + result['_ref'], method="DELETE",
                                       headers={"Accept": "application/json", "X-Restd-Err-Ack": "all"},
                                       data=self.module.jsonify(self.module.params))
            if info["status"] >= 400:
                self.module.fail_json(msg=json.loads(info["body"]))
            else:
                is_changed = True
        self.module.exit_json(changed=is_changed)

    def _lookup_entry(self, module, request_url):
        """
        Lookup for existing entry
        :param module:
        :param request_url:
        :return:
        """
        response, info = fetch_url(module, request_url, method="GET", headers={"Accept": "application/json"})
        result = None
        if response is not None:
            results = json.loads(response.read())
            result = next(iter(filter(lambda d: d['name'] == module.params.get('name'), results)), None)
        return info, result

    def _clean_result(self, result):
        """
        Will clean the result from irrelevant fields
        :param result: The result from the query
        :return: The modified result
        """
        del result['utm_host']
        del result['utm_port']
        del result['utm_token']
        del result['utm_protocol']
        del result['validate_certs']
        del result['url_username']
        del result['url_password']
        del result['state']
        return result

    def _is_object_changed(self, keys, module, result):
        """
        Check if my object is changed
        :param keys: The keys that will determine if an object is changed
        :param module: The module
        :param result: The result from the query
        :return:
        """
        for key in keys:
            if module.params.get(key) != result[key]:
                return True
        return False
